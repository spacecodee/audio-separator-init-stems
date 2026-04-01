"""
Stem Separator API — python-audio-separator + FastAPI
Pipeline completo: separación → backing vocals → de-reverb/de-echo
"""
import os
import shutil
import uuid
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.openapi.utils import get_openapi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Stem Separator API",
    description="Separación de stems con UVR5 / MelBand-RoFormer en GPU NVIDIA",
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
)

INPUT_DIR  = Path("/app/input")
OUTPUT_DIR = Path("/app/output")
MODEL_DIR  = Path("/root/.cache/audio-separator")

for d in [INPUT_DIR, OUTPUT_DIR, MODEL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

MODELS = {
    "mel_roformer":         "model_mel_band_roformer_ep_3005_sdr_11.4360.ckpt",
    "bs_roformer":          "model_bs_roformer_ep_317_sdr_12.9755.ckpt",
    "htdemucs_6s":          "htdemucs_6s.yaml",
    "htdemucs_4s":          "htdemucs.yaml",
    "mel_karaoke":          "mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt",
    "mel_karaoke_gabox":    "mel_band_roformer_karaoke_gabox.ckpt",
    "mel_karaoke_becruily": "mel_band_roformer_karaoke_becruily.ckpt",
    "dereverb_mel":         "dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt",
    "dereverb_mel_la":      "dereverb_mel_band_roformer_less_aggressive_anvuew_sdr_18.8050.ckpt",
    "dereverb_echo":        "dereverb-echo_mel_band_roformer_sdr_13.4843_v2.ckpt",
    "dereverb_bs":          "deverb_bs_roformer_8_384dim_10depth.ckpt",
    "dereverb_vr":          "UVR-De-Reverb-aufr33-jarredou.pth",
}

jobs: dict = {}


def make_separator(output_dir: Path):
    from audio_separator.separator import Separator
    return Separator(
        output_dir=str(output_dir),
        output_format="wav",
        model_file_dir=str(MODEL_DIR),
        use_autocast=True,
    )


def classify_stem(name: str) -> str:
    n = name.lower()
    if "instrumental" in n:
        return "instrumental"
    if "backing" in n or "no_vocals" in n or "novocal" in n:
        return "backing"
    if "dry" in n or "no_reverb" in n or "norev" in n:
        return "dry"
    if "reverb" in n or "wet" in n:
        return "reverb"
    if "vocal" in n or "voice" in n:
        return "vocals"
    return None


def rename_stems(files: list, step_dir: Path, prefix: str) -> dict:
    """Busca TODOS los wav en step_dir y los renombra a nombres cortos predecibles."""
    all_wavs = list(step_dir.glob("*.wav"))
    logger.info(f"[rename_stems] WAVs en {step_dir}: {[f.name for f in all_wavs]}")

    renamed = {}
    for src in all_wavs:
        key = classify_stem(src.name) or f"stem{len(renamed)}"
        dst = step_dir / f"{prefix}_{key}.wav"
        if dst.exists() and dst != src:
            dst = step_dir / f"{prefix}_{key}_{src.stem[-6:]}.wav"
        src.rename(dst)
        renamed[key] = dst
        logger.info(f"  {src.name} → {dst.name}")

    return renamed


def run_separation(job_id: str, file_path: Path, model_key: str, output_format: str):
    job_out = OUTPUT_DIR / job_id / "step1"
    job_out.mkdir(parents=True, exist_ok=True)
    try:
        jobs[job_id]["status"] = "processing"
        sep = make_separator(job_out)
        sep.output_format = output_format
        sep.load_model(MODELS.get(model_key, MODELS["mel_roformer"]))
        result = sep.separate(str(file_path))
        stems = rename_stems(result, job_out, "s1")
        jobs[job_id]["status"] = "done"
        jobs[job_id]["files"] = {k: v.name for k, v in stems.items()}
    except Exception as e:
        logger.error(f"[{job_id}] Error: {e}")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
    finally:
        file_path.unlink(missing_ok=True)


def run_pipeline(job_id: str, file_path: Path, output_format: str,
                 step1_model: str, step2_model: str, step3_model: str):
    step_dirs = {i: OUTPUT_DIR / job_id / f"step{i}" for i in range(1, 4)}
    for d in step_dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    jobs[job_id]["status"] = "processing"
    jobs[job_id]["pipeline"] = {}

    try:
        sep = make_separator(step_dirs[1])
        sep.output_format = output_format

        # Paso 1: vocal vs instrumental
        jobs[job_id]["pipeline"]["step1"] = "running"
        sep.load_model(MODELS[step1_model])
        step1_out = sep.separate(str(file_path))
        step1_stems = rename_stems(step1_out, step_dirs[1], "s1")
        jobs[job_id]["pipeline"]["step1"] = {k: v.name for k, v in step1_stems.items()}

        vocals_path = step1_stems.get("vocals")
        if not vocals_path or not vocals_path.exists():
            raise FileNotFoundError(
                f"No se encontró stem vocals en paso 1. Stems: {list(step1_stems.keys())}"
            )

        # Paso 2: lead vocals vs backing
        jobs[job_id]["pipeline"]["step2"] = "running"
        sep.output_dir = str(step_dirs[2])
        sep.load_model(MODELS[step2_model])
        step2_out = sep.separate(str(vocals_path))
        step2_stems = rename_stems(step2_out, step_dirs[2], "s2")
        jobs[job_id]["pipeline"]["step2"] = {k: v.name for k, v in step2_stems.items()}

        lead_path = step2_stems.get("vocals")
        if not lead_path or not lead_path.exists():
            raise FileNotFoundError(
                f"No se encontró lead vocals en paso 2. Stems: {list(step2_stems.keys())}"
            )

        # Paso 3: de-reverb / de-echo
        jobs[job_id]["pipeline"]["step3"] = "running"
        sep.output_dir = str(step_dirs[3])
        sep.load_model(MODELS[step3_model])
        step3_out = sep.separate(str(lead_path))
        step3_stems = rename_stems(step3_out, step_dirs[3], "s3")
        jobs[job_id]["pipeline"]["step3"] = {k: v.name for k, v in step3_stems.items()}

        jobs[job_id]["status"] = "done"
        jobs[job_id]["summary"] = {
            "instrumental":     jobs[job_id]["pipeline"]["step1"].get("instrumental"),
            "backing_vocals":   jobs[job_id]["pipeline"]["step2"].get("backing"),
            "lead_vocal_clean": jobs[job_id]["pipeline"]["step3"].get("dry")
                                or jobs[job_id]["pipeline"]["step3"].get("vocals"),
        }
        jobs[job_id]["download_base"] = f"/download/{job_id}"

    except Exception as e:
        logger.error(f"[{job_id}] Pipeline error: {e}")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
    finally:
        file_path.unlink(missing_ok=True)


def run_preload_models(models_to_download: list):
    from audio_separator.separator import Separator
    sep = Separator(output_dir="/tmp", model_file_dir=str(MODEL_DIR))
    for key in models_to_download:
        model_name = MODELS.get(key)
        if not model_name:
            continue
        try:
            logger.info(f"[preload] Descargando: {model_name}")
            sep.load_model(model_name)
            logger.info(f"[preload] OK: {model_name}")
        except Exception as e:
            logger.warning(f"[preload] Error {model_name}: {e}")


@app.on_event("startup")
async def preload_pipeline_models():
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_preload_models,
                               ["mel_roformer", "mel_karaoke", "dereverb_mel"])
    logger.info("Modelos del pipeline listos.")


