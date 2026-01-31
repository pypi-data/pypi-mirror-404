"""Cache persistence with authenticated encryption"""

import appdirs
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken
import hashlib
import logging
import os
import pickle
import pathlib
import time

import canvaslms.hacks.attachment_cache as attachment_cache
from canvaslms.hacks.canvasapi import (
    SUBMISSION_TTL_MINUTES,
    DEFAULT_CACHE_TTL_DAYS,
    USER_CACHE_TTL_DAYS,
    GROUP_CACHE_TTL_DAYS,
)

logger = logging.getLogger(__name__)
dirs = appdirs.AppDirs("canvaslms", "dbosk@kth.se")


def derive_key(token, hostname):
    """Derives a Fernet key from the Canvas token and hostname"""
    start = time.perf_counter()

    # Use hostname as salt (hashed to get consistent 16 bytes)
    salt = hashlib.sha256(hostname.encode()).digest()[:16]

    # Derive key using PBKDF2HMAC
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(token.encode()))

    elapsed = time.perf_counter() - start
    logger.info(f"Key derivation: {elapsed:.2f}s (PBKDF2 100k iterations)")

    return key


def get_cache_path(hostname):
    """Returns the path to the cache file for a given hostname"""
    # Create a safe filename from the hostname
    safe_hostname = hostname.replace("://", "_").replace("/", "_")
    cache_file = f"canvas_cache_{safe_hostname}.enc"
    return os.path.join(dirs.user_cache_dir, cache_file)


def save_canvas_cache(canvas, token, hostname):
    """Saves the Canvas object to encrypted cache"""
    try:
        save_start = time.perf_counter()

        # Derive encryption key
        key = derive_key(token, hostname)
        fernet = Fernet(key)

        # Pickle and encrypt
        pickle_start = time.perf_counter()
        pickled = pickle.dumps(canvas)
        pickle_elapsed = time.perf_counter() - pickle_start
        pickle_size = len(pickled)

        encrypt_start = time.perf_counter()
        encrypted = fernet.encrypt(pickled)
        encrypt_elapsed = time.perf_counter() - encrypt_start

        # Write to cache file
        cache_path = get_cache_path(hostname)
        os.makedirs(pathlib.PurePath(cache_path).parent, exist_ok=True)
        write_start = time.perf_counter()
        with open(cache_path, "wb") as f:
            f.write(encrypted)
        write_elapsed = time.perf_counter() - write_start

        save_elapsed = time.perf_counter() - save_start
        logger.info(
            f"Canvas cache save: {save_elapsed:.2f}s total "
            f"(pickle: {pickle_elapsed:.2f}s/{pickle_size/1024:.1f}KB, "
            f"encrypt: {encrypt_elapsed:.2f}s, write: {write_elapsed:.2f}s)"
        )
    except Exception:
        # If saving fails, silently continue
        # (cache is optional, don't break the command)
        pass


def load_canvas_cache(token, hostname):
    """Loads the Canvas object from encrypted cache, returns None if unavailable"""
    try:
        load_start = time.perf_counter()

        # Derive encryption key
        key = derive_key(token, hostname)
        fernet = Fernet(key)

        # Read and decrypt
        cache_path = get_cache_path(hostname)
        read_start = time.perf_counter()
        with open(cache_path, "rb") as f:
            encrypted = f.read()
        read_elapsed = time.perf_counter() - read_start
        encrypted_size = len(encrypted)

        decrypt_start = time.perf_counter()
        pickled = fernet.decrypt(encrypted)
        decrypt_elapsed = time.perf_counter() - decrypt_start

        unpickle_start = time.perf_counter()
        canvas = pickle.loads(pickled)
        unpickle_elapsed = time.perf_counter() - unpickle_start

        load_elapsed = time.perf_counter() - load_start
        logger.info(
            f"Canvas cache load: {load_elapsed:.2f}s total "
            f"(read: {read_elapsed:.2f}s/{encrypted_size/1024:.1f}KB, "
            f"decrypt: {decrypt_elapsed:.2f}s, unpickle: {unpickle_elapsed:.2f}s)"
        )

        return canvas
    except (FileNotFoundError, InvalidToken, pickle.UnpicklingError, Exception):
        # Cache doesn't exist or is invalid, return None
        return None


