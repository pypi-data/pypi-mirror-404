"""Module providing __init__ functionality."""

import os
import subprocess
import logging

from matrice_common.utils import dependencies_check

# Check execution mode to determine which dependencies to verify
execution_mode = os.environ.get("EXECUTION_MODE", "vm").lower()

if execution_mode == "kubernetes":
    # Kubernetes mode - only check K8s-related dependencies
    dependencies_check(
        ["kubernetes", "psutil", "cryptography"]
    )
else:
    # VM mode - check docker and other VM-specific dependencies
    dependencies_check(
        ["docker", "psutil", "cryptography", "notebook", "aiohttp", "kafka-python"]
    )

    subprocess.run( # Re-upgrade docker to avoid missing DOCKER_HOST connection error
        ["pip", "install", "--upgrade", "docker"],
        check=True,
        stdout=subprocess.DEVNULL,   # suppress normal output
        stderr=subprocess.DEVNULL    # suppress warnings/progress
    )

from matrice_compute.instance_manager import InstanceManager  # noqa: E402

logging.getLogger("kafka").setLevel(logging.INFO)
logging.getLogger("confluent_kafka").setLevel(logging.INFO)

__all__ = ["InstanceManager"]