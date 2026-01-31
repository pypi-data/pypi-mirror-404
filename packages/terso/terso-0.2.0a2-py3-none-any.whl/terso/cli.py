"""
Terso command-line interface.

Usage:
    terso upload video.mp4 --task pour_latte
    terso status <clip_id>
    terso download <clip_id> ./output
    terso list
    terso auth <api_key>
"""

from __future__ import annotations

import argparse
import json
import sys
import time


def main():
    parser = argparse.ArgumentParser(
        prog="terso",
        description="Terso CLI - Egocentric manipulation video datasets for physical AI",
    )
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show version",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # upload
    upload_p = subparsers.add_parser("upload", help="Upload video(s) for processing")
    upload_p.add_argument("videos", nargs="+", help="Path(s) to video file(s)")
    upload_p.add_argument("--task", "-t", help="Task type (e.g., pour_latte)")
    upload_p.add_argument("--source", help="Source identifier for attribution")
    upload_p.add_argument("--partner", "-p", help="(Deprecated) Use --source instead")
    upload_p.add_argument("--wait", "-w", action="store_true", help="Wait for processing")
    upload_p.add_argument("--direct", "-d", action="store_true", help="Force direct R2 upload")
    upload_p.add_argument("--server", "-s", help="API server URL")

    # cancel
    cancel_p = subparsers.add_parser("cancel", help="Cancel an in-progress upload")
    cancel_p.add_argument("clip_id", help="Clip ID to cancel")
    cancel_p.add_argument("--server", "-s", help="API server URL")
    
    # status
    status_p = subparsers.add_parser("status", help="Check clip processing status")
    status_p.add_argument("clip_id", help="Clip ID")
    status_p.add_argument("--watch", "-w", action="store_true", help="Watch until complete")
    status_p.add_argument("--server", "-s", help="API server URL")
    
    # download
    download_p = subparsers.add_parser("download", help="Download a processed clip")
    download_p.add_argument("clip_id", help="Clip ID")
    download_p.add_argument("output", nargs="?", default=".", help="Output directory")
    download_p.add_argument("--server", "-s", help="API server URL")
    
    # list
    list_p = subparsers.add_parser("list", help="List clips")
    list_p.add_argument("--task", "-t", help="Filter by task")
    list_p.add_argument("--status", help="Filter by status")
    list_p.add_argument("--limit", "-n", type=int, default=20, help="Max results")
    list_p.add_argument("--server", "-s", help="API server URL")
    
    # export
    export_p = subparsers.add_parser("export", help="Export clips as a dataset")
    export_p.add_argument("--task", "-t", help="Export clips for this task")
    export_p.add_argument("--clips", "-c", nargs="+", help="Export specific clip IDs")
    export_p.add_argument("--output", "-o", help="Output directory (auto-download)")
    export_p.add_argument("--no-video", action="store_true", help="Exclude video frames")
    export_p.add_argument("--no-depth", action="store_true", help="Exclude depth maps")
    export_p.add_argument("--no-hand-poses", action="store_true", help="Exclude hand poses")
    export_p.add_argument("--no-actions", action="store_true", help="Exclude actions")
    export_p.add_argument("--no-objects", action="store_true", help="Exclude objects")
    export_p.add_argument("--no-extract", action="store_true", help="Keep as ZIP, don't extract")
    export_p.add_argument("--server", "-s", help="API server URL")

    # datasets
    datasets_p = subparsers.add_parser("datasets", help="List available datasets")
    
    # auth
    auth_p = subparsers.add_parser("auth", help="Set API key")
    auth_p.add_argument("api_key", help="Your API key from terso.ai")
    
    # whoami
    subparsers.add_parser("whoami", help="Show current API key status")
    
    args = parser.parse_args()
    
    if args.version:
        from terso import __version__
        print(f"terso {__version__}")
        return
    
    if args.command is None:
        parser.print_help()
        return
    
    try:
        if args.command == "upload":
            cmd_upload(args)
        elif args.command == "cancel":
            cmd_cancel(args)
        elif args.command == "status":
            cmd_status(args)
        elif args.command == "download":
            cmd_download(args)
        elif args.command == "export":
            cmd_export(args)
        elif args.command == "list":
            cmd_list(args)
        elif args.command == "datasets":
            cmd_datasets(args)
        elif args.command == "auth":
            cmd_auth(args)
        elif args.command == "whoami":
            cmd_whoami(args)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_upload(args):
    """Upload video(s)."""
    from terso.client import Client

    client = Client(base_url=args.server) if args.server else Client()

    # Map partner to source for backward compatibility
    source = args.source or args.partner

    if len(args.videos) == 1:
        # Single file upload
        video = args.videos[0]
        print(f"Uploading {video}...")

        if args.direct:
            clip = client.upload_direct(
                video,
                task=args.task,
                source=source,
                wait=args.wait,
            )
        else:
            clip = client.upload(
                video,
                task=args.task,
                source=source,
                wait=args.wait,
            )

        print(json.dumps(clip, indent=2, default=str))

        if not args.wait and clip["status"] not in ("ready", "rejected"):
            print(f"\nTrack progress: terso status {clip['id']} --watch")
    else:
        # Bulk upload
        print(f"Uploading {len(args.videos)} files...")

        result = client.bulk_upload(
            args.videos,
            task=args.task,
            source=source,
            wait=args.wait,
        )

        print(f"\nUploaded: {len(result['clips'])} clips")
        if result["failed"]:
            print(f"Failed: {len(result['failed'])} files")
            for f in result["failed"]:
                print(f"  - {f.get('path', f.get('clipId'))}: {f['error']}")

        for clip in result["clips"]:
            print(f"  {clip['id']}: {clip.get('originalName', 'unknown')}")


