"""Auto-generated stubs for package: matrice_compute."""
from typing import Any, Dict, List, Optional, Set, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from datetime import datetime
from datetime import datetime, timezone
from docker.client import DockerClient
from docker.models.containers import Container
from kafka import KafkaProducer
from kafka import KafkaProducer, KafkaConsumer
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from matrice.docker_utils import check_docker
from matrice_common.session import Session
from matrice_common.stream.event_listener import EventListener
from matrice_common.utils import log_errors
from matrice_compute.action_instance import ActionInstance
from matrice_compute.actions_manager import ActionsManager
from matrice_compute.actions_scaledown_manager import ActionsScaleDownManager
from matrice_compute.compute_operations_handler import ComputeOperationsHandler
from matrice_compute.instance_utils import get_docker_disk_space_usage
from matrice_compute.instance_utils import get_gpu_with_sufficient_memory_for_action, get_decrypted_access_key_pair, get_max_file_system, get_best_service_ip_and_network
from matrice_compute.instance_utils import get_instance_info, cleanup_docker_storage, get_cpu_memory_usage, get_gpu_memory_usage, get_mem_usage, get_gpu_with_sufficient_memory_for_action, get_max_file_system, has_gpu
from matrice_compute.instance_utils import get_instance_info, get_decrypted_access_key_pair
from matrice_compute.instance_utils import has_gpu, get_gpu_info, calculate_time_difference
from matrice_compute.instance_utils import has_gpu, get_mem_usage, cleanup_docker_storage
from matrice_compute.resources_tracker import MachineResourcesTracker, ActionsResourcesTracker, KafkaResourceMonitor, ContainerResourceMonitor
from matrice_compute.resources_tracker import ResourcesTracker, MachineResourcesTracker, ActionsResourcesTracker
from matrice_compute.scaling import Scaling
from matrice_compute.shutdown_manager import ShutdownManager
from matrice_compute.task_utils import setup_workspace_and_run_task
import base64
import docker
import json
import logging
import os
import platform
import psutil
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import time as time_module
import torch
import traceback
import urllib.parse
import urllib.request
import uuid
import zipfile

# Constants
logger: Any = ...  # From compute_operations_handler
logger: Any = ...  # From k8s_scheduler

# Functions
# From action_instance
def augmentation_server_creation_execute(self) -> Any:
    """
    Create Augmentation Server
    """
    ...

# From action_instance
def data_preparation_execute(self) -> Any:
    """
    Execute data preparation task.
    """
    ...

# From action_instance
def data_processing_execute(self) -> Any:
    """
    Execute data processing task.
    """
    ...

# From action_instance
def data_split_execute(self) -> Any:
    """
    Execute data split task.
    """
    ...

# From action_instance
def database_setup_execute(self) -> Any:
    """
    Creates and setup the database for facial recognition server.
    MongoDB runs on port 27020:27017 (localhost only with --net=host).
    Qdrant runs on port 6334 (localhost only with --net=host).
    """
    ...

# From action_instance
def dataset_annotation_execute(self) -> Any:
    """
    Execute dataset annotation task.
    """
    ...

# From action_instance
def dataset_augmentation_execute(self) -> Any:
    """
    Execute dataset augmentation task.
    """
    ...

# From action_instance
def deploy_aggregator_execute(self) -> Any:
    """
    Execute deploy aggregator task.
    """
    ...

# From action_instance
def facial_recognition_setup_execute(self) -> Any:
    """
    Creates and setup the facial recognition worker server.
    Facial recognition worker runs on port 8081 (localhost only with --net=host).
    """
    ...

# From action_instance
def fe_analytics_service_execute(self) -> Any:
    """
    Creates and setup the frontend analytics service.
    Frontend analytics service runs on port 3001 (localhost only with --net=host).
    """
    ...

# From action_instance
def fe_fs_streaming_execute(self) -> Any:
    """
    Creates and setup the frontend for fs streaming.
    Frontend streaming runs on port 3000 (localhost only with --net=host).
    """
    ...

# From action_instance
def image_build_execute(self) -> Any:
    """
    Execute image building task.
    """
    ...

# From action_instance
def inference_tracker_setup_execute(self) -> Any:
    """
    Creates and start inference tracker.
    Inference tracker runs on port 8110 (localhost only with --net=host).
    """
    ...

# From action_instance
def inference_ws_server_execute(self) -> Any:
    """
    Creates and start inference pipeline.
    Inference WebSocket server runs on port 8102 (localhost only with --net=host).
    """
    ...

# From action_instance
def kafka_setup_execute(self) -> Any:
    """
    Execute kafka server task.
    Kafka runs on port 9092 (SASL_PLAINTEXT) and 9093 (CONTROLLER) - localhost only with --net=host.
    """
    ...

# From action_instance
def lpr_setup_execute(self) -> Any:
    """
    Creates and setup the license plate recognition server.
    LPR worker runs on port 8082 (localhost only with --net=host).
    """
    ...

# From action_instance
def model_deploy_execute(self) -> Any:
    """
    Execute model deployment task.
    """
    ...

# From action_instance
def model_eval_execute(self) -> Any:
    """
    Execute model evaluation task.
    """
    ...

# From action_instance
def model_export_execute(self) -> Any:
    """
    Execute model export task.
    """
    ...

# From action_instance
def model_train_execute(self) -> Any:
    """
    Execute model training task.
    """
    ...

# From action_instance
def redis_setup_execute(self) -> Any:
    """
    Creates and starts a Redis container using Docker.
    Redis runs on port 6379 (localhost only with --net=host).
    """
    ...

# From action_instance
def resource_clone_execute(self) -> Any:
    """
    Execute resource clone task.
    """
    ...

# From action_instance
def streaming_gateway_execute(self) -> Any:
    """
    Execute streaming gateway task.
    """
    ...

