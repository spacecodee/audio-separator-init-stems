from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse

from .config import INPUT_DIR
from .store import job_store


def create_job_input(file: UploadFile) -> tuple[str, Path]:
    job_id = str(uuid.uuid4())
    dest = INPUT_DIR / f"{job_id}.wav"
    with dest.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)
    return job_id, dest


def create_job_with_input(file: UploadFile, payload: dict) -> tuple[str, Path]:
    job_id, dest = create_job_input(file)
    job_store.create(job_id, payload)
    return job_id, dest


def serve_asset_file(path: Path, media_type: str) -> FileResponse:
    if not path.exists():
        raise HTTPException(404, f"Archivo no encontrado: {path.name}")
    return FileResponse(str(path), media_type=media_type)
