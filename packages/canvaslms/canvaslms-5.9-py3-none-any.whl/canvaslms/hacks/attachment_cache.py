"""Content-addressed cache for Canvas submission attachments"""

import appdirs
import hashlib
import json
import logging
import pathlib
import shutil
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

CACHE_DIR = pathlib.Path(appdirs.user_cache_dir("canvaslms")) / "attachments"
INDEX_FILE = CACHE_DIR / "index.json"


def _ensure_cache_dir():
    """Create cache directory if it doesn't exist"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _load_index() -> Dict[str, Dict[str, Any]]:
    """Load the metadata index from disk"""
    _ensure_cache_dir()
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_index(index: Dict[str, Dict[str, Any]]):
    """Save the metadata index to disk"""
    _ensure_cache_dir()
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)


def _compute_hash(file_path: pathlib.Path) -> str:
    """Compute SHA-256 hash of file content"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_cached_attachment(attachment_id: int) -> Optional[pathlib.Path]:
    """
    Get cached file path for attachment, or None if not cached.

    Updates last_access timestamp on cache hit.
    """
    index = _load_index()
    attachment_key = str(attachment_id)

    if attachment_key not in index:
        logger.info(f"Attachment cache miss: {attachment_id}")
        return None

    entry = index[attachment_key]
    file_hash = entry["hash"]
    cached_file = CACHE_DIR / f"{file_hash}.dat"

    if not cached_file.exists():
        # Index entry exists but file missing - remove stale entry
        logger.info(f"Attachment cache: stale entry removed: {attachment_id}")
        del index[attachment_key]
        _save_index(index)
        return None

    # Update last access time
    entry["last_access"] = datetime.now().isoformat()
    _save_index(index)

    logger.info(
        f"Attachment cache hit: {attachment_id} "
        f"({entry['filename']}, {entry['size'] / 1024:.1f}KB)"
    )

    return cached_file


def cache_attachment(
    attachment_id: int, file_path: pathlib.Path, metadata: Dict[str, Any]
):
    """
    Cache an attachment file using content-addressed storage.

    Args:
        attachment_id: Canvas attachment ID
        file_path: Path to the downloaded file
        metadata: Dictionary with 'filename', 'size', 'content_type'
    """
    _ensure_cache_dir()

    # Compute content hash with timing
    hash_start = time.perf_counter()
    file_hash = _compute_hash(file_path)
    hash_elapsed = time.perf_counter() - hash_start

    file_size = file_path.stat().st_size
    logger.info(
        f"Attachment {attachment_id}: hash computed "
        f"({hash_elapsed:.2f}s, {file_size / 1024:.1f}KB)"
    )

    cached_file = CACHE_DIR / f"{file_hash}.dat"

    # Copy file to cache if not already present (deduplication)
    if not cached_file.exists():
        copy_start = time.perf_counter()
        shutil.copy2(file_path, cached_file)
        copy_elapsed = time.perf_counter() - copy_start
        logger.info(
            f"Attachment {attachment_id}: file cached " f"(copy: {copy_elapsed:.2f}s)"
        )
    else:
        logger.info(f"Attachment {attachment_id}: content already cached (dedup)")

    # Update index
    index = _load_index()
    index[str(attachment_id)] = {
        "hash": file_hash,
        "filename": metadata.get("filename", "unknown"),
        "size": metadata.get("size", 0),
        "content_type": metadata.get("content_type", "application/octet-stream"),
        "last_access": datetime.now().isoformat(),
    }
    _save_index(index)


def cleanup_old_attachments(max_age_days: int = 90) -> Dict[str, Any]:
    """
    Remove cached attachments not accessed in max_age_days.

    Returns:
        Dictionary with 'files_removed' and 'bytes_freed' statistics
    """
    _ensure_cache_dir()
    index = _load_index()
    cutoff_date = datetime.now() - timedelta(days=max_age_days)

    logger.info(
        f"Attachment cache cleanup: removing files not accessed in "
        f"{max_age_days} days"
    )

    # Find attachments to remove from index
    to_remove = []
    for attachment_id, entry in index.items():
        last_access = datetime.fromisoformat(entry["last_access"])
        if last_access < cutoff_date:
            to_remove.append(attachment_id)

    # Remove old entries from index
    for attachment_id in to_remove:
        del index[attachment_id]
    _save_index(index)

    # Build set of hashes still referenced
    referenced_hashes = {entry["hash"] for entry in index.values()}

    # Find and remove orphaned .dat files
    files_removed = 0
    bytes_freed = 0

    for dat_file in CACHE_DIR.glob("*.dat"):
        file_hash = dat_file.stem  # filename without extension
        if file_hash not in referenced_hashes:
            file_size = dat_file.stat().st_size
            dat_file.unlink()
            files_removed += 1
            bytes_freed += file_size

    logger.info(
        f"Attachment cache cleanup: {files_removed} files removed, "
        f"{bytes_freed / (1024 * 1024):.1f}MB freed"
    )

    return {"files_removed": files_removed, "bytes_freed": bytes_freed}
