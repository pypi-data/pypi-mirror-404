"""
Terso - Egocentric manipulation video datasets for physical AI.

Install with full dependencies for local dataset loading:
    pip install terso[full]

Basic usage (API only):
    from terso import Client
    
    client = Client(api_key="your-key")
    client.upload("video.mp4", task="pour_latte")

Full usage (with datasets):
    from terso import load_dataset
    
    dataset = load_dataset("kitchen-v1")
    for sample in dataset:
        print(sample.hand_poses.shape)
"""

__version__ = "0.3.0"
__all__ = [
    # Core
    "Client",
    "upload",
    "download",
    "bulk_upload",
    "cancel_upload",
    "export",
    "ExportResult",
    # Datasets
    "load_dataset",
    "iter_clips",
    "get_clip",
    "list_datasets",
    # Config
    "set_api_key",
    "get_api_key",
]

from terso.client import (
    Client,
    ExportResult,
    upload,
    download,
    bulk_upload,
    cancel_upload,
    export,
)
from terso.config import set_api_key, get_api_key, list_datasets
from terso.datasets import load_dataset, iter_clips, get_clip
