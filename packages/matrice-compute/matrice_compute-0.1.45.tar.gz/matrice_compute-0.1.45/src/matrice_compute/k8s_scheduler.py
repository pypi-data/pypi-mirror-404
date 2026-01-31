"""
Kubernetes Scheduler for bg-job-scheduler

This module runs inside a Kubernetes cluster and:
1. Authenticates with Matrice API using access key and secret key (via matrice_common.session)
2. Polls for assigned actions using /v1/actions/assign_jobs_kubernetes/{cluster_id}
3. Creates K8s Jobs for each action using in-cluster authentication
4. Monitors job status and updates action records via existing action update API
5. Sends heartbeat to report cluster health

The K8s scheduler flow:
1. Register a cluster in compute_clusters with isKubernetes: true
2. When user submits a job with clusterName, processClusterName in be-action:
   - Detects the cluster is K8s (isKubernetes: true)
   - Sets kubernetesClusterId and executionMode: "kubernetes" in actionDetails
3. K8s scheduler polls /v1/actions/assign_jobs_kubernetes/{cluster_id}
4. Scheduler creates K8s Jobs for each action

"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from matrice_common.session import Session

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger("k8s_scheduler")
logger.setLevel(logging.INFO)


# Action type to script mapping (matches VM mode's action_instance.py)
ACTION_SCRIPTS: Dict[str, str] = {
    "model_train": "python3 train.py",
    "model_eval": "python3 eval.py",
    "model_export": "python3 export.py",
    "deploy_add": "python3 deploy.py",
    "data_import": "python3 /usr/src/app/main.py",
    "data_add": "python3 /usr/src/app/main.py",
    "data_split": "python3 /usr/src/app/data_split.py",
    "data_prep": "python3 /usr/src/app/data_preparation.py",
    "dataset_annotation": "python3 /usr/src/app/dataset_annotation.py",
    "dataset_augmentation": "python3 /usr/src/app/data_augmentation.py",
    "dataset_generation": "python3 /usr/src/app/synthetic_dataset_generation.py",
    "image_build": "python3 main.py",
    "resource_clone": "python3 main.py",
    "streaming_gateway": "python3 /usr/src/app/streaming_gateway.py",
    "deploy_aggregator": "python3 /usr/src/app/deploy_aggregator.py",
}

# Extra packages needed per action type
ACTION_EXTRA_PACKAGES: Dict[str, List[str]] = {
    "data_import": ["matrice_dataset"],
    "data_add": ["matrice_dataset"],
    "data_split": ["matrice_dataset"],
    "data_prep": ["matrice_dataset"],
    "dataset_annotation": ["matrice_dataset"],
    "dataset_augmentation": ["matrice_dataset"],
    "dataset_generation": ["matrice_dataset"],
    "deploy_add": ["matrice_inference", "matrice_analytics"],
    "streaming_gateway": ["matrice_streaming"],
}


class K8sScheduler:
    """
    Kubernetes Scheduler that polls for actions and creates K8s Jobs.
    Runs inside the cluster using in-cluster authentication.
    """

    # Action type to script mapping (matches VM mode's action_instance.py)
    # Constants moved to module level: ACTION_SCRIPTS and ACTION_EXTRA_PACKAGES

    # Running jobs keyed by action_id
    running_jobs: Dict[str, str]

    def __init__(self):
        # Configuration from environment
        self.cluster_id = os.environ.get("CLUSTER_ID")
        self.job_namespace = os.environ.get("JOB_NAMESPACE", "matrice-jobs")
        self.poll_interval = int(os.environ.get("POLL_INTERVAL", "10"))
        self.env = os.environ.get("ENV", "prod")

        # GPU configuration - whether this cluster has GPU nodes
        is_gpu_str = os.environ.get("IS_GPU", "false").lower()
        self.is_gpu = is_gpu_str in ("true", "1", "yes")

        # Validate required config
        if not self.cluster_id:
            raise ValueError("CLUSTER_ID environment variable is required")

        # Matrice credentials (for API authentication and action execution)
        self.matrice_access_key = os.environ.get("MATRICE_ACCESS_KEY_ID")
        self.matrice_secret_key = os.environ.get("MATRICE_SECRET_ACCESS_KEY")

        if not self.matrice_access_key or not self.matrice_secret_key:
            raise ValueError("MATRICE_ACCESS_KEY_ID and MATRICE_SECRET_ACCESS_KEY environment variables are required")

        # Initialize Matrice session for API authentication
        self.session = Session(
            account_number="",
            access_key=self.matrice_access_key,
            secret_key=self.matrice_secret_key,
        )
        self.rpc = self.session.rpc

        # Initialize Kubernetes client (in-cluster auth)
        self._init_k8s_client()

        # Track running jobs
        self.running_jobs = {}  # action_id -> job_name

        # Scheduler start time
        self.start_time = datetime.now()

        # Ensure Docker Hub image pull secret exists
        self._ensure_docker_hub_secret()

        logger.info(f"K8s Scheduler initialized for cluster {self.cluster_id}")
        logger.info(f"Job namespace: {self.job_namespace}")
        logger.info(f"Poll interval: {self.poll_interval}s")
        logger.info(f"GPU mode: {self.is_gpu}")
        logger.info(f"Matrice session initialized with access key: {self.matrice_access_key[:8]}...")

    def _init_k8s_client(self):
        """Initialize Kubernetes client using in-cluster config"""
        try:
            # Try in-cluster config first (when running inside K8s)
            config.load_incluster_config()
            logger.info("Using in-cluster Kubernetes configuration")
        except config.ConfigException:
            # Fall back to kubeconfig for local development
            try:
                config.load_kube_config()
                logger.info("Using kubeconfig for Kubernetes configuration")
            except config.ConfigException as e:
                logger.error(f"Failed to configure Kubernetes client: {e}")
                raise

        self.batch_v1 = client.BatchV1Api()
        self.core_v1 = client.CoreV1Api()

    def _ensure_docker_hub_secret(self):
        """
        Fetch Docker Hub credentials from be-compute API and create/update
        the image pull secret in the job namespace.

        Uses the same public API endpoint as VM mode: /v1/compute/get_docker_hub_credentials
        """
        try:
            # Fetch Docker Hub credentials from be-compute API
            # Use the same public endpoint as VM mode
            path = "/v1/compute/get_docker_hub_credentials"

            response = self.rpc.get(path=path)

            if not response or not response.get("success"):
                logger.warning("Failed to fetch Docker Hub credentials from API, jobs may fail to pull private images")
                return

            creds = response.get("data", {})
            username = creds.get("username")
            password = creds.get("password")

            if not username or not password:
                logger.warning("Docker Hub credentials incomplete, jobs may fail to pull private images")
                return

            # Create docker-registry secret in job namespace
            import base64
            import json

            # Create docker config JSON
            docker_config = {
                "auths": {
                    "https://index.docker.io/v1/": {
                        "username": username,
                        "password": password,
                        "auth": base64.b64encode(f"{username}:{password}".encode()).decode()
                    }
                }
            }

            docker_config_json = json.dumps(docker_config)

            # Create secret object
            secret = client.V1Secret(
                api_version="v1",
                kind="Secret",
                metadata=client.V1ObjectMeta(
                    name="matrice-registry",
                    namespace=self.job_namespace
                ),
                type="kubernetes.io/dockerconfigjson",
                data={
                    ".dockerconfigjson": base64.b64encode(docker_config_json.encode()).decode()
                }
            )

            # Try to create or update the secret
            try:
                self.core_v1.create_namespaced_secret(self.job_namespace, secret)
                logger.info(f"Created Docker Hub secret 'matrice-registry' in namespace {self.job_namespace}")
            except ApiException as e:
                if e.status == 409:  # Already exists
                    # Update existing secret
                    self.core_v1.replace_namespaced_secret("matrice-registry", self.job_namespace, secret)
                    logger.info(f"Updated Docker Hub secret 'matrice-registry' in namespace {self.job_namespace}")
                else:
                    raise

        except Exception as e:
            logger.error(f"Error creating Docker Hub secret: {e}")
            logger.warning("Jobs requiring private Docker images may fail to start")

    def _get_startup_command(self, action_type: str, action_id: str) -> List[str]:
        """
        Build the startup command for the container.

        This mirrors VM mode's get_base_docker_cmd() logic:
        1. Install matrice SDK packages
        2. Run the appropriate script for the action type

        Args:
            action_type: The type of action (model_train, data_import, etc.)
            action_id: The action record ID

        Returns:
            List of command arguments for the container
        """
        # Determine PyPI index based on environment
        pypi_index = (
            "https://test.pypi.org/simple/"
            if self.env in ["dev", "staging"]
            else "https://pypi.org/simple/"
        )

        # Base packages
        packages = ["matrice_common", "matrice"]

        # Add extra packages for specific action types
        extra_pkgs = ACTION_EXTRA_PACKAGES.get(action_type, [])
        packages.extend(extra_pkgs)

        # Build pip install command
        if self.env == "dev":
            packages = [f"{pkg}>=1.0.0" for pkg in packages]
            pip_cmd = f"pip install --pre --upgrade --force-reinstall --index-url {pypi_index} {' '.join(packages)}"
        else:
            pip_cmd = f"pip install --upgrade --force-reinstall --index-url {pypi_index} {' '.join(packages)}"

        # Get the script for this action type
        script = ACTION_SCRIPTS.get(action_type, "python3 main.py")

        # Build full command
        # Format: pip install SDK && run script with action_id
        full_command = f"{pip_cmd} && {script} {action_id}"

        # Use /bin/bash to match VM mode behavior
        return ["/bin/bash", "-c", full_command]

    def poll_pending_actions(self) -> List[Dict[str, Any]]:
        """
        Poll for actions assigned to this Kubernetes cluster.

        Uses the new K8s-specific endpoint:
        - processClusterName in be-action detects K8s clusters and sets kubernetesClusterId
        - Scheduler calls /v1/actions/assign_jobs_kubernetes/{cluster_id} to fetch assigned actions
        """
        try:
            # Use the K8s-specific endpoint
            path = f"/v1/actions/assign_jobs_kubernetes/{self.cluster_id}"
            response = self.rpc.get(path=path)

            if response and response.get("success"):
                actions = response.get("data", [])
                if actions:
                    logger.info(f"Found {len(actions)} assigned actions for cluster {self.cluster_id}")
                return actions if actions else []
            else:
                error_msg = response.get("message", "Unknown error") if response else "No response"
                logger.warning(f"Failed to poll actions: {error_msg}")
                return []

        except Exception as e:
            logger.error(f"Error polling for pending actions: {e}")
            return []

    def update_action_status(self, action_id: str, step_code: str, status: str,
                            description: str, extra_details: Optional[Dict] = None):
        """
        Update action status using the existing action update endpoint.

        Uses the standard action record update API that accepts:
        - stepCode: The step code for the action
        - status: Status (OK, ERROR, etc.)
        - statusDescription: Human-readable description

        Extra details are merged into the action record's actionDetails.
        """
        try:
            # Use RPC client for authenticated API calls
            path = "/v1/actions"
            payload: Dict[str, Any] = {
                "_id": action_id,
                "stepCode": step_code,
                "status": status,
                "statusDescription": description,
            }

            # Merge extra details into actionDetails
            if extra_details:
                payload["actionDetails"] = extra_details

            response = self.rpc.put(path=path, payload=payload)

            if response and response.get("success"):
                logger.debug(f"Updated action {action_id}: stepCode={step_code}, status={status}")
            else:
                error_msg = response.get("message", "Unknown error") if response else "No response"
                logger.warning(f"Failed to update action {action_id}: {error_msg}")

        except Exception as e:
            logger.error(f"Error updating action status: {e}")

    def create_k8s_job(self, action: Dict[str, Any]) -> Optional[str]:
        """Create a Kubernetes Job for the given action"""
        action_id = action.get("_id", action.get("id", ""))
        action_details = action.get("actionDetails", {})
        action_type = action.get("action", "unknown")

        # Get service ID for job naming
        service_id = action_details.get("serviceId", action_id)

        # Generate job name
        job_name = f"action-{action_type}-{service_id[:8]}".lower().replace("_", "-")

        # Get configuration from action details
        docker_image = action_details.get("docker")
        if not docker_image:
            logger.error(f"No docker image specified for action {action_id}")
            self.update_action_status(
                action_id, "ERROR", "ERROR",
                "No docker image specified for action"
            )
            return None

        namespace = action_details.get("kubernetesNamespace", self.job_namespace)
        cpu_request = action_details.get("cpuRequest", "500m")
        memory_request = action_details.get("memoryRequest", "512Mi")
        cpu_limit = action_details.get("cpuLimit", "2000m")
        memory_limit = action_details.get("memoryLimit", "4Gi")
        gpu_required = action_details.get("gpuRequired", False)
        gpu_count = action_details.get("gpuCount", 1)
        gpu_resource_key = action_details.get("gpuResourceKey", "nvidia.com/gpu")
        gpu_memory_limit = action_details.get("gpuMemoryLimit", "")
        gpu_node_selector = action_details.get("gpuNodeSelector", "")
        registry_secret = action_details.get("registrySecret", "matrice-registry")

        # Build environment variables
        env_vars = [
            client.V1EnvVar(name="ENV", value=self.env),
            client.V1EnvVar(name="ACTION_ID", value=action_id),
            client.V1EnvVar(name="EXECUTION_MODE", value="kubernetes"),
            client.V1EnvVar(name="KUBERNETES_CLUSTER_ID", value=self.cluster_id),
        ]

        # Add Matrice credentials if available
        if self.matrice_access_key:
            env_vars.append(client.V1EnvVar(name="MATRICE_ACCESS_KEY_ID", value=self.matrice_access_key))
        if self.matrice_secret_key:
            env_vars.append(client.V1EnvVar(name="MATRICE_SECRET_ACCESS_KEY", value=self.matrice_secret_key))

        # Add custom env vars from action
        custom_env = action_details.get("envVars", {})
        for key, value in custom_env.items():
            env_vars.append(client.V1EnvVar(name=key, value=str(value)))

        # Build resource requirements
        resources = client.V1ResourceRequirements(
            requests={
                "cpu": cpu_request,
                "memory": memory_request,
            },
            limits={
                "cpu": cpu_limit,
                "memory": memory_limit,
            }
        )

        # Add GPU resources if required
        if gpu_required:
            resources.requests[gpu_resource_key] = str(gpu_count)
            resources.limits[gpu_resource_key] = str(gpu_count)
            if gpu_memory_limit:
                resources.limits["nvidia.com/gpu-memory"] = gpu_memory_limit

        # Build container with args only (don't override command/entrypoint from Dockerfile)
        # The action images have their own ENTRYPOINT (e.g., "./main" for Go images)
        # and expect the service_id as an argument
        container = client.V1Container(
            name="action-worker",
            image=docker_image,
            image_pull_policy="Always",
            args=[service_id],  # Pass service_id as argument to the container entrypoint
            env=env_vars,
            resources=resources,
        )

        # Build pod spec
        pod_spec = client.V1PodSpec(
            restart_policy="Never",
            containers=[container],
            # Add tolerations for control-plane taint (common in single-node clusters)
            tolerations=[
                client.V1Toleration(
                    key="node-role.kubernetes.io/control-plane",
                    operator="Exists",
                    effect="NoSchedule"
                )
            ]
        )

        # Add image pull secret if specified
        if registry_secret:
            pod_spec.image_pull_secrets = [
                client.V1LocalObjectReference(name=registry_secret)
            ]

        # Add node selector for GPU
        if gpu_required and gpu_node_selector:
            pod_spec.node_selector = {gpu_node_selector: "true"}

        # Build job spec
        job_spec = client.V1JobSpec(
            backoff_limit=2,
            ttl_seconds_after_finished=3600,  # Clean up after 1 hour
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={
                        "app": "matrice-action",
                        "action-id": action_id,
                        "action-type": action_type,
                    }
                ),
                spec=pod_spec,
            ),
        )

        # Build job
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(
                name=job_name,
                namespace=namespace,
                labels={
                    "app": "matrice-action",
                    "action-id": action_id,
                    "action-type": action_type,
                    "managed-by": "matrice-scheduler",
                }
            ),
            spec=job_spec,
        )

        # Ensure namespace exists
        self._ensure_namespace(namespace)

        # Create the job
        try:
            self.batch_v1.create_namespaced_job(namespace=namespace, body=job)
            logger.info(f"Created K8s job {job_name} for action {action_id}")

            # Update action status
            self.update_action_status(
                action_id,
                "K8S_JOB_CREATED",
                "OK",
                f"Kubernetes job {job_name} created",
                {
                    "kubernetesJobName": job_name,
                    "kubernetesNamespace": namespace,
                    "jobCreatedAt": datetime.now().isoformat(),
                }
            )

            # Track the job
            self.running_jobs[action_id] = job_name

            return job_name

        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.warning(f"Job {job_name} already exists")
                self.running_jobs[action_id] = job_name
                return job_name
            else:
                logger.error(f"Failed to create K8s job: {e}")
                self.update_action_status(
                    action_id, "ERROR", "ERROR",
                    f"Failed to create Kubernetes job: {e.reason}"
                )
                return None

    def _ensure_namespace(self, namespace: str):
        """Ensure the namespace exists"""
        try:
            self.core_v1.read_namespace(namespace)
        except ApiException as e:
            if e.status == 404:
                # Create namespace
                ns = client.V1Namespace(
                    metadata=client.V1ObjectMeta(
                        name=namespace,
                        labels={"managed-by": "matrice-scheduler"}
                    )
                )
                try:
                    self.core_v1.create_namespace(ns)
                    logger.info(f"Created namespace {namespace}")
                except ApiException as create_err:
                    if create_err.status != 409:  # Not already exists
                        raise

    def check_job_status(self, action_id: str, job_name: str, namespace: str) -> Optional[str]:
        """Check the status of a K8s job and return status if completed. Also monitors resource usage."""
        try:
            job = self.batch_v1.read_namespaced_job(job_name, namespace)

            # Get pod info for detailed logging and resource monitoring
            pod_selector = f"job-name={job_name}"
            pods = self.core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=pod_selector
            )

            # Log detailed status
            if pods.items:
                pod = pods.items[0]
                pod_name = pod.metadata.name
                pod_phase = pod.status.phase

                logger.info(
                    f"Job status - Action: {action_id}, Job: {job_name}, "
                    f"Pod: {pod_name}, Phase: {pod_phase}, "
                    f"Active: {job.status.active}, Succeeded: {job.status.succeeded}, Failed: {job.status.failed}"
                )

                # Get pod resource usage metrics if available
                try:
                    resource_info = self._get_pod_resource_usage(namespace, pod_name)
                    if resource_info:
                        logger.info(f"Resource usage for {pod_name}: {resource_info}")

                        # Update action with resource info
                        self.update_action_status(
                            action_id,
                            "K8S_JOB_RUNNING",
                            "OK",
                            f"Job running - Pod: {pod_name}, Phase: {pod_phase}",
                            {
                                "podName": pod_name,
                                "podPhase": pod_phase,
                                "resourceUsage": resource_info
                            }
                        )
                except Exception as e:
                    logger.debug(f"Could not fetch resource metrics: {e}")

            if job.status.succeeded:
                return "COMPLETED"
            elif job.status.failed:
                return "FAILED"
            elif job.status.active:
                return "RUNNING"
            else:
                return "PENDING"

        except ApiException as e:
            if e.status == 404:
                return "NOT_FOUND"
            logger.error(f"Error checking job status for {job_name}: {e}")
            return None

    def _get_pod_resource_usage(self, namespace: str, pod_name: str) -> Optional[Dict[str, Dict[str, str]]]:
        """Get current resource usage for a pod"""
        try:
            # Read pod to get resource requests/limits
            pod = self.core_v1.read_namespaced_pod(pod_name, namespace)

            resource_info: Dict[str, Dict[str, str]] = {
                "requests": {},
                "limits": {}
            }

            for container in pod.spec.containers:
                if container.resources:
                    if container.resources.requests:
                        resource_info["requests"] = {
                            "cpu": str(container.resources.requests.get("cpu", "unknown") if isinstance(container.resources.requests, dict) else "unknown"),
                            "memory": str(container.resources.requests.get("memory", "unknown") if isinstance(container.resources.requests, dict) else "unknown"),
                            "gpu": str(container.resources.requests.get("nvidia.com/gpu", "0") if isinstance(container.resources.requests, dict) else "0")
                        }
                    if container.resources.limits:
                        resource_info["limits"] = {
                            "cpu": str(container.resources.limits.get("cpu", "unknown") if isinstance(container.resources.limits, dict) else "unknown"),
                            "memory": str(container.resources.limits.get("memory", "unknown") if isinstance(container.resources.limits, dict) else "unknown"),
                            "gpu": str(container.resources.limits.get("nvidia.com/gpu", "0") if isinstance(container.resources.limits, dict) else "0"),
                            "gpuMemory": str(container.resources.limits.get("nvidia.com/gpu-memory", "") if isinstance(container.resources.limits, dict) else "")
                        }

            return resource_info
        except Exception as e:
            logger.debug(f"Error getting pod resource usage: {e}")
            return None

    def monitor_running_jobs(self):
        """Monitor running jobs and update action statuses"""
        for action_id, job_name in list(self.running_jobs.items()):
            namespace = self.job_namespace
            status = self.check_job_status(action_id, job_name, namespace)

            if status == "COMPLETED":
                logger.info(f"Job {job_name} completed successfully")
                self.update_action_status(
                    action_id, "COMPLETED", "OK",
                    "Kubernetes job completed successfully"
                )
                del self.running_jobs[action_id]

            elif status == "FAILED":
                logger.warning(f"Job {job_name} failed")
                self.update_action_status(
                    action_id, "ERROR", "ERROR",
                    "Kubernetes job failed"
                )
                del self.running_jobs[action_id]

            elif status == "NOT_FOUND":
                logger.warning(f"Job {job_name} not found, removing from tracking")
                del self.running_jobs[action_id]

    def send_heartbeat(self):
        """Send heartbeat to Matrice API with cluster health info"""
        try:
            # Get cluster health info
            nodes_ready = 0
            nodes_total = 0
            gpus_available = 0
            gpus_total = 0

            try:
                nodes = self.core_v1.list_node()
                for node in nodes.items:
                    nodes_total += 1
                    for condition in node.status.conditions:
                        if condition.type == "Ready" and condition.status == "True":
                            nodes_ready += 1

                    # Check for GPU resources
                    allocatable = node.status.allocatable or {}
                    for key, value in allocatable.items():
                        if "gpu" in key.lower():
                            gpus_total += int(value)
            except Exception as e:
                logger.warning(f"Error getting node info: {e}")

            # Get job counts
            running_jobs = 0
            pending_jobs = 0
            try:
                jobs = self.batch_v1.list_namespaced_job(self.job_namespace)
                for job in jobs.items:
                    if job.status.active:
                        running_jobs += 1
                    elif not job.status.succeeded and not job.status.failed:
                        pending_jobs += 1
            except Exception as e:
                logger.warning(f"Error getting job info: {e}")

            # Send heartbeat - for now just log the status
            # TODO: Add K8s cluster heartbeat endpoint if needed
            logger.debug(f"Cluster {self.cluster_id} status: nodes={nodes_ready}/{nodes_total}, "
                        f"gpus={gpus_available}/{gpus_total}, jobs={running_jobs} running, {pending_jobs} pending")

        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")

    def start(self):
        """Main scheduler loop - matches InstanceManager.start() pattern"""
        logger.info(f"Starting K8s Scheduler for cluster {self.cluster_id}")

        heartbeat_counter = 0
        heartbeat_interval = 6  # Send heartbeat every 6 poll cycles (60s if poll_interval=10)

        while True:
            try:
                # Poll for pending actions
                logger.info(f"Polling for pending actions for cluster {self.cluster_id} (Running jobs: {len(self.running_jobs)})")
                pending_actions = self.poll_pending_actions()

                if pending_actions:
                    logger.info(f"Found {len(pending_actions)} pending action(s)")

                # Create jobs for pending actions
                for action in pending_actions:
                    action_id = action.get("_id", action.get("id", ""))
                    action_type = action.get("action", "unknown")
                    if action_id not in self.running_jobs:
                        logger.info(f"Creating job for action {action_id} (type: {action_type})")
                        self.create_k8s_job(action)
                    else:
                        logger.debug(f"Skipping action {action_id} - already running")

                # Monitor running jobs
                if self.running_jobs:
                    logger.info(f"Monitoring {len(self.running_jobs)} running job(s)")
                self.monitor_running_jobs()

                # Send heartbeat periodically
                heartbeat_counter += 1
                if heartbeat_counter >= heartbeat_interval:
                    logger.info("Sending heartbeat to Matrice API")
                    self.send_heartbeat()
                    heartbeat_counter = 0

                # Log summary
                logger.info(f"Cycle complete - Running: {len(self.running_jobs)}, Pending: {len(pending_actions)}")

                # Wait before next poll
                time.sleep(self.poll_interval)

            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                time.sleep(self.poll_interval)