def clear_cache(hostname):
    """Clears the cache for the given hostname"""
    cache_path = get_cache_path(hostname)
    try:
        os.remove(cache_path)
        return True
    except FileNotFoundError:
        return False


def add_command(subp):
    """Adds the cache command to argparse parser"""
    cache_parser = subp.add_parser(
        "cache",
        help="Manage caches",
        description=f"""
Manages the persistent caches used by canvaslms.

The Canvas object cache stores API responses (courses, assignments, users,
submissions) encrypted on disk. Objects are refreshed based on their type:

- Submissions (non-passing): {SUBMISSION_TTL_MINUTES} minutes

- Users: {USER_CACHE_TTL_DAYS} days

- Groups: {GROUP_CACHE_TTL_DAYS} days

- Other objects: {DEFAULT_CACHE_TTL_DAYS} days

Submissions with passing grades (A, P, complete) are never refreshed.

The attachment cache stores downloaded submission files using content-addressed
storage. Files not accessed in 90 days can be cleaned with clear-attachments.
""",
    )

    cache_subp = cache_parser.add_subparsers(
        title="cache commands", dest="cache_command", required=True
    )

    clear_parser = cache_subp.add_parser("clear", help="Clear the cached Canvas data")
    clear_parser.set_defaults(func=clear_command)
    clear_attachments_parser = cache_subp.add_parser(
        "clear-attachments",
        help="Remove old cached attachment files",
        description="""
    Removes cached attachment files that haven't been accessed in the specified
    number of days. This helps manage disk space while keeping frequently-used
    files available.

    Cached attachments are stored in a platform-specific cache directory and use
    content-addressed storage (files are identified by SHA-256 hash). This means
    identical files submitted by different students or in different submission
    versions are stored only once.

    The cleanup process:
    1. Identifies attachments not accessed within the time window
    2. Removes their index entries
    3. Removes orphaned data files no longer referenced by any index entry
    4. Reports statistics about files removed and space freed
    """,
    )
    clear_attachments_parser.add_argument(
        "--older-than-days",
        type=int,
        default=90,
        help="Remove files not accessed in this many days (default: 90)",
    )
    clear_attachments_parser.set_defaults(func=clear_attachments_command)


def clear_command(config, canvas, args):
    """Clears the Canvas cache"""
    import canvaslms.cli.login

    hostname, token = canvaslms.cli.login.load_credentials(config)

    if not hostname:
        import canvaslms.cli

        canvaslms.cli.err(1, "No hostname configured, run `canvaslms login`")

    if "://" not in hostname:
        hostname = f"https://{hostname}"

    if clear_cache(hostname):
        logger.info(f"Cache cleared for {hostname}")
    else:
        logger.info(f"No cache found for {hostname}")


def clear_attachments_command(config, canvas, args):
    """Removes old cached attachments and reports statistics"""
    max_age = args.older_than_days

    print(f"Removing cached attachments not accessed in {max_age} days...")

    stats = attachment_cache.cleanup_old_attachments(max_age_days=max_age)

    files_removed = stats["files_removed"]
    bytes_freed = stats["bytes_freed"]

    # Convert bytes to human-readable format
    if bytes_freed < 1024:
        size_str = f"{bytes_freed} bytes"
    elif bytes_freed < 1024 * 1024:
        size_str = f"{bytes_freed / 1024:.1f} KB"
    elif bytes_freed < 1024 * 1024 * 1024:
        size_str = f"{bytes_freed / (1024 * 1024):.1f} MB"
    else:
        size_str = f"{bytes_freed / (1024 * 1024 * 1024):.2f} GB"

    if files_removed == 0:
        print(f"No files older than {max_age} days found.")
    else:
        print(f"Removed {files_removed} file(s), freed {size_str}.")
