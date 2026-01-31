"""Basic example: loading and iterating over a dataset."""

from terso import load_dataset, set_api_key

set_api_key("your-api-key")
ds = load_dataset("test")
for clip in ds:
    print(clip["clip_id"])
