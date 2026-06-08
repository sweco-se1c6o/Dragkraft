from __future__ import annotations

import base64
import binascii
import hashlib
import re
from pathlib import Path


DEFAULT_UPLOAD_DIR = Path("runs/dashboard/uploads")
EXCEL_SUFFIXES = {".xlsx", ".xlsm", ".xltx", ".xltm"}


class UploadError(ValueError):
    """Raised when an uploaded workbook cannot be saved safely."""


def save_uploaded_workbook(
    *,
    contents: str,
    filename: str | None,
    upload_dir: str | Path = DEFAULT_UPLOAD_DIR,
) -> Path:
    source_name = filename or "uploaded.xlsx"
    suffix = Path(source_name).suffix.lower()
    if suffix not in EXCEL_SUFFIXES:
        raise UploadError("Upload an Excel workbook with .xlsx, .xlsm, .xltx, or .xltm")

    try:
        _, encoded = contents.split(",", 1)
        payload = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise UploadError("Invalid upload payload") from exc

    digest = hashlib.sha256(payload).hexdigest()[:12]
    safe_stem = _safe_stem(Path(source_name).stem)
    target_dir = Path(upload_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{safe_stem}-{digest}{suffix}"
    path.write_bytes(payload)
    return path


def _safe_stem(stem: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem).strip("._")
    return cleaned or "uploaded"
