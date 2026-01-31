"""
Main client interface for Digilog.

This module provides the wandb-like interface for initializing runs,
logging metrics, and managing experiment tracking.
"""

import os
from typing import Any, Dict, Optional
from .api import APIClient
from .run import Run
from .config import config as global_config
from .exceptions import (
    AuthenticationError, ConfigurationError, ValidationError
)
from ._state import get_current_run, _current_run, _token, get_api_base_url, get_foom_config


def _sync_with_foom2(run: Run, project_name: str, foom_config: Optional[Dict[str, str]] = None) -> None:
    """
    Sync the digilog run with foom2 server if configured.
    
    This function creates a DigilogRun record in foom2 to link the digilog run
    to a thread for experiment tracking. This is completely optional and digilog
    will work normally without foom2.
    
    Args:
        run: The Run object that was just created
        project_name: The project name used in digilog.init()
        foom_config: Optional dict with foom2 configuration (server_url, api_key)
    """
    # Get foom2 configuration from env vars or provided config
    foom_server_url = os.environ.get("FOOM_SERVER_URL")
    foom_api_key = os.environ.get("FOOM_API_KEY")
    thread_id = os.environ.get("THREAD_ID")
    sweep_run_id = os.environ.get("SWEEP_RUN_ID")  # Optional sweep run link
    
    # Override with provided config if available
    if foom_config:
        foom_server_url = foom_config.get("server_url") or foom_server_url
        foom_api_key = foom_config.get("api_key") or foom_api_key
    
    # If no foom2 configuration, skip silently
    if not all([foom_server_url, foom_api_key, thread_id]):
        print("Foom2 not configured - running in standalone mode")
        return
    
    # Skip if digilog is in offline mode (no valid run_id)
    if not run.run_id:
        print("Skipping foom2 sync - digilog in offline mode")
        return
    
    try:
        import requests
        
        # Create DigilogRun record in foom2
        url = f"{foom_server_url.rstrip('/')}/api/digilog-runs"
        headers = {
            "X-API-Key": foom_api_key,
            "Content-Type": "application/json",
        }
        data = {
            "threadId": thread_id,
            "digilogRunId": run.run_id,
            "digilogProjectId": run.project_id,
            "digilogProjectName": project_name,
            "status": "RUNNING",
        }
        
        # Add sweep run link if available
        if sweep_run_id:
            data["sweepRunId"] = sweep_run_id
            print(f"Linking to sweep run {sweep_run_id}")
        
        print(f"Syncing digilog run {run.run_id} (project: {project_name}) with foom2 thread {thread_id}")
        response = requests.post(url, json=data, headers=headers, timeout=10.0)
        response.raise_for_status()
        print(f"✓ Synced digilog run {run.run_id} (project: {project_name}) with foom2 thread {thread_id}")
    
    except Exception as e:
        # Don't fail the run if sync fails - just log a warning
        print(f"Warning: Failed to sync with foom2 (continuing anyway): {e}")


def set_token(token: str) -> None:
    """
    Set the authentication token for API requests.
    
    Args:
        token: Authentication token
    """
    global _token
    _token = token