# From action_instance
def synthetic_data_setup_execute(self) -> Any:
    """
    Execute synthetic data setup task.
    """
    ...

# From action_instance
def synthetic_dataset_generation_execute(self) -> Any:
    """
    Execute synthetic dataset generation task.
    """
    ...

# From action_instance
def video_storage_setup_execute(self) -> Any:
    """
    Creates and start Video Storage
    Video Stroage runs on port 8106 (localhost only with --net=host).
    """
    ...

# From instance_utils
def calculate_time_difference(start_time_str: str, finish_time_str: str) -> int:
    """
    Calculate time difference between start and finish times.
    
    Robust handling of timestamps from different cloud providers (AWS, GCP, Azure, OCI)
    and different precision levels (nanoseconds, microseconds, milliseconds).
    
    Args:
        start_time_str (str): Start time string in ISO format
        finish_time_str (str): Finish time string in ISO format
    
    Returns:
        int: Time difference in seconds
    """
    ...

# From instance_utils
def cleanup_docker_storage() -> None:
    """
    Clean up Docker storage if space is low.
    """
    ...

# From instance_utils
def get_best_service_ip_and_network(port: int) -> tuple:
    """
    Determine the best IP address and network configuration for a service.
    
    This function intelligently selects the best IP to bind a service to:
    
    Priority:
    1. Public IP if it's actually on a local interface (cloud servers)
    2. Private/LAN IP (NAT, local network, Docker)
    3. localhost with --net=host (fallback)
    
    Args:
        port (int): Port number for the service
    
    Returns:
        tuple: (ip_address, use_host_network) where:
            - ip_address: The IP address to use (public, private, or localhost)
            - use_host_network: True if should use --net=host, False if should use port mapping
    """
    ...

# From instance_utils
def get_cpu_memory_usage() -> float:
    """
    Get CPU memory usage.
    
    Returns:
        float: Memory usage between 0 and 1
    """
    ...

# From instance_utils
def get_decrypted_access_key_pair(enc_access_key: str, enc_secret_key: str, encryption_key: str = '') -> Tuple[Optional[str], Optional[str]]:
    """
    Get decrypted access key pair.
    
    Args:
        enc_access_key (str): Encrypted access key
        enc_secret_key (str): Encrypted secret key
        encryption_key (str): Encryption key
    
    Returns:
        tuple: (access_key, secret_key) strings
    """
    ...

# From instance_utils
def get_disk_space_usage() -> list:
    """
    Get disk space usage for all filesystems.
    
    Returns:
        list: List of disk usage information dictionaries
    """
    ...

# From instance_utils
def get_docker_disk_space_usage() -> dict:
    """
    Get disk space usage for Docker storage.
    
    Returns:
        dict: Docker disk usage information
    """
    ...

# From instance_utils
def get_encrypted_access_key_pair(access_key: str, secret_key: str, encryption_key: str = '') -> Tuple[Optional[str], Optional[str]]:
    """
    Get encrypted access key pair.
    
    Args:
        access_key (str):  access key
        secret_key (str):  secret key
        encryption_key (str): Encryption key
    
    Returns:
        tuple: (encrypted_access_key, encrypted_secret_key) strings
    """
    ...

# From instance_utils
def get_gpu_config_for_deployment(action_details, is_first_deployment = False) -> Any:
    """
    Get GPU configuration for deployment actions.
    
        For first deployment of a service, attempts to use all GPUs.
        For subsequent deployments, uses standard GPU selection (most free memory).
        Falls back gracefully to standard GPU selection if '--gpus all' is not available.
    
        Args:
            action_details (dict): Action details containing GPU requirements
            is_first_deployment (bool): Whether this is the first deployment for this service
    
        Returns:
            str: GPU configuration string ('--gpus all' or '--gpus "device=X"' or '')
    """
    ...

# From instance_utils
def get_gpu_info() -> list:
    """
    Get GPU information.
    
    Returns:
        list: GPU information strings
    """
    ...

# From instance_utils
def get_gpu_memory_usage() -> float:
    """
    Get GPU memory usage percentage.
    
    Returns:
        float: Memory usage between 0 and 1
    """
    ...

# From instance_utils
def get_gpu_with_sufficient_memory_for_action(action_details: dict) -> list:
    """
    Get GPUs with sufficient memory for action.
    
    Args:
        action_details (dict): Action details
    
    Returns:
        list: List of GPU indices
    
    Raises:
        ValueError: If insufficient GPU memory
    """
    ...

# From instance_utils
def get_instance_id() -> str:
    """
    Get instance ID.
    
    Returns:
        str: Instance ID or empty string
    """
    ...

# From instance_utils
def get_instance_info(service_provider: Optional[str] = None, instance_id: Optional[str] = None) -> tuple:
    """
    Get instance provider and ID information.
    
    Returns:
        tuple: (service_provider, instance_id) strings
    """
    ...

# From instance_utils
def get_max_file_system() -> Optional[str]:
    """
    Get filesystem with maximum available space.
    
    Returns:
        str: Path to filesystem with most space or None
    """
    ...

# From instance_utils
def get_mem_usage() -> float:
    """
    Get memory usage for either GPU or CPU.
    
    Returns:
        float: Memory usage between 0 and 1
    """
    ...

# From instance_utils
def get_required_gpu_memory(action_details: dict) -> int:
    """
    Get required GPU memory from action details.
    
    Args:
        action_details (dict): Action details
    
    Returns:
        int: Required GPU memory
    """
    ...