SWAGGER_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Stem Separator API</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" type="text/css"
        href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css">
  <style>
    body { margin: 0; background: #fafafa; }
    .swagger-ui .topbar { display: none; }
    .swagger-ui input[type=file] {
      border: 2px dashed #1a7f64;
      border-radius: 6px;
      padding: 8px 12px;
      background: #f0faf7;
      cursor: pointer;
      width: 100%;
    }
    .swagger-ui input[type=file]:hover { background: #d8f3ec; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"></script>
  <script>
    window.onload = function() {
      SwaggerUIBundle({
        url: "/openapi.json",
        dom_id: "#swagger-ui",
        presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
        layout: "BaseLayout",
        deepLinking: true,
        tryItOutEnabled: true,
      });
    };
  </script>
</body>
</html>"""


@app.get("/docs", include_in_schema=False)
async def custom_swagger():
    return HTMLResponse(content=SWAGGER_HTML)


@app.get("/openapi.json", include_in_schema=False)
async def openapi_schema():
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )


@app.get("/", summary="Estado del servidor")
def root():
    return {"status": "ok", "version": "2.0.0", "message": "Stem Separator API activa"}


@app.get("/models", summary="Modelos disponibles")
def list_models():
    return {
        "models": list(MODELS.keys()),
        "pipeline_default": {"step1": "mel_roformer", "step2": "mel_karaoke", "step3": "dereverb_mel"},
    }


@app.post("/separate", summary="Separar con un modelo (asíncrono)")
async def separate(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Archivo de audio (mp3, wav, flac)"),
    model: str = Form(default="mel_roformer", description="Modelo a usar"),
    output_format: str = Form(default="wav", description="Formato salida: wav, flac, mp3"),
):
    if model not in MODELS:
        raise HTTPException(400, f"Modelo inválido. Opciones: {list(MODELS.keys())}")
    if output_format not in ("wav", "flac", "mp3"):
        raise HTTPException(400, "output_format debe ser wav, flac o mp3")
    job_id = str(uuid.uuid4())
    dest = INPUT_DIR / f"{job_id}.wav"
    with dest.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)
    jobs[job_id] = {"status": "queued", "model": model, "type": "single", "files": {}}
    background_tasks.add_task(run_separation, job_id, dest, model, output_format)
    return {"job_id": job_id, "status": "queued", "model": model}


@app.post("/separate/pipeline", summary="Pipeline 3 pasos: stem → backing → de-reverb")
async def separate_pipeline(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Archivo de audio (mp3, wav, flac)"),
    step1_model: str = Form(default="mel_roformer", description="Paso 1 — vocal/instrumental"),
    step2_model: str = Form(default="mel_karaoke",  description="Paso 2 — lead vs backing vocals"),
    step3_model: str = Form(default="dereverb_mel", description="Paso 3 — de-reverb/de-echo"),
    output_format: str = Form(default="wav",        description="Formato salida: wav, flac, mp3"),
):
    for key, val in [("step1_model", step1_model), ("step2_model", step2_model), ("step3_model", step3_model)]:
        if val not in MODELS:
            raise HTTPException(400, f"{key} inválido. Opciones: {list(MODELS.keys())}")
    job_id = str(uuid.uuid4())
    dest = INPUT_DIR / f"{job_id}.wav"
    with dest.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)
    jobs[job_id] = {"status": "queued", "type": "pipeline", "pipeline": {}}
    background_tasks.add_task(run_pipeline, job_id, dest, output_format,
                               step1_model, step2_model, step3_model)
    return {"job_id": job_id, "status": "queued",
            "pipeline": {"step1": step1_model, "step2": step2_model, "step3": step3_model}}


@app.get("/jobs/{job_id}", summary="Estado de un job")
def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job no encontrado")
    return jobs[job_id]


@app.get("/jobs", summary="Listar todos los jobs")
def list_jobs():
    return {"total": len(jobs), "jobs": {jid: j["status"] for jid, j in jobs.items()}}


@app.get("/download/{job_id}/{filename}", summary="Descargar stem resultante")
def download_file(job_id: str, filename: str):
    for step in ["step1", "step2", "step3"]:
        path = OUTPUT_DIR / job_id / step / filename
        if path.exists():
            return FileResponse(str(path), media_type="audio/wav", filename=filename)
    raise HTTPException(404, f"Archivo '{filename}' no encontrado en job '{job_id}'")


@app.delete("/jobs/{job_id}", summary="Eliminar job y sus archivos")
def delete_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job no encontrado")
    job_dir = OUTPUT_DIR / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir)
    del jobs[job_id]
    return {"deleted": job_id}