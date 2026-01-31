"""
Dataset classes for loading Terso manipulation data.

Uses HuggingFace datasets format (parquet files).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Optional

import numpy as np


def _parse_json_field(value):
    """Parse JSON field, handling already-parsed dicts/lists."""
    if value is None:
        return {}
    if isinstance(value, (dict, list)):
        return value
    return json.loads(value)


def load_dataset(
    name_or_path: str,
    split: str = "train",
    task: Optional[str] = None,
    streaming: bool = False,
):
    """
    Load a Terso dataset in HuggingFace format.

    Args:
        name_or_path: Dataset name (e.g., "kitchen-v1") or local path
        split: Which split to load ("train", "val", "test")
        task: Optional task filter
        streaming: If True, stream data instead of loading into memory

    Returns:
        HuggingFace Dataset object

    Example:
        from terso.datasets import load_dataset

        # Load from local path
        ds = load_dataset("./my_dataset")
        for row in ds:
            hand_poses = np.array(row["hand_poses"]).reshape(2, 21, 3)
            print(row["clip_id"], hand_poses.shape)

        # Filter by task
        ds = load_dataset("./my_dataset", task="pour_latte")

        # Stream large datasets
        ds = load_dataset("./my_dataset", streaming=True)
    """
    try:
        from datasets import load_dataset as hf_load_dataset
    except ImportError:
        raise ImportError(
            "HuggingFace datasets required. Install with: pip install datasets"
        )

    path = Path(name_or_path)

    # If not a local path, download first
    if not path.exists():
        from terso.download import download_dataset
        from terso.config import get_dataset_path

        local_path = get_dataset_path(name_or_path)
        # Check if directory has data files, not just if it exists
        has_data = local_path.exists() and any(local_path.glob("*.parquet"))
        if not has_data:
            download_dataset(name_or_path, local_path)
        path = local_path

    # Load with HuggingFace
    ds = hf_load_dataset(str(path), split=split, streaming=streaming)

    # Filter by task if specified
    if task:
        ds = ds.filter(lambda x: x["task"] == task)

    return ds


def iter_clips(dataset) -> Iterator[dict]:
    """
    Iterate over a dataset grouped by clip.

    Yields dicts with clip-level data:
        - clip_id: str
        - task: str
        - num_frames: int
        - hand_poses: np.ndarray (T, 2, 21, 3)
        - actions: np.ndarray (T,)
        - objects: list[dict]

    Example:
        ds = load_dataset("./my_dataset")
        for clip in iter_clips(ds):
            print(clip["clip_id"], clip["hand_poses"].shape)
    """
    # Group frames by clip_id
    clips: dict[str, list] = {}
    for row in dataset:
        clip_id = row["clip_id"]
        if clip_id not in clips:
            clips[clip_id] = []
        clips[clip_id].append(row)

    # Yield assembled clips
    for clip_id, frames in clips.items():
        frames = sorted(frames, key=lambda x: x["frame_idx"])

        clip = {
            "clip_id": clip_id,
            "task": frames[0].get("task"),
            "num_frames": len(frames),
            "video_url": frames[0].get("video_url"),
        }

        # Stack hand poses: (T, 126) -> (T, 2, 21, 3)
        if frames[0].get("hand_poses"):
            hp = np.array([f["hand_poses"] for f in frames])
            clip["hand_poses"] = hp.reshape(-1, 2, 21, 3)

        # Stack actions
        if frames[0].get("action") is not None:
            clip["actions"] = np.array([f["action"] for f in frames])

        # Parse objects JSON
        if frames[0].get("objects"):
            clip["objects"] = [_parse_json_field(f.get("objects")) for f in frames]

        # Parse IMU JSON
        if frames[0].get("imu"):
            clip["imu"] = [_parse_json_field(f.get("imu")) for f in frames]

        yield clip


def get_clip(dataset, clip_id: str) -> dict:
    """
    Get a single clip by ID.

    Args:
        dataset: HuggingFace dataset
        clip_id: Clip identifier

    Returns:
        Dict with clip data

    Example:
        ds = load_dataset("./my_dataset")
        clip = get_clip(ds, "abc123")
        print(clip["hand_poses"].shape)
    """
    frames = [row for row in dataset if row["clip_id"] == clip_id]
    if not frames:
        raise KeyError(f"Clip not found: {clip_id}")

    frames = sorted(frames, key=lambda x: x["frame_idx"])

    clip = {
        "clip_id": clip_id,
        "task": frames[0].get("task"),
        "num_frames": len(frames),
        "video_url": frames[0].get("video_url"),
    }

    if frames[0].get("hand_poses"):
        hp = np.array([f["hand_poses"] for f in frames])
        clip["hand_poses"] = hp.reshape(-1, 2, 21, 3)

    if frames[0].get("action") is not None:
        clip["actions"] = np.array([f["action"] for f in frames])

    if frames[0].get("objects"):
        clip["objects"] = [_parse_json_field(f.get("objects")) for f in frames]

    return clip


def to_torch_dataloader(
    dataset,
    batch_size: int = 32,
    shuffle: bool = True,
):
    """
    Convert to PyTorch DataLoader for frame-level training.

    Args:
        dataset: HuggingFace dataset
        batch_size: Batch size
        shuffle: Whether to shuffle

    Returns:
        PyTorch DataLoader

    Example:
        ds = load_dataset("./my_dataset")
        loader = to_torch_dataloader(ds, batch_size=64)
        for batch in loader:
            hand_poses = batch["hand_poses"]  # (B, 2, 21, 3)
    """
    try:
        import torch
        from torch.utils.data import DataLoader
    except ImportError:
        raise ImportError("PyTorch required. Install with: pip install torch")

    class FrameDataset(torch.utils.data.Dataset):
        def __init__(self, hf_dataset):
            self.data = list(hf_dataset)

        def __len__(self):
            return len(self.data)

        def __getitem__(self, idx):
            row = self.data[idx]
            item = {
                "clip_id": row["clip_id"],
                "frame_idx": row["frame_idx"],
                "task": row["task"],
            }
            if row.get("hand_poses"):
                hp = np.array(row["hand_poses"]).reshape(2, 21, 3)
                item["hand_poses"] = torch.from_numpy(hp).float()
            if row.get("action") is not None:
                item["action"] = row["action"]
            return item

    torch_ds = FrameDataset(dataset)
    return DataLoader(torch_ds, batch_size=batch_size, shuffle=shuffle)