# From instance_utils
def get_single_gpu_with_sufficient_memory_for_action(action_details: dict) -> list:
    """
    Get single GPU with sufficient memory using most-free algorithm.
    
    Selects the GPU with the MOST free memory that meets the requirements,
    to balance load across GPUs and prevent any single GPU from being overused.
    
    Args:
        action_details (dict): Action details
    
    Returns:
        list: List with single GPU index
    
    Raises:
        ValueError: If no GPU has sufficient memory
    """
    ...

# From instance_utils
def has_gpu() -> bool:
    """
    Check if the system has a GPU.
    
    Returns:
        bool: True if GPU is present, False otherwise
    """
    ...

# From instance_utils
def is_allowed_gpu_device(gpu_index: int) -> bool:
    """
    Check if GPU device is allowed based on GPUS environment variable.
    
        The GPUS environment variable can be used to restrict which GPU devices
        are available for allocation (e.g., GPUS="0,2" allows only GPU 0 and 2).
    
        Args:
            gpu_index (int): GPU device index
    
        Returns:
            bool: True if GPU is allowed (or no filter is set), False otherwise
    """
    ...

# From instance_utils
def is_docker_running() -> bool:
    """
    Check if Docker is running.
    
    Returns:
        bool: True if Docker containers are running
    """
    ...

# From instance_utils
def prune_docker_images() -> None:
    """
    Prune Docker images.
    """
    ...

# From task_utils
def refresh_url_if_needed(url: Optional[str], scaling: Optional[Scaling] = None) -> Optional[str]:
    """
    Refresh a presigned URL if it appears to be expired or about to expire.
    
        This function attempts to refresh presigned URLs for model codebase and requirements
        to ensure they are valid before downloading.
    
        Args:
            url: The URL to potentially refresh. If None or empty, returns None.
            scaling: The Scaling instance to use for API calls. If None, returns original URL.
    
        Returns:
            The refreshed URL if successful, or the original URL if refresh fails or is not needed.
    """
    ...

# From task_utils
def setup_workspace_and_run_task(work_fs: str, action_id: str, model_codebase_url: str, model_codebase_requirements_url: Optional[str] = None, scaling: Optional[Scaling] = None) -> None:
    """
    Set up workspace and run task with provided parameters.
    
        Args:
            work_fs (str): Working filesystem path.
            action_id (str): Unique identifier for the action.
            model_codebase_url (str): URL to download model codebase from.
            model_codebase_requirements_url (Optional[str]): URL to download requirements from. Defaults to None.
            scaling (Optional[Scaling]): Scaling instance for refreshing presigned URLs. Defaults to None.
    
        Returns:
            None
    """
    ...

# Classes
# From action_instance
class ActionInstance:
    """
    Base class for tasks that run in Action containers.
    """

    def __init__(self, scaling, action_info: dict) -> None:
        """
        Initialize an action instance.
        
                Args:
                    scaling (Scaling): Scaling service instance
                    action_info (dict): Action information dictionary
        """
        ...

    def execute(self) -> Any:
        """
        Execute the task.
        """
        ...

    def get_action_details(self) -> Any:
        """
        Get action details from scaling service.
        
                Returns:
                    dict: Action details if successful, None otherwise
        """
        ...

    def get_base_docker_cmd(self, work_fs: str = '', use_gpu: str = '', mount_docker_sock: bool = False, action_id: str = '', model_key: str = '', extra_env_vars: dict = {}, port_mapping: dict = {}, network_config: str = '', destination_workspace_path: str = '/usr/src/workspace', docker_workdir: str = '', extra_pkgs: list = []) -> Any:
        """
        Build base Docker command with common options.
        
                Args:
                    work_fs (str): Work filesystem path
                    use_gpu (str): GPU configuration string
                    mount_docker_sock (bool): Whether to mount Docker socket
                    action_id (str): Action ID
                    model_key (str): Model key
                    extra_env_vars (dict): Additional environment variables
                    port_mapping (dict): Port mappings {host_port: container_port}
                    destination_workspace_path (str): Container workspace path
                    docker_workdir (str): Docker working directory
                    extra_pkgs (list): List of extra packages to install
                Returns:
                    str: Base Docker command
        """
        ...

    def get_gpu_config(self, action_details) -> Any:
        """
        Get GPU configuration string based on available GPUs.
        
                Args:
                    action_details (dict): Action details containing GPU requirements
        
                Returns:
                    str: GPU configuration string
        """
        ...

    def get_hugging_face_token(self, model_key) -> Any:
        """
        Get Hugging Face token for specific model keys.
        
                Args:
                    model_key (str): Model key to check
        
                Returns:
                    str: Hugging Face token if available, empty string otherwise
        """
        ...

    def get_hugging_face_token_for_data_generation(self) -> Any: ...

    def get_internal_api_key(self, action_id) -> Any:
        """
        Get internal API key for action.
        
                Args:
                    action_id (str): Action ID
        
                Returns:
                    str: Internal API key if available, empty string otherwise
        """
        ...

    def get_log_path(self) -> Any:
        """
        Get log directory path, creating if needed.
        
                Returns:
                    str: Path to log directory
        """
        ...

    def is_running(self) -> bool:
        """
        Check if task process is running.
        
                This method performs a thorough check to determine if the process is still running:
                1. Verifies that the process attribute exists and is not None
                2. Checks if the process has terminated using poll() method
                3. Additional safeguards against zombie processes
                4. Coordinates with log monitoring to ensure all logs are sent before cleanup
        
                Returns:
                    bool: True if process exists and is still running, False if process
                         does not exist or has terminated
        """
        ...

    def send_logs_continuously(self) -> Any:
        """
        Continuously read and send logs from the log file to the scaling service.
        
                Enhanced version that tracks log position and handles graceful shutdown.
        """
        ...

    def setup_action_requirements(self, action_details, work_fs = '', model_family = '', action_id = '') -> Any:
        """
        Setup action requirements.
        
                Args:
                    action_details (dict): Action details
                    work_fs (str): Work filesystem path
                    model_family (str): Model family name
                    action_id (str): Action ID
        
                Raises:
                    Exception: If setup fails
        """
        ...

    def start(self, cmd: str = '', log_name: str = '') -> Any:
        """
        Start the process and log monitoring thread.
        
                Args:
                    cmd (str): Command to execute
                    log_name (str): Name for log file
        """
        ...

    def start_logger(self) -> Any:
        """
        Start the log monitoring thread.
        """
        ...

    def start_process(self, cmd, log_name) -> Any:
        """
        Start the process and initialize logging.
        
                Args:
                    cmd (str): Command to execute
                    log_name (str): Name for log file
        
                Raises:
                    Exception: If process fails to start
        """
        ...

    def stop(self) -> Any:
        """
        Stop the process and log monitoring thread.
        
                Enhanced version that ensures proper cleanup sequencing and log completion.
        """
        ...


