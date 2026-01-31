#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["terso"]
# [tool.uv.sources]
# terso = { path = ".." }
# ///
"""
Example: Load and iterate over a Terso dataset.

Usage:
    uv run examples/load_dataset.py ./path/to/dataset

    # Or with a published dataset name:
    uv run examples/load_dataset.py kitchen-v1
"""

import sys
import numpy as np
from terso import load_dataset, iter_clips


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run examples/load_dataset.py <dataset_path_or_name>")
        print("\nExample:")
        print("  uv run examples/load_dataset.py ./my_exported_dataset")
        sys.exit(1)

    dataset_path = sys.argv[1]
    print(f"Loading dataset: {dataset_path}")

    # Load dataset
    ds = load_dataset(dataset_path)

    # Print basic stats
    clip_ids = set(row["clip_id"] for row in ds)
    print(f"\nDataset loaded:")
    print(f"  Total frames: {len(ds)}")
    print(f"  Total clips: {len(clip_ids)}")

    # Reload for iteration (HF datasets are consumed after iteration)
    ds = load_dataset(dataset_path)

    # Show first few frames
    print("\nFirst 3 frames:")
    for i, row in enumerate(ds):
        if i >= 3:
            break
        print(f"  [{i}] clip={row['clip_id']}, frame={row['frame_idx']}, task={row['task']}")
        if row.get("hand_poses"):
            hp = np.array(row["hand_poses"]).reshape(2, 21, 3)
            print(f"       hand_poses shape: {hp.shape}")

    # Iterate by clip
    ds = load_dataset(dataset_path)
    print("\nClips:")
    for i, clip in enumerate(iter_clips(ds)):
        print(f"  {clip['clip_id']}: {clip['num_frames']} frames, task={clip['task']}")
        if clip.get("hand_poses") is not None:
            print(f"    hand_poses: {clip['hand_poses'].shape}")
        if clip.get("actions") is not None:
            print(f"    actions: {clip['actions'].shape}")
        if i >= 4:
            print("  ...")
            break

    print("\nDone!")


if __name__ == "__main__":
    main()
