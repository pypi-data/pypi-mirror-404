"""
This module contains classes for tracking machine and action resources.
"""

import os
import subprocess
import logging
import threading
import json
from datetime import datetime, timezone
import psutil
import docker
from typing import Any, List, Tuple, Dict, Optional, TYPE_CHECKING, Iterator, cast, ClassVar, Type
from matrice_compute.instance_utils import (
    has_gpu,
    get_gpu_info,
    calculate_time_difference,
)
from matrice_compute.scaling import Scaling
from matrice_common.utils import log_errors
from docker.client import DockerClient

if TYPE_CHECKING:
    from docker.models.containers import Container as DockerContainer


class ResourcesTracker:
    """Tracks machine and container resources.
    
    GPU Utilization Note:
        GPU utilization is tracked at the DEVICE level, not per-container.
        NVIDIA does not expose reliable per-process GPU utilization.
        Per-container GPU MEMORY is accurate; per-container GPU UTILIZATION is best-effort.
    """

    # Cache for nvidia-smi output to reduce subprocess overhead
    _gpu_cache: ClassVar[Dict[str, Any]] = {}
    _gpu_cache_timestamp: ClassVar[float] = 0.0
    _gpu_cache_ttl: ClassVar[float] = 1.0  # Cache TTL in seconds
    _gpu_cache_lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self) -> None:
        """
        Initialize ResourcesTracker.
        """
        pass

    @log_errors(default_return=(0, 0), raise_exception=False)
    def get_container_cpu_and_memory(self, container: 'DockerContainer') -> Tuple[float, float]:
        """
        Get CPU and memory usage for a container.

        Args:
            container (docker.models.containers.Container): Docker container instance.

        Returns:
            Tuple[float, float]: CPU utilization percentage (0-100 per core used) and memory usage in MB.
        """
        stats_raw = container.stats(stream=False)
        if not stats_raw:
            return 0.0, 0.0

        # Normalize to a dictionary for type-checking safety
        if isinstance(stats_raw, dict):
            stats = cast(Dict[str, Any], stats_raw)
        else:
            # Some client types may return an iterator; take the first element
            stats = cast(Dict[str, Any], next(cast(Iterator[Dict[str, Any]], stats_raw), {}))
            if not stats:
                return 0.0, 0.0

        cpu_utilization = 0.0
        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        system_delta = stats["cpu_stats"].get("system_cpu_usage", 0) - stats[
            "precpu_stats"
        ].get("system_cpu_usage", 0)
        
        if system_delta > 0:
            # FIX: Multiply by online_cpus to get correct percentage
            # Docker formula: (cpu_delta / system_delta) * online_cpus * 100
            online_cpus = stats["cpu_stats"].get("online_cpus")
            if not online_cpus:
                # Fallback: count from percpu_usage or use system CPU count
                percpu = stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [])
                online_cpus = len(percpu) if percpu else psutil.cpu_count()
            cpu_utilization = (cpu_delta / system_delta) * online_cpus * 100.0
        
        # Return memory in MB (consistent units) instead of percentage
        memory_usage_bytes = stats["memory_stats"].get("usage", 0)
        # Subtract cache if available for more accurate "real" memory
        cache_bytes = stats["memory_stats"].get("stats", {}).get("cache", 0)
        memory_usage_mb = (memory_usage_bytes - cache_bytes) / (1024 * 1024)
        
        return cpu_utilization, max(0, memory_usage_mb)

    @staticmethod
    def _parse_memory_string(memory_str: str) -> float:
        """
        Parse Docker memory string to MB.
        
        Handles: "1.5GiB", "512MiB", "1024KiB", "1.5GB", "512MB", "1024KB", "1024B"
        
        Args:
            memory_str: Memory string from docker stats
            
        Returns:
            float: Memory in MB
        """
        import re
        memory_str = memory_str.strip()
        
        # Match number (with optional decimal) and unit
        match = re.match(r'^([\d.]+)\s*([A-Za-z]+)$', memory_str)
        if not match:
            # Try splitting by space
            parts = memory_str.split()
            if len(parts) >= 2:
                value_str, unit = parts[0], parts[1]
            else:
                # Last resort: assume it's bytes
                try:
                    return float(memory_str) / (1024 * 1024)
                except ValueError:
                    return 0.0
        else:
            value_str, unit = match.groups()
        
        try:
            value = float(value_str)
        except ValueError:
            return 0.0
        
        # Normalize unit to lowercase for comparison
        unit = unit.lower()
        
        # Binary units (IEC)
        if unit in ('kib', 'ki'):
            return value / 1024
        elif unit in ('mib', 'mi'):
            return value
        elif unit in ('gib', 'gi'):
            return value * 1024
        elif unit in ('tib', 'ti'):
            return value * 1024 * 1024
        # Decimal units (SI)
        elif unit in ('kb', 'k'):
            return value / 1000
        elif unit in ('mb', 'm'):
            return value
        elif unit in ('gb', 'g'):
            return value * 1000
        elif unit in ('tb', 't'):
            return value * 1000 * 1000
        # Bytes
        elif unit in ('b', 'bytes'):
            return value / (1024 * 1024)
        else:
            # Unknown unit, assume MB
            logging.debug("Unknown memory unit '%s', assuming MB", unit)
            return value

    @log_errors(default_return=(0, 0), raise_exception=False, log_error=False)
    def get_container_cpu_and_memory_with_container_id(self, container_id: str) -> Tuple[float, float]:
        """
        Get CPU and memory usage for a specific container by its ID.

        Args:
            container_id (str): ID of the Docker container.

        Returns:
            Tuple[float, float]: CPU utilization percentage and memory usage in MB.
        """
        try:
            # Use JSON format for more reliable parsing
            stats_result = subprocess.run(
                [
                    "docker",
                    "stats",
                    "--no-stream",
                    "--format",
                    '{"cpu":"{{.CPUPerc}}","mem":"{{.MemUsage}}"}',
                    container_id,
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if stats_result.returncode != 0:
                logging.debug("docker stats command failed for container %s", container_id)
                return 0, 0
            
            # Parse JSON output
            stats_json = json.loads(stats_result.stdout.strip())
            
            # Parse CPU (remove % sign)
            cpu_str = stats_json.get("cpu", "0%").replace("%", "").strip()
            cpu_usage = float(cpu_str) if cpu_str else 0.0
            
            # Parse memory (format: "used / limit")
            mem_str = stats_json.get("mem", "0B / 0B")
            mem_used = mem_str.split("/")[0].strip()
            memory_usage_mb = self._parse_memory_string(mem_used)
            
            return cpu_usage, memory_usage_mb
            
        except json.JSONDecodeError as e:
            logging.debug("JSON parse error for container %s: %s", container_id, e)
            return 0, 0
        except subprocess.TimeoutExpired:
            logging.debug("docker stats command timed out for container %s", container_id)
            return 0, 0
        except (ValueError, IndexError) as e:
            logging.debug("Error parsing docker stats for container %s: %s", container_id, e)
            return 0, 0
        except Exception as e:
            logging.debug("Unexpected error getting container stats for %s: %s", container_id, e)
            return 0, 0

    def _get_cached_gpu_data(self) -> Dict:
        """
        Get cached GPU data from nvidia-smi to reduce subprocess overhead.
        
        Returns:
            Dict: Cached GPU data with keys:
                - 'processes': List of {pid, gpu_idx, memory_mb}
                - 'gpus': List of {idx, utilization, memory_used, memory_total}
                - 'timestamp': When cache was populated
        """
        import time as time_module
        current_time = time_module.time()
        cls: Type[ResourcesTracker] = type(self)
        
        with cls._gpu_cache_lock:
            # Return cache if still valid
            if (cls._gpu_cache and 
                current_time - cls._gpu_cache_timestamp < cls._gpu_cache_ttl):
                return cls._gpu_cache
            
            # Refresh cache
            cache: Dict[str, Any] = {
                'processes': [],
                'gpus': [],
                'timestamp': current_time,
            }
            
            if not has_gpu():
                cls._gpu_cache = cache
                cls._gpu_cache_timestamp = current_time
                return cache
            
            try:
                # Single nvidia-smi call for all GPU info
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=index,utilization.gpu,memory.used,memory.total",
                        "--format=csv,noheader,nounits"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        if not line.strip():
                            continue
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 4:
                            cache['gpus'].append({
                                'idx': int(parts[0]) if parts[0].isdigit() else 0,
                                'utilization': float(parts[1]) if parts[1].replace('.', '').isdigit() else 0,
                                'memory_used': int(parts[2]) if parts[2].isdigit() else 0,
                                'memory_total': int(parts[3]) if parts[3].isdigit() else 0,
                            })
                
                # Single nvidia-smi call for all processes
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-compute-apps=pid,gpu_uuid,used_memory",
                        "--format=csv,noheader,nounits"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        if not line.strip():
                            continue
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 3:
                            cache['processes'].append({
                                'pid': parts[0],
                                'gpu_uuid': parts[1],
                                'memory_mb': int(parts[2]) if parts[2].isdigit() else 0,
                            })
                            
            except subprocess.TimeoutExpired:
                logging.debug("nvidia-smi cache refresh timed out")
            except Exception as e:
                logging.debug("Error refreshing GPU cache: %s", e)
            
            cls._gpu_cache = cache
            cls._gpu_cache_timestamp = current_time
            return cache

    @log_errors(default_return=(0, 0), raise_exception=False, log_error=False)
    def get_container_gpu_info(self, container_id: str) -> Tuple[float, int]:
        """
        Get GPU usage for a specific container.

        IMPORTANT: GPU utilization tracking limitations:
        - GPU MEMORY per container is ACCURATE (from nvidia-smi per-process data)
        - GPU UTILIZATION per container is BEST-EFFORT (NVIDIA doesn't expose per-process SM usage)
        
        For GPU utilization, we report the utilization of GPUs that have container processes.
        If multiple containers share a GPU, they will all report similar utilization.

        Args:
            container_id (str): ID of the Docker container.

        Returns:
            Tuple[float, int]: 
                - GPU utilization percentage (device-level, for GPUs used by container)
                - GPU memory usage in MB (accurate per-container)
        """
        # Get ALL PIDs belonging to this container (not just main PID)
        container_pids = self.get_all_container_pids(container_id)
        if not container_pids:
            # Fallback to main PID only
            main_pid = self.get_pid_id_by_container_id(container_id)
            if main_pid:
                container_pids = {main_pid}
            else:
                return 0, 0
        
        # Check if this is a Jetson device
        if self._is_jetson_device():
            return self._get_jetson_gpu_usage(container_pids)
        
        # Use cached GPU data for efficiency
        gpu_data = self._get_cached_gpu_data()
        
        # Find GPU memory used by container (ACCURATE)
        gpu_mem_used = 0
        container_gpu_uuids = set()
        
        for proc in gpu_data.get('processes', []):
            if proc['pid'] in container_pids:
                gpu_mem_used += proc['memory_mb']
                container_gpu_uuids.add(proc['gpu_uuid'])
        
        # Get utilization of GPUs used by container (DEVICE-LEVEL approximation)
        # NOTE: This is NOT per-container utilization - it's the utilization of shared GPUs
        gpu_util = 0.0
        if container_gpu_uuids:
            # If we have GPU UUIDs, get their utilization
            # For now, just use overall utilization as approximation
            total_util = sum(g['utilization'] for g in gpu_data.get('gpus', []))
            gpu_count = len(gpu_data.get('gpus', [])) or 1
            gpu_util = total_util / gpu_count
        
        return gpu_util, gpu_mem_used

    @log_errors(default_return=False, raise_exception=False, log_error=False)
    def _is_jetson_device(self) -> bool:
        """
        Check if the current device is an NVIDIA Jetson.

        Returns:
            bool: True if Jetson device, False otherwise.
        """
        # Check for Jetson-specific indicators
        try:
            # Method 1: Check /etc/nv_tegra_release (Jetson specific)
            if os.path.exists("/etc/nv_tegra_release"):
                return True
            
            # Method 2: Check for tegra in /proc/device-tree/compatible
            if os.path.exists("/proc/device-tree/compatible"):
                with open("/proc/device-tree/compatible", "r") as f:
                    content = f.read().lower()
                    if "tegra" in content or "jetson" in content:
                        return True
            
            # Method 3: Check if tegrastats exists
            result = subprocess.run(
                ["which", "tegrastats"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return True
                
        except Exception as e:
            logging.debug("Error checking for Jetson device: %s", e)
        
        return False

    @log_errors(default_return=set(), raise_exception=False, log_error=False)
    def get_all_container_pids(self, container_id: str) -> set:
        """
        Get ALL PIDs belonging to a container (including child processes).
        
        Uses multiple methods for robustness:
        1. docker top (most reliable for standard Docker)
        2. Docker API inspect + process tree enumeration
        3. cgroup procs files (v1 and v2)
        
        Known limitations:
        - May miss processes in rootless Docker
        - CRI-O/containerd may have different layouts

        Args:
            container_id (str): ID of the Docker container.

        Returns:
            set: Set of all PIDs (as strings) belonging to the container.
        """
        pids = set()
        
        # Method 1: Use docker top (most reliable)
        try:
            result = subprocess.run(
                ["docker", "top", container_id, "-o", "pid"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines[1:]:  # Skip header
                    pid = line.strip()
                    if pid.isdigit():
                        pids.add(pid)
        except subprocess.TimeoutExpired:
            logging.debug("docker top command timed out for container %s", container_id)
        except Exception as e:
            logging.debug("docker top failed for %s: %s", container_id, e)
        
        # Method 2: Get init PID from docker inspect and enumerate children
        if not pids:
            try:
                result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Pid}}", container_id],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    init_pid = result.stdout.strip()
                    if init_pid and init_pid.isdigit() and init_pid != "0":
                        pids.add(init_pid)
                        # Enumerate all child processes recursively
                        pids.update(self._get_child_pids(init_pid))
            except Exception as e:
                logging.debug("docker inspect failed for %s: %s", container_id, e)
        
        # Method 3: Check cgroup procs files (fallback)
        cgroup_paths = [
            # cgroup v2 paths
            f"/sys/fs/cgroup/system.slice/docker-{container_id}.scope/cgroup.procs",
            f"/sys/fs/cgroup/docker/{container_id}/cgroup.procs",
            # cgroup v1 paths
            f"/sys/fs/cgroup/pids/docker/{container_id}/cgroup.procs",
            f"/sys/fs/cgroup/cpu/docker/{container_id}/cgroup.procs",
            f"/sys/fs/cgroup/memory/docker/{container_id}/cgroup.procs",
        ]
        
        for cgroup_path in cgroup_paths:
            try:
                if os.path.exists(cgroup_path):
                    with open(cgroup_path, "r") as f:
                        for line in f:
                            pid = line.strip()
                            if pid.isdigit():
                                pids.add(pid)
                    break
            except Exception as e:
                logging.debug("Error reading cgroup %s: %s", cgroup_path, e)
        
        return pids

    @log_errors(default_return=set(), raise_exception=False, log_error=False)
    def _get_child_pids(self, parent_pid: str, visited: Optional[set[Any]] = None) -> set:
        """
        Recursively get all child PIDs of a process.

        Args:
            parent_pid (str): Parent PID to get children for.
            visited (set): Set of already visited PIDs to prevent cycles.

        Returns:
            set: Set of all child PIDs (as strings).
        """
        if visited is None:
            visited = set()
        
        if parent_pid in visited:
            return set()
        visited.add(parent_pid)
        
        children = set()
        children_path = f"/proc/{parent_pid}/task/{parent_pid}/children"
        
        try:
            if os.path.exists(children_path):
                with open(children_path, "r") as f:
                    child_pids = f.read().strip().split()
                    for child_pid in child_pids:
                        if child_pid.isdigit():
                            children.add(child_pid)
                            # Recursively get grandchildren
                            children.update(self._get_child_pids(child_pid, visited))
        except Exception as e:
            logging.debug("Error getting children of PID %s: %s", parent_pid, e)
        
        return children

    @log_errors(default_return=(0, 0), raise_exception=False, log_error=False)
    def _get_jetson_gpu_usage(self, container_pids: set) -> Tuple[float, int]:
        """
        Get GPU usage for Jetson devices.

        Args:
            container_pids (set): Set of container PIDs.

        Returns:
            Tuple[float, int]: GPU utilization percentage and GPU memory usage in MB.
        """
        gpu_util = 0.0
        gpu_mem_used = 0
        
        try:
            # Method 1: Try using tegrastats (one-shot)
            result = subprocess.run(
                ["tegrastats", "--interval", "100", "--stop", "1"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0 and result.stdout:
                output = result.stdout.strip()
                # Parse tegrastats output - format varies by Jetson model
                # Example: "RAM 2457/7773MB (lfb 1x512kB) CPU [...] GR3D_FREQ 0% ..."
                
                # Extract GR3D (GPU) utilization
                import re
                gr3d_match = re.search(r'GR3D_FREQ\s+(\d+)%', output)
                if gr3d_match:
                    gpu_util = float(gr3d_match.group(1))
                
                # For Jetson, GPU memory is shared with system RAM
                # We can estimate based on total GPU memory allocation
                # Try to get from /sys/kernel/debug/nvmap or similar
                
        except subprocess.TimeoutExpired:
            logging.debug("tegrastats timed out")
        except FileNotFoundError:
            logging.debug("tegrastats not found, trying alternative methods")
        except Exception as e:
            logging.debug("Error running tegrastats: %s", e)
        
        # Method 2: Try jtop Python library info from /sys
        if gpu_util == 0:
            try:
                # Read GPU frequency/utilization from sysfs
                gpu_load_paths = [
                    "/sys/devices/gpu.0/load",
                    "/sys/devices/platform/host1x/gpu.0/load",
                    "/sys/devices/57000000.gpu/load",
                    "/sys/devices/17000000.ga10b/load",  # Orin
                ]
                
                for path in gpu_load_paths:
                    if os.path.exists(path):
                        with open(path, "r") as f:
                            # Load is reported as 0-1000, convert to percentage
                            load_val = int(f.read().strip())
                            gpu_util = load_val / 10.0
                        break
                        
            except Exception as e:
                logging.debug("Error reading Jetson GPU load from sysfs: %s", e)
        
        # Method 3: Get GPU memory from /proc for container processes
        if container_pids:
            try:
                # On Jetson, GPU memory is unified with system RAM
                # Check /proc/[pid]/smaps for GPU-related mappings
                for pid in container_pids:
                    smaps_path = f"/proc/{pid}/smaps"
                    if os.path.exists(smaps_path):
                        with open(smaps_path, "r") as f:
                            content = f.read()
                            # Look for nvmap or GPU memory regions
                            for line in content.split("\n"):
                                if "nvmap" in line.lower() or "gpu" in line.lower():
                                    # Extract size if present
                                    if "Size:" in line:
                                        size_kb = int(line.split()[1])
                                        gpu_mem_used += size_kb // 1024  # Convert to MB
            except Exception as e:
                logging.debug("Error getting Jetson GPU memory: %s", e)
        
        return gpu_util, gpu_mem_used

    @log_errors(default_return="", raise_exception=False, log_error=False)
    def get_pid_id_by_container_id(self, container_id: str) -> str:
        """
        Get PID for a container ID.

        Args:
            container_id (str): ID of the Docker container.

        Returns:
            str: PID of the container.
        """
        try:
            pid_result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    "--format",
                    "{{.State.Pid}}",
                    container_id,
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if pid_result.returncode != 0:
                logging.debug("docker inspect command failed for container %s", container_id)
                return ""
            container_pid = pid_result.stdout.strip()
            return container_pid
        except subprocess.TimeoutExpired:
            logging.debug("docker inspect command timed out for container %s", container_id)
            return ""
        except Exception as e:
            logging.debug("Error getting PID for container %s: %s", container_id, e)
            return ""

    @log_errors(default_return=0, raise_exception=False, log_error=False)
    def get_container_gpu_usage(self, container_pid: str) -> float:
        """
        Get GPU usage for a container PID.

        Args:
            container_pid (str): PID of the Docker container.

        Returns:
            float: GPU utilization percentage.
        """
        return self.get_container_gpu_usage_multi_pid({str(container_pid)})

    @log_errors(default_return=0, raise_exception=False, log_error=False)
    def get_container_gpu_usage_multi_pid(self, container_pids: set) -> float:
        """
        Get GPU usage for multiple container PIDs.

        Args:
            container_pids (set): Set of container PIDs (as strings).

        Returns:
            float: Total GPU utilization percentage across all matching processes.
        """
        if not has_gpu():
            return 0
        if not container_pids:
            return 0
            
        gpu_util = 0.0
        
        try:
            # Method 1: nvidia-smi pmon (process monitoring)
            result = subprocess.run(
                ["nvidia-smi", "pmon", "-c", "1", "-s", "u"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if result.returncode == 0:
                pmon_output = result.stdout.strip().split("\n")
                for line in pmon_output:
                    # Skip header lines (start with # or contain column names)
                    if line.startswith("#") or "gpu" in line.lower() and "pid" in line.lower():
                        continue
                    parts = line.split()
                    if len(parts) >= 4:
                        pid = parts[1]
                        sm_usage = parts[3] if len(parts) > 3 else "0"
                        if pid in container_pids:
                            if sm_usage != "-" and sm_usage.replace(".", "").isdigit():
                                gpu_util += float(sm_usage)
                
                if gpu_util > 0:
                    return gpu_util
            
            # Method 2: Query per-process GPU utilization
            result = subprocess.run(
                ["nvidia-smi", "--query-compute-apps=pid,gpu_uuid", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if result.returncode == 0:
                # Get overall GPU utilization per GPU
                gpu_utils = {}
                util_result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=uuid,utilization.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
                )
                if util_result.returncode == 0:
                    for line in util_result.stdout.strip().split("\n"):
                        parts = line.split(",")
                        if len(parts) >= 2:
                            gpu_uuid = parts[0].strip()
                            util = float(parts[1].strip()) if parts[1].strip().replace(".", "").isdigit() else 0
                            gpu_utils[gpu_uuid] = util
                
                # Check which GPUs have our container processes
                matched_gpus = set()
                for line in result.stdout.strip().split("\n"):
                    if not line.strip():
                        continue
                    parts = line.split(",")
                    if len(parts) >= 2:
                        pid = parts[0].strip()
                        gpu_uuid = parts[1].strip()
                        if pid in container_pids:
                            matched_gpus.add(gpu_uuid)
                
                # Sum utilization for matched GPUs
                for gpu_uuid in matched_gpus:
                    if gpu_uuid in gpu_utils:
                        gpu_util += gpu_utils[gpu_uuid]
                        
        except subprocess.TimeoutExpired:
            logging.debug("nvidia-smi command timed out in get_container_gpu_usage_multi_pid")
            return 0
        except (ValueError, IndexError) as e:
            logging.debug("Error parsing GPU usage info: %s", e)
            return 0
        except FileNotFoundError:
            logging.debug("nvidia-smi not found on this system")
            return 0
        except Exception as e:
            logging.debug("Unexpected error in get_container_gpu_usage_multi_pid: %s", e)
            return 0
            
        return gpu_util

    @log_errors(default_return=0, raise_exception=False, log_error=False)
    def get_container_gpu_memory_usage(self, container_pid: str) -> int:
        """
        Get GPU memory usage for a container PID.

        Args:
            container_pid (str): PID of the Docker container.

        Returns:
            int: GPU memory usage in MB.
        """
        return self.get_container_gpu_memory_usage_multi_pid({str(container_pid)})

    @log_errors(default_return=0, raise_exception=False, log_error=False)
    def get_container_gpu_memory_usage_multi_pid(self, container_pids: set) -> int:
        """
        Get GPU memory usage for multiple container PIDs.

        Args:
            container_pids (set): Set of container PIDs (as strings).

        Returns:
            int: Total GPU memory usage in MB across all matching processes.
        """
        if not has_gpu():
            return 0
        if not container_pids:
            return 0
            
        total_memory = 0
        
        try:
            # Method 1: Query compute apps for memory usage
            cmd = [
                "nvidia-smi",
                "--query-compute-apps=pid,used_memory",
                "--format=csv,noheader,nounits",
            ]
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    # Handle both ", " and "," separators
                    if ", " in line:
                        parts = line.split(", ")
                    else:
                        parts = line.split(",")
                    if len(parts) >= 2:
                        process_pid = parts[0].strip()
                        used_memory = parts[1].strip()
                        if process_pid in container_pids:
                            if used_memory.isdigit():
                                total_memory += int(used_memory)
                
                if total_memory > 0:
                    return total_memory
            
            # Method 2: Use pmon for memory info
            result = subprocess.run(
                ["nvidia-smi", "pmon", "-c", "1", "-s", "m"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if result.returncode == 0:
                pmon_output = result.stdout.strip().split("\n")
                for line in pmon_output:
                    if line.startswith("#") or "gpu" in line.lower() and "pid" in line.lower():
                        continue
                    parts = line.split()
                    # Format: gpu pid type fb_mem (MB)
                    if len(parts) >= 4:
                        pid = parts[1]
                        fb_mem = parts[3] if len(parts) > 3 else "0"
                        if pid in container_pids:
                            if fb_mem != "-" and fb_mem.isdigit():
                                total_memory += int(fb_mem)
                                
        except subprocess.TimeoutExpired:
            logging.debug("nvidia-smi command timed out in get_container_gpu_memory_usage_multi_pid")
            return 0
        except (ValueError, IndexError) as e:
            logging.debug("Error parsing GPU memory usage info: %s", e)
            return 0
        except FileNotFoundError:
            logging.debug("nvidia-smi not found on this system")
            return 0
        except Exception as e:
            logging.debug("Unexpected error in get_container_gpu_memory_usage_multi_pid: %s", e)
            return 0
            
        return total_memory

    @log_errors(default_return=(0, 0, 0, 0), raise_exception=False, log_error=True)
    def get_available_resources(self) -> Tuple[float, float, int, float]:
        """
        Get available machine resources.
        
        Note: CPU measurement is non-blocking (uses interval=0).
        For more accurate CPU usage, call this method periodically and track trends.

        Returns:
            Tuple[float, float, int, float]: 
                - Available memory in GB
                - Available CPU percentage (100 - current_usage)
                - Free GPU memory in MB
                - GPU utilization percentage (0-100)
        """
        # Memory: straightforward
        available_memory = psutil.virtual_memory().available / (1024 ** 3)
        
        # CPU: NON-BLOCKING - interval=0 returns instant snapshot
        # For better accuracy, consider using load average or tracking over time
        # Note: Inside containers, this may not reflect cgroup limits
        try:
            # Use interval=0 for non-blocking (returns cached value or 0.0 on first call)
            cpu_percent = psutil.cpu_percent(1)
            # # If first call (returns 0.0), try load average as fallback
            # if cpu_percent == 0.0:
            #     try:
            #         # Use 1-minute load average as percentage of CPU count
            #         load_avg = os.getloadavg()[0]
            #         cpu_count = psutil.cpu_count() or 1
            #         cpu_percent = min(100.0, (load_avg / cpu_count) * 100.0)
            #     except (OSError, AttributeError):
            #         # os.getloadavg() not available on Windows
            #         pass
            available_cpu = max(0.0, 100.0 - cpu_percent)
        except Exception:
            available_cpu = 100.0
        
        gpu_memory_free, gpu_utilization = self._get_gpu_resources()
        return available_memory, available_cpu, gpu_memory_free, gpu_utilization

    @log_errors(default_return=(0, 0.0), raise_exception=False, log_error=False)
    def _get_gpu_resources(self) -> Tuple[int, float]:
        """
        Get available GPU resources using cached data.

        Returns:
            Tuple[int, float]: Free GPU memory in MB and GPU utilization percentage.
        """
        if not has_gpu():
            return 0, 0.0
        
        # Use cached GPU data for efficiency
        gpu_data = self._get_cached_gpu_data()
        
        if not gpu_data.get('gpus'):
            # Cache miss or no GPUs, fall back to direct query
            return self._get_gpu_resources_direct()
        
        gpu_memory_free = 0
        gpu_utilization = 0.0
        gpu_count = 0
        
        for gpu in gpu_data['gpus']:
            # Be defensive: nvidia-smi can occasionally report N/A/0 for total while used is numeric,
            # which would otherwise produce negative "free" memory.
            total_mb = gpu.get('memory_total', 0) or 0
            used_mb = gpu.get('memory_used', 0) or 0
            free_mb = total_mb - used_mb
            if free_mb < 0:
                logging.debug(
                    "Negative GPU free memory computed (gpu_idx=%s total_mb=%s used_mb=%s); clamping to 0",
                    gpu.get('idx'),
                    total_mb,
                    used_mb,
                )
                free_mb = 0
            gpu_memory_free += free_mb
            gpu_utilization += gpu['utilization']
            gpu_count += 1
        
        if gpu_count > 0:
            gpu_utilization /= gpu_count

        return max(0, gpu_memory_free), gpu_utilization

    @log_errors(default_return=(0, 0.0), raise_exception=False, log_error=False)
    def _get_gpu_resources_direct(self) -> Tuple[int, float]:
        """
        Get GPU resources directly (fallback when cache is empty).

        Returns:
            Tuple[int, float]: Free GPU memory in MB and GPU utilization percentage.
        """
        gpu_memory_free = 0
        gpu_utilization = 0.0

        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.free,utilization.gpu", "--format=csv,noheader,nounits"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return 0, 0.0
            
            gpu_count = 0
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    gpu_memory_free += int(parts[0]) if parts[0].isdigit() else 0
                    gpu_utilization += float(parts[1]) if parts[1].replace('.', '').isdigit() else 0
                    gpu_count += 1
            
            if gpu_count > 0:
                gpu_utilization /= gpu_count
                
        except subprocess.TimeoutExpired:
            logging.debug("nvidia-smi command timed out in _get_gpu_resources_direct")
        except FileNotFoundError:
            logging.debug("nvidia-smi not found on this system")
        except Exception as e:
            logging.debug("Error in _get_gpu_resources_direct: %s", e)

        return gpu_memory_free, gpu_utilization


class ActionsResourcesTracker:
    """Tracks Docker container action resources"""

    def __init__(self, scaling: Scaling):
        """Initialize ActionsResourcesTracker"""
        self.scaling = scaling
        self.max_actions_usage: dict[Any, Any] = {}
        self.resources_tracker = ResourcesTracker()
        self.client = docker.from_env()
        self.logged_stopped_containers: list[Any] = []

    @log_errors(raise_exception=False, log_error=True)
    def update_actions_resources(self) -> None:
        """Process both running and exited containers.
        
        Note: Does not remove containers to keep logs. Only tracks resource usage.
        """
        exited_containers = self.client.containers.list(
            filters={"status": "exited"},
            all=True,
        )
        running_containers = self.client.containers.list(filters={"status": "running"})
        if exited_containers:
            for container in exited_containers:
                try:
                    if container.id in self.logged_stopped_containers:
                        continue
                    self._update_container_action_status(container, "completed")
                    self.logged_stopped_containers.append(container.id)
                    # COMMENTED OUT: Do not remove containers to keep logs
                    # container.remove()
                except Exception as err:
                    logging.error(
                        "Error processing exited container %s: %s",
                        container.id,
                        str(err),
                    )
        if running_containers:
            for container in running_containers:
                try:
                    self._update_container_action_status(container, "running")
                except Exception as err:
                    logging.error(
                        "Error processing running container %s: %s",
                        container.id,
                        str(err),
                    )

    @log_errors(default_return=[], raise_exception=False)
    def get_sub_containers_by_label(self, label_key: str, label_value: str) -> list:
        """Get running containers with specified label key and value"""
        containers = self.client.containers.list(
            filters={
                "label": [f"{label_key}={label_value}"],
                "status": "running",
            }
        )
        return containers

    @log_errors(raise_exception=False, log_error=True)
    def _update_container_action_status(self, container, status: str) -> None:
        """Update action status for a specific container"""
        inspect_data = self.client.api.inspect_container(container.id)
        start_time = inspect_data["State"]["StartedAt"]
        finish_time = (
            inspect_data["State"]["FinishedAt"]
            if status == "completed"
            else datetime.now(timezone.utc).isoformat()
        )

        def remove_quotation_marks(args):
            """Remove quotes from container args"""
            new_args = []
            for arg in args:
                new_args.extend([x.replace('"', "").replace("'", "") for x in arg.split(" ")])
            return new_args

        def is_valid_objectid(s: str) -> bool:
            """Check if string is a valid MongoDB ObjectId (24 hex characters)"""
            s = s.strip()
            return len(s) == 24 and all(c in '0123456789abcdefABCDEF' for c in s)
        
        valid_objectids = [arg for arg in remove_quotation_marks(inspect_data["Args"]) if is_valid_objectid(arg)]
        action_record_id = valid_objectids[-1] if valid_objectids else None
        if not action_record_id:
            logging.debug("No valid action_id found for the container. Container ID: %s, Args: %s", container.id, inspect_data["Args"])
        duration = calculate_time_difference(start_time, finish_time)
        (
            current_gpu_utilization,
            current_gpu_memory,
            current_cpu_utilization,
            current_memory_utilization,
        ) = self.get_current_action_usage(container, status)
        sub_containers = self.get_sub_containers_by_label("action_id", action_record_id)
        for sub_container in sub_containers:
            if sub_container.id in self.logged_stopped_containers:
                continue
            (
                sub_container_gpu_utilization,
                sub_container_gpu_memory,
                sub_container_cpu_utilization,
                sub_container_memory_utilization,
            ) = self.get_current_action_usage(sub_container, status)
            current_gpu_utilization += sub_container_gpu_utilization
            current_gpu_memory += sub_container_gpu_memory
            current_cpu_utilization += sub_container_cpu_utilization
            current_memory_utilization += sub_container_memory_utilization
            # COMMENTED OUT: Do not stop/remove sub-containers to keep logs
            if status == "completed":
                try:
                    sub_container.stop()
                    self.logged_stopped_containers.append(sub_container.id)
            #         sub_container.remove(force=True)
                except Exception as err:
                    logging.error(
                        "Error removing sub-container %s: %s",
                        sub_container.id,
                        str(err),
                    )
        (
            max_gpu_utilization,
            max_gpu_memory,
            max_cpu_utilization,
            max_memory_utilization,
        ) = self.update_max_action_usage(
            action_record_id,
            current_gpu_utilization,
            current_gpu_memory,
            current_cpu_utilization,
            current_memory_utilization,
        )
        logging.info(
            "Updating action status: service_provider=%s, action_id=%s, running=%s, status=%s, duration=%s, start=%s, gpu_util=%.2f%%, cpu_util=%.2f%%, gpu_mem=%dMB, mem_util=%.2f%%, created=%s, updated=%s",
            os.environ["SERVICE_PROVIDER"],
            action_record_id,
            status == "running",
            status,
            duration,
            start_time,
            max_gpu_utilization,
            max_cpu_utilization,
            max_gpu_memory,
            max_memory_utilization,
            start_time,
            finish_time,
        )
        self.scaling.update_action_status(
            service_provider=os.environ["SERVICE_PROVIDER"],
            action_record_id=action_record_id,
            isRunning=status == "running",
            status=status,
            action_duration=duration,
            docker_start_time=start_time,
            gpuUtilisation=max_gpu_utilization,
            cpuUtilisation=max_cpu_utilization,
            gpuMemoryUsed=max_gpu_memory,
            memoryUtilisation=max_memory_utilization,
            createdAt=start_time,
            updatedAt=finish_time,
        )

    @log_errors(default_return=(0, 0, 0, 0), raise_exception=False)
    def get_current_action_usage(self, container, status: str) -> Tuple[float, int, float, float]:
        """Get current resource usage for a container"""
        current_gpu_utilization = 0
        current_gpu_memory = 0
        current_cpu_utilization = 0
        current_memory_utilization = 0
        if status == "running":
            try:
                (
                    current_cpu_utilization,
                    current_memory_utilization,
                ) = self.resources_tracker.get_container_cpu_and_memory(container)
                (
                    current_gpu_utilization,
                    current_gpu_memory,
                ) = self.resources_tracker.get_container_gpu_info(container_id=container.id)
            except Exception as err:
                logging.error(
                    "Error getting container usage metrics: %s",
                    str(err),
                )
        return (
            current_gpu_utilization,
            current_gpu_memory,
            current_cpu_utilization,
            current_memory_utilization,
        )

    @log_errors(default_return=(0, 0, 0, 0), raise_exception=False, log_error=True)
    def update_max_action_usage(
        self,
        action_record_id: str,
        current_gpu_utilization: float,
        current_gpu_memory: int,
        current_cpu_utilization: float,
        current_memory_utilization: float,
    ) -> Tuple[float, int, float, float]:
        
        """Update and return maximum resource usage values for an action"""
        if action_record_id not in self.max_actions_usage:
            self.max_actions_usage[action_record_id] = {
                "gpu_utilization": 0,
                "gpu_memory": 0,
                "cpu_utilization": 0,
                "memory_utilization": 0,
            }
        current_values = {
            "gpu_utilization": current_gpu_utilization or 0,
            "gpu_memory": current_gpu_memory or 0,
            "cpu_utilization": current_cpu_utilization or 0,
            "memory_utilization": current_memory_utilization or 0,
        }
        for key in current_values:
            self.max_actions_usage[action_record_id][key] = max(
                current_values[key],
                self.max_actions_usage[action_record_id][key],
            )
        return (
            self.max_actions_usage[action_record_id]["gpu_utilization"],
            self.max_actions_usage[action_record_id]["gpu_memory"],
            self.max_actions_usage[action_record_id]["cpu_utilization"],
            self.max_actions_usage[action_record_id]["memory_utilization"],
        )


class MachineResourcesTracker:
    """Tracks machine-level resources like CPU, memory and GPU"""

    def __init__(self, scaling: Scaling):
        """Initialize MachineResourcesTracker"""
        self.scaling = scaling
        self.resources_tracker = ResourcesTracker()

    @log_errors(raise_exception=False, log_error=True)
    def update_available_resources(self):
        """Update available machine resources"""
        (
            available_memory,
            available_cpu,
            gpu_memory_free,
            gpu_utilization,
        ) = self.resources_tracker.get_available_resources()
        _, err, _ = self.scaling.update_available_resources(
            availableCPU=available_cpu,
            availableMemory=available_memory,
            availableGPU=100 - gpu_utilization,
            availableGPUMemory=max(0, gpu_memory_free),
        )
        if err is not None:
            logging.error(
                "Error in updating available resources: %s",
                err,
            )


class ContainerResourceMonitor:
    """
    Monitors individual container resource utilization and publishes to Kafka.
    This thread runs independently and reports CPU, memory, and GPU usage for all running containers.
    """

    def __init__(
        self,
        instance_id: Optional[str] = None,
        kafka_bootstrap: Optional[str] = None,
        interval_seconds: int = 30,
    ):
        """
        Initialize ContainerResourceMonitor.

        Args:
            instance_id: Instance identifier for Kafka topic. Defaults to INSTANCE_ID env var.
            kafka_bootstrap: Kafka bootstrap servers. Required - should be obtained from Scaling.get_kafka_bootstrap_servers().
            interval_seconds: Interval between container checks in seconds. Defaults to 30.
        """
        self.instance_id = instance_id or os.getenv("INSTANCE_ID")
        if not self.instance_id:
            raise ValueError("instance_id must be provided or INSTANCE_ID env var must be set")

        if not kafka_bootstrap:
            raise ValueError("kafka_bootstrap must be provided - use Scaling.get_kafka_bootstrap_servers() to get internal Kafka config")

        self.kafka_bootstrap = kafka_bootstrap
        self.interval_seconds = interval_seconds
        self.topic_name = "instance_resource_utilisation"

        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._producer = None
        self._is_running = False
        self._docker_client: Optional[DockerClient] = None
        self._resources_tracker = ResourcesTracker()

    def _get_all_running_containers(self) -> List['DockerContainer']:
        """
        Get all running Docker containers.

        Returns:
            List[docker.models.containers.Container]: List of running containers
        """
        try:
            if not self._docker_client:
                self._docker_client = docker.from_env()
            assert self._docker_client is not None
            containers = self._docker_client.containers.list(filters={"status": "running"})
            return containers
        except Exception as e:
            logging.debug("Error getting running containers: %s", e)
            return []

    def _collect_container_resources(self, container: 'DockerContainer') -> Optional[dict[str, Any]]:
        """
        Collect resource usage for a single container.

        Args:
            container: Docker container instance

        Returns:
            Dict: Container resource data
        """
        try:
            container_id = container.id
            container_name = container.name
            
            # Get CPU and memory usage
            cpu_util, memory_mb = self._resources_tracker.get_container_cpu_and_memory(container)
            
            # Get GPU usage (utilization and memory)
            gpu_util, gpu_memory_mb = self._resources_tracker.get_container_gpu_info(container_id)
            
            return {
                "container_id": container_id,
                "container_name": container_name,
                "cpu_utilization_percent": round(cpu_util, 2),
                "memory_usage_mb": round(memory_mb, 2),
                "gpu_utilization_percent": round(gpu_util, 2),
                "gpu_memory_usage_mb": gpu_memory_mb,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logging.debug("Error collecting resources for container %s: %s", container.name, e)
            return None

    def _monitor_worker(self):
        """
        Worker function that runs in a separate thread to monitor containers and publish to Kafka.
        """
        try:
            from kafka import KafkaProducer

            self._producer = KafkaProducer(
                bootstrap_servers=self.kafka_bootstrap,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retries=5,
            )
            logging.info("Container resource monitor started. Publishing to topic: %s", self.topic_name)

        except ImportError:
            logging.error("kafka-python not installed. Install with: pip install kafka-python")
            return
        except Exception as e:
            logging.error("Failed to initialize Kafka producer for container monitor: %s", e)
            return

        while not self._stop_event.is_set():
            try:
                # Get all running containers
                containers = self._get_all_running_containers()
                
                if not containers:
                    logging.debug("No running containers found")
                else:
                    container_data = []
                    
                    # Collect resources for each container
                    for container in containers:
                        resource_data = self._collect_container_resources(container)
                        if resource_data:
                            container_data.append(resource_data)
                    
                    # Create the payload with instance information and all container data
                    payload = {
                        "instance_id": self.instance_id,
                        "container_count": len(container_data),
                        "containers": container_data,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }

                    # Send to Kafka topic
                    self._producer.send(self.topic_name, payload)
                    self._producer.flush()

                    logging.debug("Published container resource stats for %d containers", len(container_data))

            except Exception as e:
                logging.error("Error in container resource monitor loop: %s", e)

            # Wait for interval or until stop event is set
            if self._stop_event.wait(self.interval_seconds):
                break

        # Cleanup
        if self._producer:
            try:
                self._producer.close()
            except Exception as e:
                logging.debug("Error closing Kafka producer: %s", e)

        if self._docker_client:
            try:
                self._docker_client.close()
            except Exception as e:
                logging.debug("Error closing Docker client: %s", e)

        logging.info("Container resource monitor stopped.")

    @log_errors(raise_exception=False, log_error=True)
    def start(self):
        """
        Start the container resource monitoring thread.

        Returns:
            bool: True if started successfully, False otherwise.
        """
        if self._is_running:
            logging.warning("Container resource monitor is already running.")
            return False

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_worker,
            daemon=True,
            name="ContainerResourceMonitor"
        )
        self._monitor_thread.start()
        self._is_running = True

        logging.info("Started container resource monitor thread.")
        return True

    @log_errors(raise_exception=False, log_error=True)
    def stop(self, timeout: int = 10):
        """
        Stop the container resource monitoring thread gracefully.

        Args:
            timeout: Maximum time to wait for thread to stop in seconds.

        Returns:
            bool: True if stopped successfully, False otherwise.
        """
        if not self._is_running:
            logging.warning("Container resource monitor is not running.")
            return False

        logging.info("Stopping container resource monitor...")
        self._stop_event.set()

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=timeout)

            if self._monitor_thread.is_alive():
                logging.error("Container resource monitor thread did not stop within timeout.")
                return False

        self._is_running = False
        logging.info("Container resource monitor stopped successfully.")
        return True

    def is_running(self) -> bool:
        """
        Check if the container resource monitor is currently running.

        Returns:
            bool: True if running, False otherwise.
        """
        return self._is_running

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class KafkaResourceMonitor:
    """
    Monitors system resources and publishes them to Kafka in a separate thread.
    This class provides thread-safe start/stop operations for resource monitoring.
    """

    def __init__(
        self,
        instance_id: Optional[str] = None,
        kafka_bootstrap: Optional[str] = None,
        interval_seconds: int = 60,
    ):
        """
        Initialize KafkaResourceMonitor.

        Args:
            instance_id: Instance identifier for Kafka topic. Defaults to INSTANCE_ID env var.
            kafka_bootstrap: Kafka bootstrap servers. Required - should be obtained from Scaling.get_kafka_bootstrap_servers().
            interval_seconds: Interval between resource checks in seconds. Defaults to 60.
        """
        self.instance_id = instance_id or os.getenv("INSTANCE_ID")
        if not self.instance_id:
            raise ValueError("instance_id must be provided or INSTANCE_ID env var must be set")

        if not kafka_bootstrap:
            raise ValueError("kafka_bootstrap must be provided - use Scaling.get_kafka_bootstrap_servers() to get internal Kafka config")

        self.kafka_bootstrap = kafka_bootstrap
        self.interval_seconds = interval_seconds
        self.topic_name = "compute_instance_resource_utilization"

        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._producer = None
        self._is_running = False

    @staticmethod
    def get_all_gpu_memory() -> Dict[int, tuple]:
        """
        Get GPU memory usage and total for all GPUs.

        Returns:
            Dict[int, tuple]: Dictionary mapping GPU ID to (used_gb, total_gb).
                             Returns empty dict if nvidia-smi is not available.
        """
        gpu_usage = {}

        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=index,memory.used,memory.total",
                "--format=csv,noheader,nounits"
            ]
            result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=5)
            lines = result.decode().strip().split("\n")

            for line in lines:
                gpu_id_str, mem_used_mb_str, mem_total_mb_str = line.split(",")
                gpu_id = int(gpu_id_str.strip())
                mem_used_gb = int(mem_used_mb_str.strip()) / 1024  # MB → GB
                mem_total_gb = int(mem_total_mb_str.strip()) / 1024  # MB → GB
                gpu_usage[gpu_id] = (round(mem_used_gb, 2), round(mem_total_gb, 2))

        except Exception as e:
            logging.debug("Failed to get GPU memory info: %s", e)
            return {}

        return gpu_usage

    @staticmethod
    def get_all_storage_info() -> Dict[str, tuple]:
        """
        Get storage information for all mounted drives.

        Returns:
            Dict[str, tuple]: Dictionary mapping mount point to (free_gb, total_gb).
        """
        storage_info = {}

        try:
            # Get all disk partitions
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    # Get usage statistics for this partition
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    # Convert bytes to GB
                    free_gb = usage.free / (1024 ** 3)
                    total_gb = usage.total / (1024 ** 3)
                    
                    storage_info[partition.mountpoint] = (round(free_gb, 2), round(total_gb, 2))
                    
                except PermissionError:
                    # Skip drives that we can't access (common on Windows)
                    logging.debug("Permission denied accessing %s", partition.mountpoint)
                    continue
                except Exception as e:
                    logging.debug("Error getting storage info for %s: %s", partition.mountpoint, e)
                    continue
                    
        except Exception as e:
            logging.debug("Failed to get storage info: %s", e)
            return {}

        return storage_info

    def get_stats(self) -> Tuple[float, int, float, float, Dict[int, tuple], Dict[str, tuple]]:
        """
        Collect current system resource statistics.

        Returns:
            Tuple[float, int, float, float, Dict[int, tuple], Dict[str, tuple]]: 
            CPU usage %, CPU cores, RAM total GB, RAM used GB, GPU memory dict (used, total), Storage dict (free, total)
        """
        cpu_usage = psutil.cpu_percent(interval=1)
        cpu_cores = psutil.cpu_count(logical=True) or 0  # Total logical CPU cores

        mem = psutil.virtual_memory()
        ram_total = mem.total / (1024 ** 3)
        ram_used = mem.used / (1024 ** 3)

        gpu_usage = self.get_all_gpu_memory()
        storage_info = self.get_all_storage_info()

        return cpu_usage, cpu_cores, ram_total, ram_used, gpu_usage, storage_info

    def _monitor_worker(self):
        """
        Worker function that runs in a separate thread to monitor and publish resources.
        """
        try:
            from kafka import KafkaProducer

            self._producer = KafkaProducer(
                bootstrap_servers=self.kafka_bootstrap,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retries=5,
            )
            logging.info("Kafka resource monitor started. Publishing to topic: %s", self.topic_name)

        except ImportError:
            logging.error("kafka-python not installed. Install with: pip install kafka-python")
            return
        except Exception as e:
            logging.error("Failed to initialize Kafka producer: %s", e)
            return

        while not self._stop_event.is_set():
            try:
                cpu, cpu_cores, total, used, gpus, storage = self.get_stats()

                # Format GPU info for output: {0: {"used_gb": x, "total_gb": y}, ...}
                gpu_memory_gb = {k: {"used_gb": v[0], "total_gb": v[1]} for k, v in gpus.items()}
                # Format storage info for output: {"/": {"free_gb": x, "total_gb": y}, ...}
                storage_gb = {k: {"free_gb": v[0], "total_gb": v[1]} for k, v in storage.items()}
                payload = {
                    "instance_id": self.instance_id,
                    "cpu_usage_percent": round(cpu, 2),
                    "cpu_cores": cpu_cores,
                    "ram_total_gb": round(total, 2),
                    "ram_used_gb": round(used, 2),
                    "gpu_memory_gb": gpu_memory_gb,  # dict: {0: {used_gb, total_gb}, ...}
                    "storage_gb": storage_gb,  # dict: {"/": {free_gb, total_gb}, ...}
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                self._producer.send(self.topic_name, payload)
                self._producer.flush()

                logging.debug("Published resource stats: %s", payload)

            except Exception as e:
                logging.error("Error in resource monitor loop: %s", e)

            # Wait for interval or until stop event is set
            if self._stop_event.wait(self.interval_seconds):
                break

        # Cleanup
        if self._producer:
            try:
                self._producer.close()
            except Exception as e:
                logging.debug("Error closing Kafka producer: %s", e)

        logging.info("Kafka resource monitor stopped.")

    @log_errors(raise_exception=False, log_error=True)
    def start(self):
        """
        Start the resource monitoring thread.

        Returns:
            bool: True if started successfully, False otherwise.
        """
        if self._is_running:
            logging.warning("Kafka resource monitor is already running.")
            return False

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_worker,
            daemon=True,
            name="KafkaResourceMonitor"
        )
        self._monitor_thread.start()
        self._is_running = True

        logging.info("Started Kafka resource monitor thread.")
        return True

    @log_errors(raise_exception=False, log_error=True)
    def stop(self, timeout: int = 10):
        """
        Stop the resource monitoring thread gracefully.

        Args:
            timeout: Maximum time to wait for thread to stop in seconds.

        Returns:
            bool: True if stopped successfully, False otherwise.
        """
        if not self._is_running:
            logging.warning("Kafka resource monitor is not running.")
            return False

        logging.info("Stopping Kafka resource monitor...")
        self._stop_event.set()

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=timeout)

            if self._monitor_thread.is_alive():
                logging.error("Kafka resource monitor thread did not stop within timeout.")
                return False

        self._is_running = False
        logging.info("Kafka resource monitor stopped successfully.")
        return True

    def is_running(self) -> bool:
        """
        Check if the resource monitor is currently running.

        Returns:
            bool: True if running, False otherwise.
        """
        return self._is_running

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