# From actions_manager
class ActionsManager:
    """
    Class for managing actions.
    """

    def __init__(self, scaling) -> None:
        """
        Initialize an action manager.
        
                Args:
                    scaling (Scaling): Scaling service instance
        """
        ...

    def fetch_actions(self) -> list:
        """
        Poll for actions and process them if memory threshold is not exceeded.
        
                Returns:
                    list: List of fetched actions
        """
        ...

    def get_all_actions(self) -> dict:
        """
        Get all tracked actions (both running and stopped).
        
                Returns:
                    dict: All tracked actions with their status
        """
        ...

    def get_current_actions(self) -> dict:
        """
        Get the current running actions.
        
                This method:
                1. Updates action status tracking via update_actions_status()
                2. Returns only the running actions (current_actions dict)
                3. Provides detailed logging about current actions state
        
                Returns:
                    dict: Current running actions only
        """
        ...

    def get_stopped_actions(self) -> dict:
        """
        Get stopped actions.
        
                Returns:
                    dict: Stopped actions
        """
        ...

    def process_action(self, action: dict) -> Any:
        """
        Process the given action.
        
                Args:
                    action (dict): Action details to process
        
                Returns:
                    ActionInstance: Processed action instance or None if failed
        """
        ...

    def process_actions(self) -> None:
        """
        Process fetched actions.
        """
        ...

    def purge_unwanted(self) -> None:
        """
        Purge completed or failed actions.
        
                NOTE: This now calls update_actions_status() which moves stopped actions
                to a separate dict instead of deleting them. This prevents interference
                with compute operations handler while maintaining accurate status.
        """
        ...

    def restart_action(self, action_record_id: str) -> dict:
        """
        Restart a specific action by its record ID.
        
                This method stops the action if it's running, then fetches fresh action
                details from the backend and starts it again.
        
                Args:
                    action_record_id (str): The action record ID to restart
        
                Returns:
                    dict: Result dictionary with status information
        """
        ...

    def start_actions_manager(self) -> None:
        """
        Start the actions manager main loop.
        """
        ...

    def stop_action(self, action_record_id: str) -> dict:
        """
        Stop a specific action by its record ID.
        
                Args:
                    action_record_id (str): The action record ID to stop
        
                Returns:
                    dict: Result dictionary with status information
        """
        ...

    def update_actions_status(self) -> None:
        """
        Update tracking of running vs stopped actions.
        
                This method checks all actions and moves stopped ones to stopped_actions dict
                without deleting them. This prevents interference with compute operations
                handler while maintaining accurate status reporting.
        """
        ...


# From actions_scaledown_manager
class ActionsScaleDownManager:
    """
    Class for managing container scale down operations.
    """

    def __init__(self, scaling) -> None:
        """
        Initialize the scale down manager.
        
                Args:
                    scaling (Scaling): Scaling service instance
        """
        ...

    def auto_scaledown_actions(self) -> None:
        """
        Start polling for containers that need to be scaled down and stop them.
        """
        ...


