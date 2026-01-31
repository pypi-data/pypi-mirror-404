"""
Terso configuration management.
"""

from __future__ import annotations

import json
import mimetypes
import os
from pathlib import Path
from typing import Any

# Default API endpoint
DEFAULT_BASE_URL = "https://backend-production-5251.up.railway.app"

# Upload constants
MULTIPART_THRESHOLD = 100 * 1024 * 1024  # 100MB - use multipart for files >= this size
CHUNK_SIZE = 100 * 1024 * 1024           # 100MB per part
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB max file size
MAX_BULK_FILES = 50                       # Max files in a bulk upload
ALLOWED_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}

# MIME types for video files
CONTENT_TYPES = {
    '.mp4': 'video/mp4',
    '.mov': 'video/quicktime',
    '.avi': 'video/x-msvideo',
    '.mkv': 'video/x-matroska',
    '.webm': 'video/webm',
}


def get_content_type(extension: str) -> str:
    """Get MIME type for a file extension."""
    ext = extension.lower()
    return CONTENT_TYPES.get(ext, 'application/octet-stream')

# Config directory
CONFIG_DIR = Path.home() / ".terso"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_config() -> dict[str, Any]:
    """Load config from file."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(config: dict[str, Any]) -> None:
    """Save config to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_api_key() -> str | None:
    """
    Get API key from environment or config.
    
    Checks in order:
        1. TERSO_API_KEY environment variable
        2. ~/.terso/config.json
    """
    # Environment variable takes precedence
    api_key = os.environ.get("TERSO_API_KEY")
    if api_key:
        return api_key
    
    # Fall back to config file
    config = get_config()
    return config.get("api_key")


def set_api_key(api_key: str) -> None:
    """
    Save API key to config file.
    
    Args:
        api_key: Your API key from terso.ai
    """
    config = get_config()
    config["api_key"] = api_key
    save_config(config)
    print(f"API key saved to {CONFIG_FILE}")


def get_base_url() -> str:
    """Get API base URL."""
    return os.environ.get("TERSO_API_URL", DEFAULT_BASE_URL)


def get_dataset_path(name: str) -> Path:
    """Get local path for a dataset."""
    return CONFIG_DIR / "datasets" / name


def list_datasets() -> dict[str, dict]:
    """
    List available datasets.
    
    Returns:
        Dict of dataset name -> metadata
        
    Example:
        from terso import list_datasets
        for name, info in list_datasets().items():
            print(f"{name}: {info['description']}")
    """
    import requests
    
    try:
        response = requests.get(
            f"{get_base_url()}/datasets",
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list):
            return {d["name"]: d for d in data}
        return data
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch datasets: {e}") from e
