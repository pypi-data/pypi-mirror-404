"""
Dataset download utilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import requests
from tqdm import tqdm

from terso.config import get_api_key, get_base_url, get_dataset_path, list_datasets

if TYPE_CHECKING:
    pass


def download_dataset(
    name: str,
    output_dir: str | Path | None = None,
    *,
    api_key: str | None = None,
    split: str | None = None,
) -> Path:
    """
    Download a dataset.
    
    Args:
        name: Dataset name (e.g., "kitchen-v1")
        output_dir: Where to save the dataset (default: ~/.terso/datasets/<name>)
        api_key: API key for authentication (uses saved key if not provided)
        split: Optional split to download ("train", "val", "test", or None for all)
        
    Returns:
        Path to downloaded dataset
        
    Example:
        from terso.download import download_dataset
        path = download_dataset("kitchen-v1")
    """
    if output_dir is None:
        output_dir = get_dataset_path(name)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get download URL (requires API key)
    api_key = api_key or get_api_key()
    if not api_key:
        raise ValueError(
            "API key required. Get one at https://terso.ai "
            "and run: terso auth <your-key>"
        )
    
    headers = {"x-api-key": api_key}
    params = {}
    if split:
        params["split"] = split
    
    base_url = get_base_url()
    response = requests.get(
        f"{base_url}/datasets/{name}/files",
        headers=headers,
        params=params,
        timeout=30,
    )
    
    if response.status_code == 401:
        raise ValueError(
            "Invalid API key. Get a new one at https://terso.ai "
            "and run: terso auth <your-key>"
        )
    
    if response.status_code == 403:
        raise ValueError(
            "You don't have access to this dataset. "
            "Contact hello@terso.ai for access."
        )
    
    if response.status_code == 404:
        # Try to list available datasets for better error message
        try:
            datasets = list_datasets()
            available = list(datasets.keys())
            raise ValueError(f"Dataset '{name}' not found. Available: {available}")
        except Exception:
            raise ValueError(f"Dataset '{name}' not found")
    
    response.raise_for_status()
    download_info = response.json()
    
    # Download
    download_url = download_info["url"]
    filename = download_info.get("filename", f"{name}.tar.gz")
    file_path = output_dir / filename
    
    print(f"Downloading {name}...")
    _download_file(download_url, file_path)
    
    # Extract
    if filename.endswith((".tar.gz", ".tgz")):
        import tarfile
        print("Extracting...")
        with tarfile.open(file_path, "r:gz") as tar:
            tar.extractall(output_dir)
        file_path.unlink()
    elif filename.endswith(".zip"):
        import zipfile
        print("Extracting...")
        with zipfile.ZipFile(file_path, "r") as zf:
            zf.extractall(output_dir)
        file_path.unlink()
    
    print(f"Dataset ready: {output_dir}")
    return output_dir


def _download_file(url: str, output_path: Path) -> None:
    """Download file with progress bar."""
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    
    total_size = int(response.headers.get("content-length", 0))
    
    with open(output_path, "wb") as f:
        with tqdm(total=total_size, unit="B", unit_scale=True, desc=output_path.name) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))