def cmd_cancel(args):
    """Cancel an upload."""
    from terso.client import Client

    client = Client(base_url=args.server) if args.server else Client()

    if client.cancel_upload(args.clip_id):
        print(f"Cancelled upload: {args.clip_id}")
    else:
        print(f"Failed to cancel: {args.clip_id}")


def cmd_status(args):
    """Check clip status."""
    from terso.client import Client
    
    client = Client(base_url=args.server) if args.server else Client()
    
    if args.watch:
        print(f"Watching clip {args.clip_id}...")
        clip = client.wait(args.clip_id, timeout=3600)
    else:
        clip = client.get(args.clip_id)
    
    print(json.dumps(clip, indent=2, default=str))
    
    if clip["status"] == "rejected":
        errors = clip.get("validation", {}).get("errors", [])
        if errors:
            print(f"\nRejected: {', '.join(errors)}")


def cmd_download(args):
    """Download a clip."""
    from terso.client import Client

    client = Client(base_url=args.server) if args.server else Client()

    path = client.download(args.clip_id, args.output)
    print(f"Downloaded to: {path}")


def cmd_export(args):
    """Export clips as a dataset."""
    from terso.client import Client

    client = Client(base_url=args.server) if args.server else Client()

    if not args.task and not args.clips:
        print("Error: Must specify --task or --clips", file=sys.stderr)
        sys.exit(1)

    result = client.export(
        task=args.task,
        clip_ids=args.clips,
        include_video=not args.no_video,
        include_depth=not args.no_depth,
        include_hand_poses=not args.no_hand_poses,
        include_actions=not args.no_actions,
        include_objects=not args.no_objects,
        output_path=args.output,
        extract=not args.no_extract,
    )

    print(f"Export complete:")
    print(f"  Clips: {result.total_clips}")
    print(f"  Frames: {result.total_frames}")
    print(f"  Expires: {result.expires_at}")

    if result.local_path:
        print(f"  Downloaded to: {result.local_path}")
    else:
        print(f"  Download URL: {result.download_url}")


def cmd_list(args):
    """List clips."""
    from terso.client import Client
    
    client = Client(base_url=args.server) if args.server else Client()
    
    result = client.list(
        task=args.task,
        status=args.status,
        limit=args.limit,
    )
    
    clips = result.get("clips", [])
    total = result.get("total", len(clips))
    
    if not clips:
        print("No clips found.")
        return
    
    print(f"Showing {len(clips)} of {total} clips:\n")
    
    for clip in clips:
        status_icon = {
            "ready": "✓",
            "rejected": "✗",
            "processing": "◐",
            "validating": "◐",
            "pending": "○",
        }.get(clip["status"], "?")
        
        print(f"  {status_icon} {clip['id'][:8]}  {clip.get('originalName', 'unknown'):<30}  {clip['status']}")


def cmd_datasets(args):
    """List available datasets."""
    from terso.config import list_datasets
    
    datasets = list_datasets()
    
    print("Available Datasets:\n")
    
    for name, info in datasets.items():
        status = info.get("status", "available")
        status_str = "(coming soon)" if status == "coming_soon" else ""
        
        print(f"  {name} {status_str}")
        print(f"    {info.get('description', '')}")
        
        if info.get("tasks"):
            print(f"    Tasks: {', '.join(info['tasks'])}")
        print()


def cmd_auth(args):
    """Set API key."""
    from terso.config import set_api_key
    
    set_api_key(args.api_key)
    print("API key saved. You can now upload and download clips.")


def cmd_whoami(args):
    """Show API key status."""
    from terso.config import get_api_key, get_base_url
    
    api_key = get_api_key()
    base_url = get_base_url()
    
    print(f"API URL: {base_url}")
    
    if api_key:
        # Mask the key
        masked = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "****"
        print(f"API Key: {masked}")
    else:
        print("API Key: Not set")
        print("\nSet your API key with: terso auth <your-key>")


if __name__ == "__main__":
    main()
