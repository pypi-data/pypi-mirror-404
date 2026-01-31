"""
Terso API client.
"""

from __future__ import annotations

import os
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Callable

import requests
from tqdm import tqdm

from terso.config import (
    get_api_key,
    get_base_url,
    get_content_type,
    MULTIPART_THRESHOLD,
    CHUNK_SIZE,
    MAX_FILE_SIZE,
    MAX_BULK_FILES,
    ALLOWED_EXTENSIONS,
)


@dataclass
class ExportResult:
    """Result from an export operation."""
    download_url: str
    total_clips: int
    total_frames: int
    export_key: str
    expires_at: str
    local_path: Path | None = None


class TersoError(Exception):
    """Base exception for Terso errors."""
    pass


class AuthenticationError(TersoError):
    """Raised when API key is invalid or missing."""
    pass


class NotFoundError(TersoError):
    """Raised when a resource is not found."""
    pass


class Client:
    """
    Client for the Terso API.
    
    Usage:
        client = Client(api_key="your-key")
        
        # Upload a video
        clip = client.upload("video.mp4", task="pour_latte")
        print(f"Clip ID: {clip['id']}")
        
        # Wait for processing
        clip = client.wait(clip["id"])
        
        # Download results
        client.download(clip["id"], "output/")
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize the Terso client.
        
        Args:
            api_key: Your API key. If not provided, reads from TERSO_API_KEY
                    environment variable or ~/.terso/config.json
            base_url: API base URL. Defaults to https://api.terso.ai
        """
        self.api_key = api_key or get_api_key()
        self.base_url = (base_url or get_base_url()).rstrip("/")
        
        self._session = requests.Session()
        if self.api_key:
            self._session.headers["x-api-key"] = self.api_key
    
    def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> requests.Response:
        """Make an API request."""
        url = f"{self.base_url}{path}"
        response = self._session.request(method, url, **kwargs)
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid or missing API key")
        if response.status_code == 404:
            raise NotFoundError(f"Not found: {path}")
        
        response.raise_for_status()
        return response
    
    def upload(
        self,
        video_path: str | Path,
        *,
        task: str | None = None,
        partner_id: str | None = None,
        source: str | None = None,
        wait: bool = False,
        timeout: int = 600,
    ) -> dict[str, Any]:
        """
        Upload a video for processing. Auto-detects large files (>=100MB)
        and uses direct R2 upload for better performance.

        Args:
            video_path: Path to video file (mp4, mov, avi, mkv, webm)
            task: Task type (e.g., "pour_latte", "pick_object")
            partner_id: Deprecated, use source instead
            source: Source identifier for attribution
            wait: If True, wait for processing to complete
            timeout: Timeout in seconds when waiting

        Returns:
            Clip metadata dict with id, status, etc.

        Example:
            clip = client.upload("demo.mp4", task="pour", wait=True)
            print(clip["status"])  # "ready"
        """
        video_path = Path(video_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        # Map partner_id to source for backward compatibility
        source = source or partner_id

        file_size = video_path.stat().st_size

        # Use direct upload for large files
        if file_size >= MULTIPART_THRESHOLD:
            return self.upload_direct(
                video_path,
                task=task,
                source=source,
                wait=wait,
                timeout=timeout,
            )

        # Standard upload for small files
        with open(video_path, "rb") as f:
            files = {"file": (video_path.name, f, "video/mp4")}
            data = {}
            if task:
                data["task"] = task
            if source:
                data["source"] = source

            response = self._request(
                "POST",
                "/clips/upload",
                files=files,
                data=data,
            )

        result = response.json()

        if wait:
            result = self.wait(result["id"], timeout=timeout)

        return result
    
    def wait(
        self,
        clip_id: str,
        timeout: int = 600,
        poll_interval: int = 2,
    ) -> dict[str, Any]:
        """
        Wait for clip processing to complete.
        
        Args:
            clip_id: Clip ID from upload
            timeout: Maximum time to wait in seconds
            poll_interval: How often to check status
            
        Returns:
            Final clip metadata
        """
        start = time.time()
        
        with tqdm(total=100, desc="Processing", unit="%", leave=False) as pbar:
            last_progress = 0
            
            while time.time() - start < timeout:
                clip = self.get(clip_id)
                status = clip["status"]
                
                # Map status to progress
                progress_map = {
                    "pending": 5,
                    "validating": 20,
                    "processing": 50,
                    "ready": 100,
                    "rejected": 100,
                }
                progress = progress_map.get(status, 0)
                
                # Use detailed progress if available
                if clip.get("progress"):
                    progress = clip["progress"].get("percent", progress)
                
                pbar.update(progress - last_progress)
                last_progress = progress
                
                if status in ("ready", "rejected"):
                    break
                
                time.sleep(poll_interval)
            else:
                raise TimeoutError(f"Processing timed out after {timeout}s")
        
        return clip
    
    def get(self, clip_id: str) -> dict[str, Any]:
        """
        Get clip metadata.
        
        Args:
            clip_id: Clip ID
            
        Returns:
            Clip metadata dict
        """
        response = self._request("GET", f"/clips/{clip_id}")
        return response.json()
    
    def status(self, clip_id: str) -> dict[str, Any]:
        """
        Get clip processing status.
        
        Args:
            clip_id: Clip ID
            
        Returns:
            Status dict with status and progress
        """
        response = self._request("GET", f"/clips/{clip_id}/status")
        return response.json()
    
    def list(
        self,
        *,
        task: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List clips.
        
        Args:
            task: Filter by task type
            status: Filter by status (pending, processing, ready, rejected)
            limit: Max results to return
            offset: Pagination offset
            
        Returns:
            Dict with "clips" list and "total" count
        """
        params = {"limit": limit, "offset": offset}
        if task:
            params["task"] = task
        if status:
            params["status"] = status
        
        response = self._request("GET", "/clips", params=params)
        return response.json()
    
    def download(
        self,
        clip_id: str,
        output_dir: str | Path,
        *,
        extract: bool = True,
    ) -> Path:
        """
        Download a processed clip with annotations.
        
        Args:
            clip_id: Clip ID
            output_dir: Directory to save to
            extract: Whether to extract the zip archive
            
        Returns:
            Path to downloaded clip directory
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        response = self._request(
            "GET",
            f"/clips/{clip_id}/download",
            stream=True,
        )
        
        archive_path = output_dir / f"{clip_id}.zip"
        total_size = int(response.headers.get("content-length", 0))
        
        with open(archive_path, "wb") as f:
            with tqdm(total=total_size, unit="B", unit_scale=True, desc="Downloading") as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        if extract:
            import zipfile
            
            clip_dir = output_dir / clip_id
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(clip_dir)
            
            archive_path.unlink()
            return clip_dir
        
        return archive_path
    
    def annotation(
        self,
        clip_id: str,
        annotation_type: str,
    ) -> Any:
        """
        Get a specific annotation.
        
        Args:
            clip_id: Clip ID
            annotation_type: One of: hand_poses, actions, depth_maps, objects, metadata
            
        Returns:
            Annotation data (format depends on type)
        """
        response = self._request("GET", f"/clips/{clip_id}/annotations/{annotation_type}")
        return response.json()
    
    def delete(self, clip_id: str) -> bool:
        """
        Delete a clip.
        
        Args:
            clip_id: Clip ID
            
        Returns:
            True if deleted
        """
        self._request("DELETE", f"/clips/{clip_id}")
        return True
    
    def retry(self, clip_id: str) -> dict[str, Any]:
        """
        Retry processing a failed clip.

        Args:
            clip_id: Clip ID of a rejected clip

        Returns:
            Updated clip metadata
        """
        response = self._request("POST", f"/clips/{clip_id}/retry")
        return response.json()

    # -------------------------------------------------------------------------
    # Direct Upload (R2) Methods
    # -------------------------------------------------------------------------

    def _init_upload(
        self,
        file_name: str,
        file_size: int,
        content_type: str,
        task: str | None,
        source: str | None,
    ) -> dict[str, Any]:
        """Initialize a direct upload, returns upload URLs."""
        payload = {
            "fileName": file_name,
            "fileSize": file_size,
            "contentType": content_type,
        }
        if task:
            payload["task"] = task
        if source:
            payload["source"] = source

        response = self._request("POST", "/clips/upload/init", json=payload)
        return response.json()

    def _upload_part(
        self,
        upload_url: str,
        data: bytes,
        part_number: int,
        content_type: str,
    ) -> str:
        """Upload a single part to presigned URL, returns ETag."""
        response = requests.put(
            upload_url,
            data=data,
            headers={"Content-Type": content_type},
        )
        response.raise_for_status()
        return response.headers.get("ETag", "").strip('"')

    def _confirm_upload(self, clip_id: str) -> dict[str, Any]:
        """Confirm a simple direct upload is complete."""
        response = self._request("POST", f"/clips/{clip_id}/confirm")
        return response.json()

    def _complete_multipart(
        self,
        clip_id: str,
        parts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Complete a multipart upload with part ETags."""
        response = self._request(
            "POST",
            f"/clips/{clip_id}/complete",
            json={"parts": parts},
        )
        return response.json()

    def upload_direct(
        self,
        video_path: str | Path,
        *,
        task: str | None = None,
        source: str | None = None,
        wait: bool = False,
        timeout: int = 600,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """
        Upload a video directly to R2 storage. Auto-detects whether to use
        simple or multipart upload based on file size.

        Args:
            video_path: Path to video file
            task: Task type (e.g., "pour_latte")
            source: Source identifier for attribution
            wait: If True, wait for processing to complete
            timeout: Timeout in seconds when waiting
            on_progress: Optional callback(bytes_uploaded, total_bytes)

        Returns:
            Clip metadata dict with id, status, etc.
        """
        video_path = Path(video_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        ext = video_path.suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {ext}. "
                f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        file_size = video_path.stat().st_size

        if file_size > MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {file_size / (1024**3):.1f}GB. "
                f"Maximum: {MAX_FILE_SIZE / (1024**3):.0f}GB"
            )

        content_type = get_content_type(ext)

        # Initialize upload
        init_result = self._init_upload(
            file_name=video_path.name,
            file_size=file_size,
            content_type=content_type,
            task=task,
            source=source,
        )

        clip_id = init_result["clipId"]

        if file_size >= MULTIPART_THRESHOLD:
            # Multipart upload for large files
            result = self._do_multipart_upload(
                video_path=video_path,
                clip_id=clip_id,
                upload_id=init_result["uploadId"],
                part_urls=init_result["partUrls"],
                content_type=content_type,
                file_size=file_size,
                on_progress=on_progress,
            )
        else:
            # Simple single-part upload
            result = self._do_simple_upload(
                video_path=video_path,
                clip_id=clip_id,
                upload_url=init_result["uploadUrl"],
                content_type=content_type,
                file_size=file_size,
                on_progress=on_progress,
            )

        if wait:
            result = self.wait(clip_id, timeout=timeout)

        return result

    def _do_simple_upload(
        self,
        video_path: Path,
        clip_id: str,
        upload_url: str,
        content_type: str,
        file_size: int,
        on_progress: Callable[[int, int], None] | None,
    ) -> dict[str, Any]:
        """Perform a simple single-part upload."""
        with open(video_path, "rb") as f:
            data = f.read()

        with tqdm(total=file_size, unit="B", unit_scale=True, desc="Uploading") as pbar:
            response = requests.put(
                upload_url,
                data=data,
                headers={"Content-Type": content_type},
            )
            response.raise_for_status()
            pbar.update(file_size)
            if on_progress:
                on_progress(file_size, file_size)

        return self._confirm_upload(clip_id)

    def _do_multipart_upload(
        self,
        video_path: Path,
        clip_id: str,
        upload_id: str,
        part_urls: list[str],
        content_type: str,
        file_size: int,
        on_progress: Callable[[int, int], None] | None,
    ) -> dict[str, Any]:
        """Perform a multipart upload for large files."""
        parts = []
        uploaded_bytes = 0

        with open(video_path, "rb") as f:
            with tqdm(total=file_size, unit="B", unit_scale=True, desc="Uploading") as pbar:
                for part_number, upload_url in enumerate(part_urls, start=1):
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break

                    etag = self._upload_part(upload_url, chunk, part_number, content_type)
                    parts.append({"partNumber": part_number, "etag": etag})

                    uploaded_bytes += len(chunk)
                    pbar.update(len(chunk))

                    if on_progress:
                        on_progress(uploaded_bytes, file_size)

        return self._complete_multipart(clip_id, parts)

    def bulk_upload(
        self,
        video_paths: list[str | Path],
        *,
        task: str | None = None,
        source: str | None = None,
        wait: bool = False,
        timeout: int = 600,
        max_workers: int = 4,
    ) -> dict[str, Any]:
        """
        Upload multiple videos in parallel.

        Args:
            video_paths: List of paths to video files (max 50)
            task: Task type (e.g., "pour_latte")
            source: Source identifier for attribution
            wait: If True, wait for all processing to complete
            timeout: Timeout in seconds when waiting
            max_workers: Max parallel uploads

        Returns:
००            Dict with "clips" list and "failed" list

        Example:
            result = client.bulk_upload(["a.mp4", "b.mp4"], task="pour")
            print(f"Uploaded {len(result['clips'])} clips")
        """
        paths = [Path(p) for p in video_paths]

        if len(paths) > MAX_BULK_FILES:
            raise ValueError(
                f"Too many files: {len(paths)}. Maximum: {MAX_BULK_FILES}"
            )

        # Validate all files exist first
        for p in paths:
            if not p.exists():
                raise FileNotFoundError(f"Video not found: {p}")
            ext = p.suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise ValueError(f"Unsupported file type: {ext}")

        clips = []
        failed = []

        def upload_one(path: Path) -> dict[str, Any] | Exception:
            try:
                return self.upload_direct(
                    path,
                    task=task,
                    source=source,
                    wait=False,  # We'll wait at the end if needed
                )
            except Exception as e:
                return e

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(upload_one, p): p for p in paths}

            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Uploading",
                unit="file",
            ):
                path = futures[future]
                try:
                    result = future.result()
                    if isinstance(result, Exception):
                        failed.append({"path": str(path), "error": str(result)})
                    else:
                        clips.append(result)
                except Exception as e:
                    failed.append({"path": str(path), "error": str(e)})

        # Wait for all clips to finish processing if requested
        if wait and clips:
            for i, clip in enumerate(clips):
                try:
                    clips[i] = self.wait(clip["id"], timeout=timeout)
                except Exception as e:
                    failed.append({"clipId": clip["id"], "error": str(e)})

        return {"clips": clips, "failed": failed}

    def cancel_upload(self, clip_id: str) -> bool:
        """
        Cancel an in-progress upload.

        Args:
            clip_id: Clip ID to cancel

        Returns:
            True if cancelled successfully
        """
        self._request("POST", f"/clips/{clip_id}/cancel")
        return True

    def export(
        self,
        *,
        task: str | None = None,
        clip_ids: list[str] | None = None,
        include_video: bool = True,
        include_depth: bool = True,
        include_hand_poses: bool = True,
        include_actions: bool = True,
        include_objects: bool = True,
        chunk_size: int | None = None,
        output_path: str | Path | None = None,
        extract: bool = True,
    ) -> ExportResult:
        """
        Export clips as a downloadable dataset.

        Args:
            task: Export all clips for this task
            clip_ids: Export specific clips by ID
            include_video: Include video frames
            include_depth: Include depth maps
            include_hand_poses: Include hand pose annotations
            include_actions: Include action annotations
            include_objects: Include object annotations
            chunk_size: Max clips per export (for large exports)
            output_path: If set, download and optionally extract to this path
            extract: If True and output_path set, extract the ZIP

        Returns:
            ExportResult with download URL and metadata

        Example:
            result = client.export(task="pour_latte", output_path="./data/")
            print(f"Exported {result.total_clips} clips")
        """
        if not task and not clip_ids:
            raise ValueError("Must specify either task or clip_ids")

        payload = {
            "includeVideo": include_video,
            "includeDepth": include_depth,
            "includeHandPoses": include_hand_poses,
            "includeActions": include_actions,
            "includeObjects": include_objects,
        }

        if task:
            payload["task"] = task
        if clip_ids:
            payload["clipIds"] = clip_ids
        if chunk_size:
            payload["chunkSize"] = chunk_size

        response = self._request("POST", "/exports", json=payload)
        data = response.json()

        result = ExportResult(
            download_url=data["downloadUrl"],
            total_clips=data["totalClips"],
            total_frames=data["totalFrames"],
            export_key=data["exportKey"],
            expires_at=data["expiresAt"],
        )

        # Download if output path specified
        if output_path:
            output_path = Path(output_path)
            output_path.mkdir(parents=True, exist_ok=True)

            # Download the ZIP
            download_response = requests.get(result.download_url, stream=True)
            download_response.raise_for_status()

            zip_path = output_path / f"{result.export_key}.zip"
            total_size = int(download_response.headers.get("content-length", 0))

            with open(zip_path, "wb") as f:
                with tqdm(total=total_size, unit="B", unit_scale=True, desc="Downloading") as pbar:
                    for chunk in download_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))

            if extract:
                extract_dir = output_path / result.export_key
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(extract_dir)
                zip_path.unlink()
                result.local_path = extract_dir
            else:
                result.local_path = zip_path

        return result


# Module-level convenience functions using default client
_default_client: Client | None = None


def _get_client() -> Client:
    """Get or create default client."""
    global _default_client
    if _default_client is None:
        _default_client = Client()
    return _default_client


def upload(video_path: str | Path, **kwargs) -> dict[str, Any]:
    """
    Upload a video. See Client.upload for args.
    
    Example:
        from terso import upload
        clip = upload("video.mp4", task="pour", wait=True)
    """
    return _get_client().upload(video_path, **kwargs)


def download(clip_id: str, output_dir: str | Path, **kwargs) -> Path:
    """
    Download a clip. See Client.download for args.

    Example:
        from terso import download
        path = download("abc123", "./output")
    """
    return _get_client().download(clip_id, output_dir, **kwargs)


def bulk_upload(video_paths: list[str | Path], **kwargs) -> dict[str, Any]:
    """
    Upload multiple videos. See Client.bulk_upload for args.

    Example:
        from terso import bulk_upload
        result = bulk_upload(["a.mp4", "b.mp4"], task="pour")
    """
    return _get_client().bulk_upload(video_paths, **kwargs)


def cancel_upload(clip_id: str) -> bool:
    """
    Cancel an upload. See Client.cancel_upload for args.

    Example:
        from terso import cancel_upload
        cancel_upload("clip_abc123")
    """
    return _get_client().cancel_upload(clip_id)


def export(**kwargs) -> ExportResult:
    """
    Export clips as a dataset. See Client.export for args.

    Example:
        from terso import export
        result = export(task="pour_latte", output_path="./data/")
    """
    return _get_client().export(**kwargs)
