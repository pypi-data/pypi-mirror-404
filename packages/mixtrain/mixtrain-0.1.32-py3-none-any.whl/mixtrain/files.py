"""Files - File storage operations for Mixtrain workspace.

This module provides the Files class for uploading, downloading, listing,
and deleting files in workspace cloud storage.

Example:
    >>> from mixtrain import Files
    >>> files = Files()
    >>>
    >>> # Upload a file
    >>> info = files.upload("model.bin", "outputs/model.bin")
    >>>
    >>> # List files
    >>> for f in files.list("outputs/"):
    ...     print(f.path, f.size)
    >>>
    >>> # Download a file
    >>> local_path = files.download("outputs/model.bin", "local_model.bin")
    >>>
    >>> # Delete a file
    >>> files.delete("outputs/model.bin")
    >>>
    >>> # Upload a directory
    >>> result = files.upload_dir("./my_data/", "data/")
    >>> print(f"Uploaded {len(result.successful)} files")
"""

import logging
import mimetypes
import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from .client import MixClient

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Metadata for a file in storage.

    Attributes:
        path: User-facing path (e.g., 'outputs/model.bin')
        name: File name (last segment of path)
        url: Full storage URL (e.g., 'gs://bucket/prefix/outputs/model.bin')
        size: File size in bytes
        content_type: MIME type of the file
        last_modified: Last modification timestamp
        download_url: Presigned URL for downloading (when available)
    """

    path: str
    name: str
    url: str | None = None
    size: int | None = None
    content_type: str | None = None
    last_modified: datetime | None = None
    download_url: str | None = None

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "FileInfo":
        """Create FileInfo from API response data."""
        last_modified = data.get("last_modified")
        if last_modified and isinstance(last_modified, str):
            # Parse ISO format datetime
            try:
                last_modified = datetime.fromisoformat(
                    last_modified.replace("Z", "+00:00")
                )
            except ValueError as e:
                logger.warning(
                    f"Failed to parse last_modified timestamp '{last_modified}': {e}"
                )
                last_modified = None

        return cls(
            path=data.get("path", ""),
            name=data.get("name", ""),
            size=data.get("size_bytes"),
            content_type=data.get("content_type"),
            last_modified=last_modified,
            download_url=data.get("download_url"),
        )


@dataclass
class UploadError:
    """Details about a failed file upload.

    Attributes:
        local_path: Path to the local file that failed to upload
        remote_path: Intended remote path
        error: Error message describing the failure
    """

    local_path: str
    remote_path: str
    error: str


@dataclass
class UploadDirResult:
    """Result of a directory upload operation.

    Attributes:
        successful: List of FileInfo for successfully uploaded files
        failed: List of UploadError for failed uploads
    """

    successful: list[FileInfo]
    failed: list[UploadError]

    @property
    def all_succeeded(self) -> bool:
        """Returns True if all files were uploaded successfully."""
        return len(self.failed) == 0

    def __len__(self) -> int:
        """Returns total number of files attempted."""
        return len(self.successful) + len(self.failed)


class Files:
    """File storage operations for workspace.

    Provides methods to upload, download, list, and delete files in
    workspace cloud storage. Uses presigned URLs for direct-to-cloud
    transfers.

    Usage:
        >>> from mixtrain import Files
        >>> files = Files()

        # Upload a file
        >>> info = files.upload("model.bin", "outputs/model.bin")
        >>> print(info.path)
        outputs/model.bin

        # List files with prefix
        >>> for f in files.list("outputs/"):
        ...     print(f"{f.path}: {f.size} bytes")

        # Download a file
        >>> local_path = files.download("outputs/model.bin")
        >>> print(f"Downloaded to: {local_path}")

        # Delete a file
        >>> files.delete("outputs/model.bin")

    Args:
        client: Optional MixClient instance. If not provided, creates a new one.
    """

    def __init__(self, client: MixClient | None = None):
        """Initialize Files with optional MixClient.

        Args:
            client: MixClient instance for API operations. Creates new one if not provided.
        """
        self._client = client or MixClient()

    @property
    def workspace(self) -> str:
        """Get the current workspace name."""
        return self._client._workspace_name

    def upload(
        self,
        local_path: str,
        remote_path: str | None = None,
        content_type: str | None = None,
        timeout: float = 300.0,
    ) -> FileInfo:
        """Upload a file to workspace storage.

        Args:
            local_path: Path to the local file to upload
            remote_path: Target path in storage. Defaults to the local filename.
            content_type: MIME type. Auto-detected if not provided.
            timeout: HTTP timeout in seconds for the upload. Default 300s (5 min).

        Returns:
            FileInfo with the uploaded file's metadata

        Raises:
            FileNotFoundError: If local file doesn't exist
            Exception: On upload failure
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")

        if remote_path is None:
            remote_path = os.path.basename(local_path)

        if content_type is None:
            content_type, _ = mimetypes.guess_type(local_path)
            content_type = content_type or "application/octet-stream"

        file_size = os.path.getsize(local_path)

        # Request presigned upload URL
        response = self._client._request(
            "GET",
            "/files/presigned",
            params={
                "path": remote_path,
                "content_type": content_type,
            },
        )
        upload_info = response.json()

        # Upload directly to cloud storage
        with open(local_path, "rb") as f:
            with httpx.Client(timeout=timeout) as http_client:
                upload_response = http_client.put(
                    upload_info["upload_url"],
                    content=f,
                    headers={"Content-Type": content_type},
                )
                upload_response.raise_for_status()

        return FileInfo(
            path=remote_path,
            name=os.path.basename(remote_path),
            url=upload_info.get("storage_url"),
            size=file_size,
            content_type=content_type,
        )

    def upload_dir(
        self,
        local_dir: str,
        remote_prefix: str = "",
        pattern: str = "**/*",
        timeout: float = 300.0,
        max_concurrency: int = 5,
    ) -> UploadDirResult:
        """Upload an entire directory to workspace storage.

        Files are uploaded in parallel for efficiency. The directory structure
        is preserved relative to the local_dir.

        Args:
            local_dir: Path to the local directory to upload
            remote_prefix: Prefix to add to remote paths (e.g., "data/" to upload to data/ folder)
            pattern: Glob pattern to filter files (default "**/*" for all files)
            timeout: HTTP timeout in seconds per file upload. Default 300s (5 min).
            max_concurrency: Maximum number of parallel uploads. Default 5.

        Returns:
            UploadDirResult with lists of successful and failed uploads

        Raises:
            FileNotFoundError: If local_dir doesn't exist or isn't a directory

        Example:
            >>> files = Files()
            >>> # Upload all files
            >>> result = files.upload_dir("./my_data/", "data/")
            >>> print(f"Uploaded {len(result.successful)}, Failed {len(result.failed)}")
            >>>
            >>> # Upload only JSON files
            >>> result = files.upload_dir("./my_data/", "data/", pattern="**/*.json")
            >>>
            >>> # Upload with more parallelism
            >>> result = files.upload_dir("./my_data/", "data/", max_concurrency=10)
        """
        local_path = Path(local_dir)
        if not local_path.exists():
            raise FileNotFoundError(f"Directory not found: {local_dir}")
        if not local_path.is_dir():
            raise FileNotFoundError(f"Not a directory: {local_dir}")

        # Normalize remote prefix
        if remote_prefix and not remote_prefix.endswith("/"):
            remote_prefix = remote_prefix + "/"

        # Collect all files matching the pattern
        files_to_upload: list[tuple[Path, str]] = []
        for file_path in local_path.glob(pattern):
            if file_path.is_file():
                # Calculate relative path from local_dir
                relative_path = file_path.relative_to(local_path)
                remote_path = f"{remote_prefix}{relative_path}"
                files_to_upload.append((file_path, remote_path))

        if not files_to_upload:
            logger.warning(
                f"No files found matching pattern '{pattern}' in {local_dir}"
            )
            return UploadDirResult(successful=[], failed=[])

        successful: list[FileInfo] = []
        failed: list[UploadError] = []

        def upload_single(
            item: tuple[Path, str],
        ) -> tuple[bool, FileInfo | UploadError]:
            file_path, remote_path = item
            try:
                info = self.upload(str(file_path), remote_path, timeout=timeout)
                return (True, info)
            except Exception as e:
                return (
                    False,
                    UploadError(
                        local_path=str(file_path),
                        remote_path=remote_path,
                        error=str(e),
                    ),
                )

        # Upload files in parallel
        with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
            futures = {
                executor.submit(upload_single, item): item for item in files_to_upload
            }
            for future in as_completed(futures):
                success, result = future.result()
                if success:
                    successful.append(result)
                else:
                    failed.append(result)

        return UploadDirResult(successful=successful, failed=failed)

    def download(
        self,
        remote_path: str,
        local_path: str | None = None,
        timeout: float = 300.0,
    ) -> str:
        """Download a file from workspace storage or HTTP URL.

        Supports multiple URL schemes:
        - gs://bucket/path - Google Cloud Storage (requires workspace secrets)
        - s3://bucket/path - S3/S3-compatible storage (requires workspace secrets)
        - http://... or https://... - Public HTTP URLs (no auth required)
        - Relative paths - Files in workspace storage

        Args:
            remote_path: Path of the file in storage, or full URL
            local_path: Local destination path. Defaults to the filename in current directory.
            timeout: HTTP timeout in seconds for the download. Default 300s (5 min).

        Returns:
            Path to the downloaded file

        Raises:
            Exception: On download failure
        """
        # Handle HTTP/HTTPS URLs directly
        if remote_path.startswith(("http://", "https://")):
            download_url = remote_path
            if local_path is None:
                from urllib.parse import unquote, urlparse

                parsed = urlparse(remote_path)
                local_path = os.path.basename(unquote(parsed.path)) or "download"
        else:
            if local_path is None:
                local_path = os.path.basename(remote_path)

            # Get presigned download URL
            response = self._client._request(
                "GET",
                f"/files/{remote_path}",
            )
            download_info = response.json()
            download_url = download_info["download_url"]

        # Download directly from URL
        with httpx.Client(timeout=timeout, follow_redirects=True) as http_client:
            with http_client.stream("GET", download_url) as r:
                r.raise_for_status()
                with open(local_path, "wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)

        return local_path

    def list(
        self,
        prefix: str = "",
        limit: int = 100,
    ) -> list[FileInfo]:
        """List files in workspace storage.

        Args:
            prefix: Filter files by path prefix (e.g., "outputs/")
            limit: Maximum number of files to return per request

        Returns:
            List of FileInfo objects for matching files
        """
        response = self._client._request(
            "GET",
            "/files",
            params={"prefix": prefix, "limit": limit},
        )
        data = response.json()

        return [FileInfo.from_api_response(f) for f in data.get("data", [])]

    def iter(
        self,
        prefix: str = "",
        limit: int = 100,
    ) -> Iterator[FileInfo]:
        """Iterate over all files in workspace storage with automatic pagination.

        Args:
            prefix: Filter files by path prefix (e.g., "outputs/")
            limit: Number of files to fetch per API request

        Yields:
            FileInfo objects for each file
        """
        continuation_token = None

        while True:
            params = {"prefix": prefix, "limit": limit}
            if continuation_token:
                params["continuation_token"] = continuation_token

            response = self._client._request(
                "GET",
                "/files",
                params=params,
            )
            data = response.json()

            for file_data in data.get("data", []):
                yield FileInfo.from_api_response(file_data)

            continuation_token = data.get("continuation_token")
            if not continuation_token:
                break

    def get(self, remote_path: str) -> FileInfo:
        """Get metadata and download URL for a file.

        Supports multiple URL schemes:
        - gs://bucket/path - Google Cloud Storage (requires workspace secrets)
        - s3://bucket/path - S3/S3-compatible storage (requires workspace secrets)
        - http://... or https://... - Public HTTP URLs (no auth required)
        - Relative paths - Files in workspace storage

        Args:
            remote_path: Path of the file in storage, or full URL

        Returns:
            FileInfo with metadata and presigned download URL

        Raises:
            Exception: If file not found or inaccessible
        """
        # Handle HTTP/HTTPS URLs directly without going through the backend
        if remote_path.startswith(("http://", "https://")):
            return self._get_http_file(remote_path)

        response = self._client._request(
            "GET",
            f"/files/{remote_path}",
        )
        data = response.json()

        return FileInfo(
            path=data.get("path", remote_path),
            name=os.path.basename(remote_path),
            size=data.get("size_bytes"),
            content_type=data.get("content_type"),
            last_modified=(
                datetime.fromisoformat(data["last_modified"].replace("Z", "+00:00"))
                if data.get("last_modified")
                else None
            ),
            download_url=data.get("download_url"),
        )

    def _get_http_file(self, url: str) -> FileInfo:
        """Get metadata for an HTTP/HTTPS URL.

        Uses HTTP HEAD request to fetch metadata without downloading the file.

        Args:
            url: Full HTTP or HTTPS URL

        Returns:
            FileInfo with metadata and the URL itself as download_url

        Raises:
            Exception: If URL is inaccessible
        """
        from email.utils import parsedate_to_datetime
        from urllib.parse import unquote, urlparse

        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.head(url)
                response.raise_for_status()

                # Extract metadata from headers
                content_length = response.headers.get("content-length")
                content_type = response.headers.get("content-type")
                last_modified_str = response.headers.get("last-modified")

                # Parse last-modified header (RFC 7231 format)
                last_modified = None
                if last_modified_str:
                    try:
                        last_modified = parsedate_to_datetime(last_modified_str)
                    except (ValueError, TypeError):
                        pass

                # Extract filename from URL path
                parsed = urlparse(url)
                path = unquote(parsed.path)
                name = os.path.basename(path) or url

                return FileInfo(
                    path=url,
                    name=name,
                    url=url,
                    size=int(content_length) if content_length else None,
                    content_type=content_type.split(";")[0].strip()
                    if content_type
                    else None,
                    last_modified=last_modified,
                    download_url=url,
                )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise FileNotFoundError(f"File not found: {url}") from e
            raise Exception(
                f"HTTP error {e.response.status_code} fetching {url}"
            ) from e
        except httpx.RequestError as e:
            raise Exception(f"Failed to fetch {url}: {e}") from e

    def delete(self, remote_path: str) -> bool:
        """Delete a file from workspace storage.

        Args:
            remote_path: Path of the file to delete

        Returns:
            True if deletion was successful

        Raises:
            Exception: If file not found or deletion failed
        """
        self._client._request(
            "DELETE",
            f"/files/{remote_path}",
        )
        # 204 No Content indicates success
        return True

    def exists(self, remote_path: str) -> bool:
        """Check if a file exists in workspace storage.

        Args:
            remote_path: Path of the file to check

        Returns:
            True if file exists, False otherwise

        Raises:
            Exception: On network/auth errors (only 404 returns False)
        """
        try:
            self.get(remote_path)
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise
