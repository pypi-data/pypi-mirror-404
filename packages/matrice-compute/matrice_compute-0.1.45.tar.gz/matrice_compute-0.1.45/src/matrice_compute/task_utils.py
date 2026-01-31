"""Module providing task_utils functionality."""

import logging
import os
import shutil
import urllib.request
import zipfile
from typing import Optional
from matrice_common.utils import log_errors
from matrice_compute.scaling import Scaling


@log_errors(raise_exception=False, log_error=True, default_return=None)
def refresh_url_if_needed(url: Optional[str], scaling: Optional[Scaling] = None) -> Optional[str]:
    """Refresh a presigned URL if it appears to be expired or about to expire.
    
    This function attempts to refresh presigned URLs for model codebase and requirements
    to ensure they are valid before downloading.
    
    Args:
        url: The URL to potentially refresh. If None or empty, returns None.
        scaling: The Scaling instance to use for API calls. If None, returns original URL.
        
    Returns:
        The refreshed URL if successful, or the original URL if refresh fails or is not needed.
    """
    if not url:
        return None
    
    if not scaling:
        logging.warning("No scaling instance provided, returning original URL")
        return url
    
    logging.info("Attempting to refresh presigned URL")
    try:
        refreshed_url, error, message = scaling.refresh_presigned_url(url)
        if error:
            logging.warning(f"Failed to refresh presigned URL: {message}. Using original URL.")
            return url
        if refreshed_url:
            logging.info("Successfully refreshed presigned URL")
            return refreshed_url
        else:
            logging.warning("Refresh returned empty URL, using original URL")
            return url
    except Exception as e:
        logging.warning(f"Exception while refreshing presigned URL: {e}. Using original URL.")
        return url


@log_errors(raise_exception=True, log_error=True)
def setup_workspace_and_run_task(
    work_fs: str,
    action_id: str,
    model_codebase_url: str,
    model_codebase_requirements_url: Optional[str] = None,
    scaling: Optional[Scaling] = None,
) -> None:
    """Set up workspace and run task with provided parameters.

    Args:
        work_fs (str): Working filesystem path.
        action_id (str): Unique identifier for the action.
        model_codebase_url (str): URL to download model codebase from.
        model_codebase_requirements_url (Optional[str]): URL to download requirements from. Defaults to None.
        scaling (Optional[Scaling]): Scaling instance for refreshing presigned URLs. Defaults to None.

    Returns:
        None
    """
    workspace_dir = f"{work_fs}/{action_id}"
    codebase_zip_path = f"{workspace_dir}/file.zip"
    requirements_txt_path = f"{workspace_dir}/requirements.txt"
    # if os.path.exists(workspace_dir): # don't skip if workspace already exists, override it
    #     return
    os.makedirs(workspace_dir, exist_ok=True)
    
    # Refresh presigned URLs before downloading to ensure they are valid
    refreshed_codebase_url = refresh_url_if_needed(model_codebase_url, scaling)
    if refreshed_codebase_url:
        model_codebase_url = refreshed_codebase_url
    
    # Download codebase ZIP file
    urllib.request.urlretrieve(model_codebase_url, codebase_zip_path)
    
    # Extract ZIP file with overwrite
    with zipfile.ZipFile(codebase_zip_path, 'r') as zip_ref:
        zip_ref.extractall(workspace_dir)
    
    # Move files from subdirectories to workspace root (equivalent to rsync -av)
    for root, dirs, files in os.walk(workspace_dir):
        # Skip the workspace_dir itself to avoid moving files to themselves
        if root == workspace_dir:
            continue
        
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(workspace_dir, file)
            
            # If destination file exists, overwrite it (equivalent to rsync -av behavior)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            
            shutil.move(src_file, dst_file)
        
        # Remove empty directories after moving files
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            if os.path.exists(dir_path) and not os.listdir(dir_path):
                os.rmdir(dir_path)
    
    # Clean up any remaining empty subdirectories
    for root, dirs, files in os.walk(workspace_dir, topdown=False):
        if root == workspace_dir:
            continue
        if not files and not dirs:
            try:
                os.rmdir(root)
            except OSError:
                pass  # Directory might not be empty or might not exist
    
    # Download requirements.txt if URL is provided
    if model_codebase_requirements_url:
        # Refresh presigned URL for requirements before downloading
        refreshed_requirements_url = refresh_url_if_needed(model_codebase_requirements_url, scaling)
        if refreshed_requirements_url:
            model_codebase_requirements_url = refreshed_requirements_url
        urllib.request.urlretrieve(model_codebase_requirements_url, requirements_txt_path)