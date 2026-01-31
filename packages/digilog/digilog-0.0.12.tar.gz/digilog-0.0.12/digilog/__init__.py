"""
Digilog Python Client

A Python client for Digilog experiment tracking with a wandb-like interface.
"""

from .client import init, log, finish, set_token
from .run import Run
from .config import Config
from .exceptions import DigilogError
from ._state import get_current_run, set_api_base_url, get_api_base_url, set_foom_config
from .api import get_effective_api_url

__version__ = "0.0.10"
__all__ = ["init", "log", "finish", "set_token", "set_foom_config", "Run", "Config", "DigilogError"]
