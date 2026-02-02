"""File explorer API routes."""

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/files", tags=["files"])


class FileInfo(BaseModel):
    """File or directory information."""

    name: str
    path: str
    is_dir: bool
    size: int
    modified: float


class DirectoryListing(BaseModel):
    """Directory listing response."""

    path: str
    parent: Optional[str]
    items: list[FileInfo]


def get_safe_path(base: str, requested: str) -> Path:
    """Get a safe absolute path, preventing directory traversal.

    Args:
        base: Base directory (usually home)
        requested: Requested path

    Returns:
        Safe absolute path

    Raises:
        HTTPException: If path is outside base directory
    """
    base_path = Path(base).resolve()

    if requested:
        # Handle ~ for home directory
        if requested.startswith("~"):
            requested = os.path.expanduser(requested)
        requested_path = Path(requested).resolve()
    else:
        requested_path = base_path

    # Ensure the path is within allowed boundaries
    try:
        requested_path.relative_to(base_path)
    except ValueError:
        # Path is outside base, but allow if it's an absolute path that exists
        if not requested_path.exists():
            raise HTTPException(status_code=403, detail="Access denied")

    return requested_path


@router.get("", response_model=DirectoryListing)
async def list_directory(path: Optional[str] = Query(None, description="Directory path to list")):
    """List contents of a directory.

    Args:
        path: Directory path (defaults to home directory)

    Returns:
        Directory listing with files and folders
    """
    home = os.path.expanduser("~")

    if path is None:
        path = home

    # Expand ~ in path
    if path.startswith("~"):
        path = os.path.expanduser(path)

    dir_path = Path(path).resolve()

    if not dir_path.exists():
        raise HTTPException(status_code=404, detail="Directory not found")

    if not dir_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    items = []
    try:
        for entry in sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                stat = entry.stat()
                items.append(
                    FileInfo(
                        name=entry.name,
                        path=str(entry),
                        is_dir=entry.is_dir(),
                        size=stat.st_size if not entry.is_dir() else 0,
                        modified=stat.st_mtime,
                    )
                )
            except (PermissionError, OSError):
                # Skip files we can't access
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Get parent directory
    parent = str(dir_path.parent) if dir_path != dir_path.parent else None

    return DirectoryListing(path=str(dir_path), parent=parent, items=items)


@router.get("/download")
async def download_file(path: str = Query(..., description="File path to download")):
    """Download a file.

    Args:
        path: Path to the file

    Returns:
        File download response
    """
    # Expand ~ in path
    if path.startswith("~"):
        path = os.path.expanduser(path)

    file_path = Path(path).resolve()

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    try:
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type="application/octet-stream",
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    path: str = Query(..., description="Directory to upload to"),
):
    """Upload a file to a directory.

    Args:
        file: File to upload
        path: Directory path to upload to

    Returns:
        Upload result
    """
    # Expand ~ in path
    if path.startswith("~"):
        path = os.path.expanduser(path)

    dir_path = Path(path).resolve()

    if not dir_path.exists():
        raise HTTPException(status_code=404, detail="Directory not found")

    if not dir_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    # Create the destination file path
    dest_path = dir_path / file.filename

    try:
        # Read and write the file
        content = await file.read()
        with open(dest_path, "wb") as f:
            f.write(content)

        return {
            "success": True,
            "filename": file.filename,
            "path": str(dest_path),
            "size": len(content),
        }
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