# From compute_operations_handler
class ComputeOperationsHandler:
    """
    Handles Kafka-based compute operations for instance and action management.
    
    This class uses EventListener from matrice_common to listen for operation
    events from the 'compute_operations' Kafka topic. It delegates operations
    to the ActionsManager for execution and updates status via API calls.
    """

    def __init__(self, actions_manager, session, scaling, instance_id: str) -> None:
        """
        Initialize the Compute Operations Handler.
        
        Args:
            actions_manager: Reference to the ActionsManager instance
            session: Session object for authentication and Kafka configuration
            scaling: Scaling service instance for API status updates
            instance_id: This compute instance's ID for filtering events
        """
        ...

    KAFKA_TOPIC: Any

    def start(self) -> bool:
        """
        Start the operations handler using EventListener.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        ...

    def stop(self) -> Any:
        """
        Stop the operations handler gracefully.
        """
        ...


# From instance_manager
class InstanceManager:
    """
    Class for managing compute instances and their associated actions.
    
        Now includes auto streaming capabilities for specified deployment IDs.
    """

    def __init__(self, matrice_access_key_id: str = '', matrice_secret_access_key: str = '', encryption_key: str = '', instance_id: str = '', service_provider: str = '', env: str = '', gpus: str = '', workspace_dir: str = 'matrice_workspace', enable_kafka: bool = False) -> None:
        """
        Initialize an instance manager.
        
                Args:
                    matrice_access_key_id (str): Access key ID for Matrice authentication.
                        Defaults to empty string.
                    matrice_secret_access_key (str): Secret access key for Matrice
                        authentication. Defaults to empty string.
                    encryption_key (str): Key used for encrypting sensitive data.
                        Defaults to empty string.
                    instance_id (str): Unique identifier for this compute instance.
                        Defaults to empty string.
                    service_provider (str): Cloud service provider being used.
                        Defaults to empty string.
                    env (str): Environment name (e.g. dev, prod).
                        Defaults to empty string.
                    gpus (str): GPU configuration string (e.g. "0,1").
                        Defaults to empty string.
                    workspace_dir (str): Directory for workspace files.
                        Defaults to "matrice_workspace".
                    enable_kafka (bool): Enable Kafka communication (default False).
        """
        ...

    def start(self) -> tuple:
        """
        Start the instance manager threads.
        
                Returns:
                    tuple: (instance_manager_thread, actions_manager_thread)
        """
        ...

    def start_container_status_monitor(self) -> Any:
        """
        Start the background container status monitoring.
        """
        ...

    def start_instance_manager(self) -> None:
        """
        Run the instance manager loop.
        """
        ...

    def stop(self) -> Any:
        """
        Stop all background threads and cleanup resources.
        """
        ...

    def stop_container_status_monitor(self) -> Any:
        """
        Stop the background container status monitoring.
        """
        ...


# From k8s_scheduler
class K8sScheduler:
    """
    Kubernetes Scheduler that polls for actions and creates K8s Jobs.
    Runs inside the cluster using in-cluster authentication.
    """

    def __init__(self) -> None: ...

    def check_job_status(self, action_id: str, job_name: str, namespace: str) -> Optional[str]:
        """
        Check the status of a K8s job and return status if completed. Also monitors resource usage.
        """
        ...

    def create_k8s_job(self, action: Dict[str, Any]) -> Optional[str]:
        """
        Create a Kubernetes Job for the given action
        """
        ...

    def monitor_running_jobs(self) -> Any:
        """
        Monitor running jobs and update action statuses
        """
        ...

    def poll_pending_actions(self) -> List[Dict[str, Any]]:
        """
        Poll for actions assigned to this Kubernetes cluster.
        
        Uses the new K8s-specific endpoint:
        - processClusterName in be-action detects K8s clusters and sets kubernetesClusterId
        - Scheduler calls /v1/actions/assign_jobs_kubernetes/{cluster_id} to fetch assigned actions
        """
        ...

    def send_heartbeat(self) -> Any:
        """
        Send heartbeat to Matrice API with cluster health info
        """
        ...

    def start(self) -> Any:
        """
        Main scheduler loop - matches InstanceManager.start() pattern
        """
        ...

    def update_action_status(self, action_id: str, step_code: str, status: str, description: str, extra_details: Optional[Dict] = None) -> Any:
        """
        Update action status using the existing action update endpoint.
        
        Uses the standard action record update API that accepts:
        - stepCode: The step code for the action
        - status: Status (OK, ERROR, etc.)
        - statusDescription: Human-readable description
        
        Extra details are merged into the action record's actionDetails.
        """
        ...


# From prechecks
class Prechecks:
    """
    Class for running pre-checks before compute operations.
    """

    def __init__(self, session, instance_id: Optional[str] = None) -> None:
        """
        Initialize Prechecks.
        
                Args:
                    session: Session object for RPC calls
                    instance_id: Optional instance ID
        """
        ...

    def check_credentials(self, access_key: Optional[str] = None, secret_key: Optional[str] = None) -> bool:
        """
        Check if access key and secret key are valid.
        
                Args:
                    access_key: Optional access key to validate
                    secret_key: Optional secret key to validate
        
                Returns:
                    bool: True if credentials are valid
        """
        ...

    def check_docker(self) -> bool:
        """
        Check if docker is installed and working.
        
                Returns:
                    bool: True if docker is working
        """
        ...

    def check_fetch_actions(self) -> bool:
        """
        Test action fetching and validation.
        
                Returns:
                    bool: True if action fetching works
        """
        ...

    def check_filesystem_space(self) -> bool:
        """
        Check available filesystem space and usage.
        
                Returns:
                    bool: True if filesystem space is sufficient
        """
        ...

    def check_get_gpu_indices(self) -> bool:
        """
        Check if get_gpu_indices returns valid indices.
        
                Returns:
                    bool: True if GPU indices are valid
        """
        ...

    def check_gpu(self) -> bool:
        """
        Check if machine has GPU and it's functioning.
        
                Returns:
                    bool: True if GPU check passes
        """
        ...

    def check_instance_id(self, instance_id: Optional[str] = None) -> bool:
        """
        Validate instance ID from args or env.
        
                Args:
                    instance_id: Optional instance ID to validate
        
                Returns:
                    bool: True if instance ID is valid
        """
        ...

    def check_resources(self) -> bool:
        """
        Validate system resource limits and availability.
        
                Returns:
                    bool: True if resource checks pass
        """
        ...

    def check_resources_tracking(self) -> bool:
        """
        Test resource tracking updates and monitoring.
        
                Returns:
                    bool: True if resource tracking is working
        """
        ...

    def check_scaling_status(self) -> bool:
        """
        Test scaling service status.
        
                Returns:
                    bool: True if scaling status is ok
        """
        ...

    def cleanup_docker_storage(self) -> bool:
        """
        Clean up docker storage and verify space freed.
        
                Returns:
                    bool: True if cleanup successful
        """
        ...

    def create_docker_volume(self) -> bool:
        """
        Create docker volume.
        
        Returns:
            bool: True if volume created successfully
        """
        ...

    def get_available_resources(self) -> bool:
        """
        Check available system resources are within valid ranges.
        
                Returns:
                    bool: True if resources are within valid ranges
        """
        ...

    def get_shutdown_details(self) -> bool:
        """
        Get and validate shutdown details from response.
        
                Returns:
                    bool: True if shutdown details are valid
        """
        ...

    def run_all_checks(self, instance_id: Optional[str] = None, access_key: Optional[str] = None, secret_key: Optional[str] = None) -> bool:
        """
        Run all prechecks in sequence.
        
                Args:
                    instance_id: Optional instance ID to validate
                    access_key: Optional access key to validate
                    secret_key: Optional secret key to validate
        
                Returns:
                    bool: True if all checks pass
        """
        ...

    def setup_docker(self) -> bool:
        """
        Setup docker.
        
        Returns:
            bool: True if setup successful
        """
        ...

    def test_actions_scale_down(self) -> bool:
        """
        Test actions scale down.
        
                Returns:
                    bool: True if scale down test passes
        """
        ...

    def test_gpu(self) -> bool:
        """
        Test if GPU is working and has sufficient memory.
        
                Returns:
                    bool: True if GPU test passes
        """
        ...


# From resources_tracker
class ActionsResourcesTracker:
    """
    Tracks Docker container action resources
    """

    def __init__(self, scaling) -> None:
        """
        Initialize ActionsResourcesTracker
        """
        ...

    def get_current_action_usage(self, container, status: str) -> Tuple[float, int, float, float]:
        """
        Get current resource usage for a container
        """
        ...

    def get_sub_containers_by_label(self, label_key: str, label_value: str) -> list:
        """
        Get running containers with specified label key and value
        """
        ...

    def update_actions_resources(self) -> None:
        """
        Process both running and exited containers.
        
                Note: Does not remove containers to keep logs. Only tracks resource usage.
        """
        ...

    def update_max_action_usage(self, action_record_id: str, current_gpu_utilization: float, current_gpu_memory: int, current_cpu_utilization: float, current_memory_utilization: float) -> Tuple[float, int, float, float]:
        """
        Update and return maximum resource usage values for an action
        """
        ...


# From resources_tracker
class ContainerResourceMonitor:
    """
    Monitors individual container resource utilization and publishes to Kafka.
    This thread runs independently and reports CPU, memory, and GPU usage for all running containers.
    """

    def __init__(self, instance_id: Optional[str] = None, kafka_bootstrap: Optional[str] = None, interval_seconds: int = 30) -> None:
        """
        Initialize ContainerResourceMonitor.
        
        Args:
            instance_id: Instance identifier for Kafka topic. Defaults to INSTANCE_ID env var.
            kafka_bootstrap: Kafka bootstrap servers. Required - should be obtained from Scaling.get_kafka_bootstrap_servers().
            interval_seconds: Interval between container checks in seconds. Defaults to 30.
        """
        ...

    def is_running(self) -> bool:
        """
        Check if the container resource monitor is currently running.
        
        Returns:
            bool: True if running, False otherwise.
        """
        ...

    def start(self) -> Any:
        """
        Start the container resource monitoring thread.
        
        Returns:
            bool: True if started successfully, False otherwise.
        """
        ...

    def stop(self, timeout: int = 10) -> Any:
        """
        Stop the container resource monitoring thread gracefully.
        
        Args:
            timeout: Maximum time to wait for thread to stop in seconds.
        
        Returns:
            bool: True if stopped successfully, False otherwise.
        """
        ...


# From resources_tracker
class KafkaResourceMonitor:
    """
    Monitors system resources and publishes them to Kafka in a separate thread.
    This class provides thread-safe start/stop operations for resource monitoring.
    """

    def __init__(self, instance_id: Optional[str] = None, kafka_bootstrap: Optional[str] = None, interval_seconds: int = 60) -> None:
        """
        Initialize KafkaResourceMonitor.
        
        Args:
            instance_id: Instance identifier for Kafka topic. Defaults to INSTANCE_ID env var.
            kafka_bootstrap: Kafka bootstrap servers. Required - should be obtained from Scaling.get_kafka_bootstrap_servers().
            interval_seconds: Interval between resource checks in seconds. Defaults to 60.
        """
        ...

    def get_all_gpu_memory() -> Dict[int, tuple]:
        """
        Get GPU memory usage and total for all GPUs.
        
        Returns:
            Dict[int, tuple]: Dictionary mapping GPU ID to (used_gb, total_gb).
                             Returns empty dict if nvidia-smi is not available.
        """
        ...

    def get_all_storage_info() -> Dict[str, tuple]:
        """
        Get storage information for all mounted drives.
        
        Returns:
            Dict[str, tuple]: Dictionary mapping mount point to (free_gb, total_gb).
        """
        ...

    def get_stats(self) -> Tuple[float, int, float, float, Dict[int, tuple], Dict[str, tuple]]:
        """
        Collect current system resource statistics.
        
        Returns:
            Tuple[float, int, float, float, Dict[int, tuple], Dict[str, tuple]]:
            CPU usage %, CPU cores, RAM total GB, RAM used GB, GPU memory dict (used, total), Storage dict (free, total)
        """
        ...

    def is_running(self) -> bool:
        """
        Check if the resource monitor is currently running.
        
        Returns:
            bool: True if running, False otherwise.
        """
        ...

    def start(self) -> Any:
        """
        Start the resource monitoring thread.
        
        Returns:
            bool: True if started successfully, False otherwise.
        """
        ...

    def stop(self, timeout: int = 10) -> Any:
        """
        Stop the resource monitoring thread gracefully.
        
        Args:
            timeout: Maximum time to wait for thread to stop in seconds.
        
        Returns:
            bool: True if stopped successfully, False otherwise.
        """
        ...


# From resources_tracker
class MachineResourcesTracker:
    """
    Tracks machine-level resources like CPU, memory and GPU
    """

    def __init__(self, scaling) -> None:
        """
        Initialize MachineResourcesTracker
        """
        ...

    def update_available_resources(self) -> Any:
        """
        Update available machine resources
        """
        ...


# From resources_tracker
class ResourcesTracker:
    """
    Tracks machine and container resources.
    
        GPU Utilization Note:
            GPU utilization is tracked at the DEVICE level, not per-container.
            NVIDIA does not expose reliable per-process GPU utilization.
            Per-container GPU MEMORY is accurate; per-container GPU UTILIZATION is best-effort.
    """

    def __init__(self) -> None:
        """
        Initialize ResourcesTracker.
        """
        ...

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
        ...

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
        ...

    def get_container_cpu_and_memory(self, container) -> Tuple[float, float]:
        """
        Get CPU and memory usage for a container.
        
        Args:
            container (docker.models.containers.Container): Docker container instance.
        
        Returns:
            Tuple[float, float]: CPU utilization percentage (0-100 per core used) and memory usage in MB.
        """
        ...

    def get_container_cpu_and_memory_with_container_id(self, container_id: str) -> Tuple[float, float]:
        """
        Get CPU and memory usage for a specific container by its ID.
        
        Args:
            container_id (str): ID of the Docker container.
        
        Returns:
            Tuple[float, float]: CPU utilization percentage and memory usage in MB.
        """
        ...

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
        ...

    def get_container_gpu_memory_usage(self, container_pid: str) -> int:
        """
        Get GPU memory usage for a container PID.
        
        Args:
            container_pid (str): PID of the Docker container.
        
        Returns:
            int: GPU memory usage in MB.
        """
        ...

    def get_container_gpu_memory_usage_multi_pid(self, container_pids: set) -> int:
        """
        Get GPU memory usage for multiple container PIDs.
        
        Args:
            container_pids (set): Set of container PIDs (as strings).
        
        Returns:
            int: Total GPU memory usage in MB across all matching processes.
        """
        ...

    def get_container_gpu_usage(self, container_pid: str) -> float:
        """
        Get GPU usage for a container PID.
        
        Args:
            container_pid (str): PID of the Docker container.
        
        Returns:
            float: GPU utilization percentage.
        """
        ...

    def get_container_gpu_usage_multi_pid(self, container_pids: set) -> float:
        """
        Get GPU usage for multiple container PIDs.
        
        Args:
            container_pids (set): Set of container PIDs (as strings).
        
        Returns:
            float: Total GPU utilization percentage across all matching processes.
        """
        ...

    def get_pid_id_by_container_id(self, container_id: str) -> str:
        """
        Get PID for a container ID.
        
        Args:
            container_id (str): ID of the Docker container.
        
        Returns:
            str: PID of the container.
        """
        ...


# From scaling
class Scaling:
    """
    Class providing scaling functionality for compute instances.
    """

    def __init__(self, session, instance_id = None, enable_kafka = False) -> None:
        """
        Initialize Scaling instance.
        
                Args:
                    session: Session object for making RPC calls
                    instance_id: ID of the compute instance
                    enable_kafka: Enable Kafka communication (default True)
        
                Raises:
                    Exception: If instance_id is not provided
        """
        ...

    def add_account_compute_instance(self, account_number, alias, service_provider, instance_type, shut_down_time, lease_type, launch_duration) -> Any:
        """
        Add a compute instance for an account.
        
                Args:
                    account_number: Account number
                    alias: Instance alias
                    service_provider: Cloud service provider
                    instance_type: Type of instance
                    shut_down_time: Time to shutdown
                    lease_type: Type of lease
                    launch_duration: Duration to launch
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def assign_jobs(self, is_gpu) -> Any:
        """
        Assign jobs to the instance using REST API.
        
                Args:
                    is_gpu: Boolean or any value indicating if this is a GPU instance.
                            Will be converted to proper boolean.
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def delete_account_compute(self, account_number, alias) -> Any:
        """
        Delete a compute instance for an account.
        
                Args:
                    account_number: Account number
                    alias: Instance alias
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def get_action_details(self, action_status_id) -> Any:
        """
        Get details for a specific action using Kafka (with REST fallback).
        
                Args:
                    action_status_id: ID of the action status to fetch
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def get_all_instances_type(self) -> Any:
        """
        Get all instance types using Kafka (with REST fallback).
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def get_compute_details(self) -> Any:
        """
        Get compute instance details using Kafka (with REST fallback).
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def get_data_processing_image(self) -> Any:
        """
        Get data processing image name.
        
                Returns:
                    Full image name including repository and tag
        """
        ...

    def get_docker_hub_credentials(self) -> Any:
        """
        Get Docker Hub credentials using Kafka (with REST fallback).
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def get_downscaled_ids(self) -> Any:
        """
        Get IDs of downscaled instances using Kafka (with REST fallback).
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def get_internal_api_key(self, action_id) -> Any:
        """
        Get internal API key using Kafka (with REST fallback).
        
                Args:
                    action_id: ID of the action
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def get_kafka_bootstrap_servers(self) -> Any:
        """
        Get Kafka bootstrap servers from API and decode base64 fields.
        
                Returns:
                    str: Kafka bootstrap servers in format "ip:port"
        
                Raises:
                    ValueError: If unable to fetch Kafka configuration
        """
        ...

    def get_model_codebase(self, model_family_id) -> Any:
        """
        Get model codebase.
        
                Args:
                    model_family_id: ID of the model family
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def get_model_codebase_requirements(self, dockerId) -> Any:
        """
        Get model codebase requirements.
        
                Args:
                    dockerId: ID of the docker
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def get_model_codebase_script(self, model_family_id) -> Any:
        """
        Get model codebase script.
        
                Args:
                    model_family_id: ID of the model family
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def get_model_secret_keys(self, secret_name) -> Any:
        """
        Get model secret keys using Kafka (with REST fallback).
        
                Args:
                    secret_name: Name of the secret
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def get_open_port(self) -> Any:
        """
        Get an available open port.
        
                Returns:
                    Port number if available, None otherwise
        """
        ...

    def get_open_ports_config(self) -> Any:
        """
        Get open ports configuration using Kafka (with REST fallback).
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def get_shutdown_details(self) -> Any:
        """
        Get shutdown details for the instance using Kafka (with REST fallback).
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def get_tasks_details(self) -> Any:
        """
        Get task details for the instance using Kafka (with REST fallback).
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def get_user_access_key_pair(self, user_id) -> Any:
        """
        Get user access key pair using Kafka (with REST fallback).
        
                Args:
                    user_id: ID of the user
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def handle_response(self, resp, success_message, error_message) -> Any:
        """
        Helper function to handle API response.
        
                Args:
                    resp: Response from API call
                    success_message: Message to log on success
                    error_message: Message to log on error
        
                Returns:
                    Tuple of (data, error, message)
        """
        ...

    def refresh_presigned_url(self, url: str) -> Any:
        """
        Refresh a presigned URL that may have expired.
        
                Args:
                    url: The presigned URL to refresh
        
                Returns:
                    Tuple of (refreshed_url, error, message) from API response
        """
        ...

    def report_architecture_info(self) -> Any:
        """
        Collects and sends architecture info to the compute service.
        """
        ...

    def restart_account_compute(self, account_number, alias) -> Any:
        """
        Restart a compute instance for an account using Kafka (with REST fallback).
        
                Args:
                    account_number: Account number
                    alias: Instance alias
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def shutdown(self) -> Any:
        """
        Gracefully shutdown Kafka connections.
        """
        ...

    def stop_account_compute(self, account_number, alias) -> Any:
        """
        Stop a compute instance for an account using Kafka (with REST fallback).
        
                Args:
                    account_number: Account number
                    alias: Instance alias
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def stop_instance(self) -> Any:
        """
        Stop the compute instance using Kafka (with REST fallback).
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def update_action(self, id = '', step_code = '', action_type = '', status = '', sub_action = '', status_description = '', service = '', job_params = None) -> Any:
        """
        Update an action using Kafka (with REST fallback).
        
                Args:
                    id: Action ID
                    step_code: Step code
                    action_type: Type of action
                    status: Status of the action
                    sub_action: Sub-action details
                    status_description: Description of the status
                    service: Service name
                    job_params: Job parameters dictionary
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def update_action_container_id(self, action_record_id, container_id) -> Any:
        """
        Update container ID for an action using Kafka (with REST fallback).
        
                Args:
                    action_record_id: ID of the action record
                    container_id: Container ID to update
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def update_action_docker_logs(self, action_record_id, log_content) -> Any:
        """
        Update docker logs for an action using Kafka (with REST fallback).
        
                Args:
                    action_record_id: ID of the action record
                    log_content: Content of the logs to update
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def update_action_status(self, service_provider = '', action_record_id = '', isRunning = True, status = '', docker_start_time = None, action_duration = 0, cpuUtilisation = 0.0, gpuUtilisation = 0.0, memoryUtilisation = 0.0, gpuMemoryUsed = 0, createdAt = None, updatedAt = None) -> Any:
        """
        Update status of an action using Kafka (with REST fallback).
        
                Args:
                    service_provider: Provider of the service
                    action_record_id: ID of the action record
                    isRunning: Whether action is running
                    status: Status of the action
                    docker_start_time: Start time of docker container
                    action_duration: Duration of the action
                    cpuUtilisation: CPU utilization percentage
                    gpuUtilisation: GPU utilization percentage
                    memoryUtilisation: Memory utilization percentage
                    gpuMemoryUsed: GPU memory used
                    createdAt: Creation timestamp
                    updatedAt: Last update timestamp
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def update_available_resources(self, availableCPU = 0, availableGPU = 0, availableMemory = 0, availableGPUMemory = 0) -> Any:
        """
        Update available resources for the instance using Kafka (with REST fallback).
        
                Args:
                    availableCPU: Available CPU resources
                    availableGPU: Available GPU resources
                    availableMemory: Available memory
                    availableGPUMemory: Available GPU memory
        
                Returns:
                    Tuple of (data, error, message) from API response
        """
        ...

    def update_jupyter_token(self, token = '') -> Any:
        """
        Update Jupyter notebook token using Kafka (with REST fallback).
        """
        ...

    def update_status(self, action_record_id, action_type, service_name, stepCode, status, status_description) -> None:
        """
        Update status of an action using Kafka (with REST fallback).
        
                Args:
                    action_record_id: ID of the action record
                    action_type: Type of action
                    service_name: Name of the service
                    stepCode: Code indicating step in process
                    status: Status to update
                    status_description: Description of the status
        """
        ...


# From shutdown_manager
class ShutdownManager:
    """
    Class for managing compute instance shutdown.
    """

    def __init__(self, scaling) -> None:
        """
        Initialize ShutdownManager.
        
        Args:
            scaling (Scaling): Scaling instance to manage shutdown.
        """
        ...

    def do_cleanup_and_shutdown(self) -> bool:
        """
        Clean up resources and shut down the instance.
        
                This method attempts a coordinated shutdown with multiple fallback strategies:
                1. API call to notify the scaling service
                2. Graceful OS shutdown command
                3. Aggressive shutdown methods if needed
                4. Emergency forced shutdown as last resort
        
                Returns:
                    bool: True if shutdown was initiated successfully, False otherwise
        """
        ...

    def handle_shutdown(self, tasks_running: bool) -> None:
        """
        Check idle time and trigger shutdown if threshold is exceeded.
        
                Args:
                    tasks_running: Boolean indicating if there are running tasks
        """
        ...


from . import action_instance, actions_manager, actions_scaledown_manager, compute_operations_handler, instance_manager, instance_utils, k8s_scheduler, prechecks, resources_tracker, scaling, shutdown_manager, task_utils

def __getattr__(name: str) -> Any: ...