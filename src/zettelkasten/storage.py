"""Safe, testable Markdown file IO. No background threads or database."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
from datetime import datetime, timezone
from uuid import uuid4


class ExternalChangeError(Exception):
    """The on-disk file no longer matches the version opened by the editor."""


def fingerprint(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_note(path: Path) -> tuple[str, str]:
    data = Path(path).read_bytes()
    return data.decode("utf-8-sig"), fingerprint(data)


def new_note_path(notes_dir: Path) -> Path:
    notes_dir.mkdir(parents=True, exist_ok=True)
    while True:
        path = notes_dir / f"n_{uuid4().hex}.md"
        if not path.exists():
            return path


def _sync_directory(directory: Path) -> None:
    if os.name != "posix":
        return
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def save_note(path: Path, text: str, expected_hash: str | None, recovery_dir: Path, *, max_copies: int = 10) -> str:
    """Write atomically; check disk fingerprint; retain bounded old versions.

    expected_hash=None means create a new file, and refuses to overwrite one.
    Caller must not silently retry on ExternalChangeError.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    previous = path.read_bytes() if path.exists() else None
    if expected_hash is None:
        if previous is not None:
            raise ExternalChangeError(f"File already exists: {path}")
    elif previous is None or fingerprint(previous) != expected_hash:
        raise ExternalChangeError(f"File changed outside the editor: {path}")
    encoded = text.encode("utf-8")
    if previous == encoded:
        return fingerprint(encoded)

    # A recoverable copy is written before replacing an existing file.
    if previous is not None:
        recovery_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = recovery_dir / f"{path.stem}.{stamp}.{uuid4().hex[:8]}.md"
        with backup.open("xb") as out:
            out.write(previous)
            out.flush()
            os.fsync(out.fileno())
        _sync_directory(recovery_dir)

    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        if previous is not None:
            os.fchmod(fd, path.stat().st_mode & 0o777)
        with os.fdopen(fd, "wb") as out:
            out.write(encoded)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp_name, path)
        _sync_directory(path.parent)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)

    if max_copies > 0 and recovery_dir.exists():
        copies = sorted(recovery_dir.glob(f"{path.stem}.*.md"), reverse=True)
        for old in copies[max_copies:]:
            old.unlink()
    return fingerprint(encoded)


def preserve_unsaved_copy(path: Path, text: str, recovery_dir: Path) -> Path:
    """Save editor text separately without modifying an externally changed original."""
    recovery_dir.mkdir(parents=True, exist_ok=True)
    target = recovery_dir / f"{path.stem}.unsaved-{uuid4().hex}.md"
    with target.open("x", encoding="utf-8", newline="\n") as out:
        out.write(text)
        out.flush()
        os.fsync(out.fileno())
    return target
