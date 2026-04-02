import shutil

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..config import OUTPUT_DIR
from ..store import job_store

router = APIRouter()


@router.get(
    "/jobs/{job_id}",
    summary="Estado de un job",
    responses={404: {"description": "Job no encontrado"}},
)
def get_job(job_id: str):
    if not job_store.exists(job_id):
        raise HTTPException(404, "Job no encontrado")
    return job_store.get(job_id)


@router.get("/jobs", summary="Listar todos los jobs")
def list_jobs():
    return {"total": len(job_store.jobs), "jobs": job_store.status_map()}


@router.get(
    "/download/{job_id}/{filename}",
    summary="Descargar stem resultante",
    responses={404: {"description": "Archivo no encontrado"}},
)
def download_file(job_id: str, filename: str):
    for step in ["step1", "step2", "step3"]:
        path = OUTPUT_DIR / job_id / step / filename
        if path.exists():
            return FileResponse(str(path), media_type="audio/wav", filename=filename)
    raise HTTPException(404, f"Archivo '{filename}' no encontrado en job '{job_id}'")


@router.delete(
    "/jobs/{job_id}",
    summary="Eliminar job y sus archivos",
    responses={404: {"description": "Job no encontrado"}},
)
def delete_job(job_id: str):
    if not job_store.exists(job_id):
        raise HTTPException(404, "Job no encontrado")
    job_dir = OUTPUT_DIR / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir)
    job_store.delete(job_id)
    return {"deleted": job_id}