def init(
    project: str,
    name: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    group: Optional[str] = None,
    tags: Optional[list] = None,
    notes: Optional[str] = None,
    **kwargs
) -> Run:
    """
    Initialize a new experiment run.
    
    Args:
        project: Project name
        name: Run name (optional)
        config: Configuration parameters (optional)
        group: Group name for related runs (optional)
        tags: Tags for organization (optional, not yet implemented)
        notes: Description/notes (optional)
        **kwargs: Additional configuration parameters
        
    Returns:
        Run object for the new experiment
        
    Raises:
        AuthenticationError: If no valid token is provided
        ValidationError: If required parameters are invalid
    """
    global _current_run
    
    # Check if there's already an active run
    if _current_run is not None:
        raise ValidationError("A run is already active. Call finish() first.")
    
    # Validate required parameters
    if not project or not isinstance(project, str):
        raise ValidationError("Project name is required and must be a string")
    
    # Get authentication token
    token = _token or os.environ.get('DIGILOG_API_KEY')
    if not token:
        raise AuthenticationError(
            "No authentication token found. Set DIGILOG_API_KEY environment variable "
            "or call set_token()"
        )
    
    # Log environment variable status
    print("Digilog initialization - checking environment variables:")
    print(f"  ✓ DIGILOG_API_KEY: {'set' if token else 'NOT SET'}")
    
    # Check optional foom2 integration variables
    foom_server_url = os.environ.get("FOOM_SERVER_URL")
    foom_api_key = os.environ.get("FOOM_API_KEY")
    thread_id = os.environ.get("THREAD_ID")
    sweep_id = os.environ.get("SWEEP_ID")
    sweep_run_id = os.environ.get("SWEEP_RUN_ID")
    
    if all([foom_server_url, foom_api_key, thread_id]):
        print("  ✓ Foom2 integration: ENABLED (FOOM_SERVER_URL, FOOM_API_KEY, THREAD_ID all set)")
        if sweep_id:
            print(f"  ✓ Sweep mode: ENABLED (SWEEP_ID={sweep_id})")
    else:
        print("  ℹ Foom2 integration: DISABLED (optional)")
        missing_vars = []
        if not foom_server_url:
            missing_vars.append("FOOM_SERVER_URL")
        if not foom_api_key:
            missing_vars.append("FOOM_API_KEY")
        if not thread_id:
            missing_vars.append("THREAD_ID")
        print(f"    Missing: {', '.join(missing_vars)}")
        print("    Note: Foom2 integration is optional and provides thread-based experiment tracking")
    
    # Auto-set group from SWEEP_ID if not explicitly provided
    if group is None and sweep_id:
        group = sweep_id
        print(f"  ℹ Auto-setting group to SWEEP_ID: {sweep_id}")
    
    # Create API client
    api_client = APIClient(get_api_base_url(), token)
    
    # Merge config from kwargs
    if config is None:
        config_dict = {}
    else:
        config_dict = config.copy()
    if kwargs:
        config_dict.update(kwargs)
    
    # Try to create project and run - gracefully handle failures
    project_data = None
    run_data = None
    offline_mode = False
    
    try:
        # Create or get project
        try:
            project_data = api_client.create_project(project, notes)
        except Exception:
            projects = api_client.get_projects()
            project_data = next((p for p in projects if p['name'] == project), None)
        
        if project_data:
            run_data = api_client.create_run(
                project_id=project_data['id'],
                name=name,
                description=notes,
                group_id=group
            )
    except Exception as e:
        print(f"⚠ Digilog server unavailable, running in offline mode: {e}")
        offline_mode = True
    
    # Create Run object (works in offline mode too)
    _current_run = Run(
        api_client=api_client,
        run_id=run_data['id'] if run_data else None,
        project_id=project_data['id'] if project_data else None,
        name=name,
        description=notes,
        group_id=group,
        config=config_dict,
        offline_mode=offline_mode,
        _project_name=project  # Store for retry at finish
    )
    
    # Sync with foom2 if configured
    try:
        foom_config = get_foom_config()
        _sync_with_foom2(_current_run, project, foom_config if foom_config else None)
    except Exception as e:
        print(f"Warning: Failed to sync with foom2 (continuing anyway): {e}")
    
    # Update global config
    global_config.update(config_dict)
    global_config.freeze()
    
    return _current_run


def log(data: Dict[str, Any], step: Optional[int] = None) -> None:
    """
    Log metrics and other data to the current run.
    
    Args:
        data: Dictionary of metrics to log
        step: Step number (optional)
        
    Raises:
        ValidationError: If no active run or invalid data
    """
    run = get_current_run()
    if run is None:
        raise ValidationError("No active run. Call init() first.")
    
    run.log(data, step)


def finish() -> None:
    """
    Finish the current run.
    
    Raises:
        ValidationError: If no active run
    """
    global _current_run
    
    if _current_run is None:
        raise ValidationError("No active run to finish.")
    
    _current_run.finish()
    _current_run = None
    
    # Unfreeze global config
    global_config.unfreeze()


# Convenience functions for direct access to current run
def log_metric(key: str, value: Any, step: Optional[int] = None) -> None:
    """Log a single metric to the current run."""
    run = get_current_run()
    if run is None:
        raise ValidationError("No active run. Call init() first.")
    
    if isinstance(value, (int, float)):
        run.log_metric(key, value, step)
    else:
        run.log_config(key, value)


def log_config(key: str, value: Any) -> None:
    """Log a configuration parameter to the current run."""
    run = get_current_run()
    if run is None:
        raise ValidationError("No active run. Call init() first.")
    
    run.log_config(key, value)


def log_configs(configs: Dict[str, Any]) -> None:
    """Log multiple configuration parameters to the current run."""
    run = get_current_run()
    if run is None:
        raise ValidationError("No active run. Call init() first.")
    
    run.log_configs(configs)


def log_image(
    image: Any,
    name: str,
    step: Optional[int] = None,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> None:
    """
    Log an image to the current run.
    
    Supports PIL Images, numpy arrays, file paths, and matplotlib figures.
    
    Args:
        image: Image object (PIL.Image, numpy array, file path, or matplotlib figure)
        name: Name/key for the image
        step: Optional step number
        title: Optional title (defaults to name)
        description: Optional description
        
    Example:
        >>> import digilog
        >>> import numpy as np
        >>> 
        >>> digilog.init(project="vision-project")
        >>> 
        >>> # Log a numpy array
        >>> array = np.random.rand(100, 100, 3)
        >>> digilog.log_image(array, "random_pattern", step=1)
    """
    run = get_current_run()
    if run is None:
        raise ValidationError("No active run. Call init() first.")
    
    run.log_image(image, name, step, title, description)


# Context manager support
class run:
    """
    Context manager for automatic run management.
    
    Usage:
        with digilog.run(project="my-project") as run:
            run.log({"loss": 0.1})
    """
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._run = None
    
    def __enter__(self):
        self._run = init(**self.kwargs)
        return self._run
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._run:
            status = "FAILED" if exc_type else "FINISHED"
            self._run.finish(status) 