"""
codrsync cloud storage — Upload/download files to DO Spaces via API

Usage:
    from codrsync.cloud import upload_file, list_files, get_usage

    # Upload a file
    result = upload_file("./myfile.txt")

    # List files
    files = list_files()

    # Get storage usage
    usage = get_usage()
"""

import mimetypes
from pathlib import Path
from typing import Optional, List, Dict, Any

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from codrsync.cloud_auth import get_cloud_credentials, CODRSYNC_API_URL
from codrsync.i18n import t

console = Console()


class StorageError(Exception):
    """Storage operation error."""
    pass


class StorageLimitExceeded(StorageError):
    """Storage limit exceeded."""
    def __init__(self, message: str, usage: dict):
        super().__init__(message)
        self.usage = usage


def _get_auth_headers() -> dict:
    """Get authorization headers from stored credentials."""
    creds = get_cloud_credentials()
    if not creds or not creds.get("access_token"):
        raise StorageError(t("cloud_storage.not_authenticated"))

    return {
        "Authorization": f"Bearer {creds['access_token']}",
        "Content-Type": "application/json",
    }


def _api_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[dict] = None,
    base_url: Optional[str] = None,
) -> dict:
    """Make authenticated API request."""
    url = f"{base_url or CODRSYNC_API_URL}{endpoint}"
    headers = _get_auth_headers()

    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            resp = requests.post(url, json=data, headers=headers, timeout=30)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=30)
        else:
            raise StorageError(f"Unsupported method: {method}")

        if resp.status_code == 403:
            error_data = resp.json()
            if "usage" in error_data:
                raise StorageLimitExceeded(
                    error_data.get("message", "Storage limit exceeded"),
                    error_data.get("usage", {})
                )
            raise StorageError(error_data.get("error", "Forbidden"))

        resp.raise_for_status()
        return resp.json()

    except requests.RequestException as e:
        raise StorageError(f"Request failed: {str(e)}")


def upload_file(
    file_path: str,
    folder: str = "uploads",
    is_public: bool = False,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Upload a file to cloud storage.

    Args:
        file_path: Path to local file
        folder: Folder in storage (default: uploads)
        is_public: Whether file should be publicly accessible
        base_url: API base URL (default: codrsync.dev)

    Returns:
        Dict with key, url, and usage info

    Raises:
        StorageError: If upload fails
        StorageLimitExceeded: If storage limit is exceeded
    """
    path = Path(file_path)
    if not path.exists():
        raise StorageError(f"File not found: {file_path}")

    file_size = path.stat().st_size
    filename = path.name
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    # Step 1: Get presigned URL
    console.print(t("cloud_storage.requesting_upload_url"))

    presign_data = _api_request(
        "/api/storage/presign",
        method="POST",
        data={
            "filename": filename,
            "contentType": content_type,
            "fileSize": file_size,
            "folder": folder,
        },
        base_url=base_url,
    )

    upload_url = presign_data["uploadUrl"]
    key = presign_data["key"]

    # Step 2: Upload directly to DO Spaces
    console.print(t("cloud_storage.uploading", filename=filename, size=_format_bytes(file_size)))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Uploading...", total=file_size)

        with open(path, "rb") as f:
            file_data = f.read()

        try:
            resp = requests.put(
                upload_url,
                data=file_data,
                headers={"Content-Type": content_type},
                timeout=300,
            )
            resp.raise_for_status()
            progress.update(task, completed=file_size)
        except requests.RequestException as e:
            raise StorageError(f"Upload failed: {str(e)}")

    # Step 3: Confirm upload
    console.print(t("cloud_storage.confirming"))

    _api_request(
        "/api/storage/confirm",
        method="POST",
        data={
            "key": key,
            "filename": filename,
            "size": file_size,
            "contentType": content_type,
            "folder": folder,
            "isPublic": is_public,
        },
        base_url=base_url,
    )

    console.print(f"[green]{t('common.success')}[/green] {t('cloud_storage.uploaded', key=key)}")

    return {
        "key": key,
        "filename": filename,
        "size": file_size,
        "url": presign_data.get("publicUrl"),
        "usage": presign_data.get("usage"),
    }


def download_file(
    key: str,
    output_path: Optional[str] = None,
    base_url: Optional[str] = None,
) -> str:
    """Download a file from cloud storage.

    Args:
        key: File key in storage
        output_path: Local path to save file (default: current directory)
        base_url: API base URL

    Returns:
        Path to downloaded file
    """
    # Get file info and presigned URL
    files = list_files(base_url=base_url)

    file_info = None
    for f in files:
        if f["key"] == key:
            file_info = f
            break

    if not file_info:
        raise StorageError(f"File not found: {key}")

    url = file_info["url"]
    filename = file_info.get("filename") or key.split("/")[-1]

    if output_path:
        save_path = Path(output_path)
    else:
        save_path = Path.cwd() / filename

    console.print(t("cloud_storage.downloading", filename=filename))

    try:
        resp = requests.get(url, timeout=300)
        resp.raise_for_status()
        save_path.write_bytes(resp.content)
    except requests.RequestException as e:
        raise StorageError(f"Download failed: {str(e)}")

    console.print(f"[green]{t('common.success')}[/green] {t('cloud_storage.downloaded', path=str(save_path))}")

    return str(save_path)


def list_files(
    folder: Optional[str] = None,
    base_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List files in cloud storage.

    Args:
        folder: Filter by folder (optional)
        base_url: API base URL

    Returns:
        List of file info dicts
    """
    endpoint = "/api/storage/files"
    if folder:
        endpoint += f"?folder={folder}"

    result = _api_request(endpoint, base_url=base_url)
    return result.get("files", [])


def delete_file(
    key: str,
    base_url: Optional[str] = None,
) -> bool:
    """Delete a file from cloud storage.

    Args:
        key: File key to delete
        base_url: API base URL

    Returns:
        True if deleted successfully
    """
    _api_request(
        f"/api/storage/files?key={key}",
        method="DELETE",
        base_url=base_url,
    )

    console.print(f"[green]{t('common.success')}[/green] {t('cloud_storage.deleted', key=key)}")
    return True


def get_usage(base_url: Optional[str] = None) -> Dict[str, Any]:
    """Get storage usage and limits.

    Returns:
        Dict with usage, limit, remaining, percentUsed
    """
    return _api_request("/api/storage/usage", base_url=base_url)


def _format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"
