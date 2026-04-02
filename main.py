"""
Stem Separator API — python-audio-separator + FastAPI
Pipeline completo: separación → backing vocals → de-reverb/de-echo
"""
import shutil
import uuid
import logging
from pathlib import Path
from typing import Annotated

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
APP_DIR = Path("/app")
MODELS_EXPLORER_HTML = APP_DIR / "models-explorer.html"
MODELS_EXPLORER_CSS = APP_DIR / "models-explorer.css"
MODELS_EXPLORER_JS = APP_DIR / "models-explorer.js"
MODELS_EXPLORER_JSON = APP_DIR / "models.json"

for d in [INPUT_DIR, OUTPUT_DIR, MODEL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

MODELS = {
    # Vocales principales / acapella
    "kim_vocals": "vocals_mel_band_roformer.ckpt",
    "big_beta4": "melband_roformer_big_beta4.ckpt",
    "big_beta5e": "melband_roformer_big_beta5e.ckpt",
    "big_syhft_v1": "MelBandRoformerBigSYHFTV1.ckpt",
    "kim_ft": "mel_band_roformer_kim_ft_unwa.ckpt",
    "kim_ft2": "mel_band_roformer_kim_ft2_unwa.ckpt",
    "kim_ft2_bleedless": "mel_band_roformer_kim_ft2_bleedless_unwa.ckpt",
    "bs_roformer": "model_bs_roformer_ep_317_sdr_12.9755.ckpt",
    "bs_roformer_1296": "model_bs_roformer_ep_368_sdr_12.9628.ckpt",
    "mel_roformer": "model_mel_band_roformer_ep_3005_sdr_11.4360.ckpt",

    # Instrumental
    "inst_duality_v2": "melband_roformer_instvox_duality_v2.ckpt",
    "inst_duality_v1": "melband_roformer_instvoc_duality_v1.ckpt",
    "inst_v2": "melband_roformer_inst_v2.ckpt",
    "inst_v1": "melband_roformer_inst_v1.ckpt",
    "inst_v1e": "melband_roformer_inst_v1e.ckpt",
    "inst_bleedless_v1": "mel_band_roformer_instrumental_bleedless_v1_gabox.ckpt",
    "inst_bleedless_v2": "mel_band_roformer_instrumental_bleedless_v2_gabox.ckpt",
    "inst_bleedless_v3": "mel_band_roformer_instrumental_bleedless_v3_gabox.ckpt",
    "inst_fullness_v3": "mel_band_roformer_instrumental_fullness_v3_gabox.ckpt",
    "inst_instv8": "mel_band_roformer_instrumental_instv8_gabox.ckpt",
    "mdx23c_instvoc_hq2": "MDX23C-8KFFT-InstVoc_HQ_2.ckpt",
    "mdx23c_instvoc_hq": "MDX23C-8KFFT-InstVoc_HQ.ckpt",
    "bs_resurrection_inst": "bs_roformer_instrumental_resurrection_unwa.ckpt",

    # Karaoke / backing vocals
    "mel_karaoke": "mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt",
    "mel_karaoke_gabox": "mel_band_roformer_karaoke_gabox.ckpt",
    "mel_karaoke_gabox_v2": "mel_band_roformer_karaoke_gabox_v2.ckpt",
    "mel_karaoke_becruily": "mel_band_roformer_karaoke_becruily.ckpt",

    # Backing vocals extractor
    "bve_1": "UVR-BVE-4B_SN-44100-1.pth",
    "bve_2": "UVR-BVE-4B_SN-44100-2.pth",

    # Coros / masculino-femenino
    "chorus_male_female": "model_chorus_bs_roformer_ep_267_sdr_24.1275.ckpt",
    "male_female_aufr33": "bs_roformer_male_female_by_aufr33_sdr_7.2889.ckpt",

    # Multi-stem 4 pistas
    "htdemucs_ft": "htdemucs_ft.yaml",
    "htdemucs": "htdemucs.yaml",
    "hdemucs_mmi": "hdemucs_mmi.yaml",

    # Multi-stem 6 pistas
    "htdemucs_6s": "htdemucs_6s.yaml",

    # Bateria detallada
    "drumsep": "MDX23C-DrumSep-aufr33-jarredou.ckpt",

    # Drum-bass
    "drum_bass_sep": "model_bs_roformer_ep_937_sdr_10.5309.ckpt",

    # Vientos
    "woodwinds": "17_HP-Wind_Inst-UVR.pth",

    # De-reverb
    "dereverb_mel": "dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt",
    "dereverb_mel_la": "dereverb_mel_band_roformer_less_aggressive_anvuew_sdr_18.8050.ckpt",
    "dereverb_mel_mono": "dereverb_mel_band_roformer_mono_anvuew.ckpt",
    "dereverb_mel_big": "dereverb_big_mbr_ep_362.ckpt",
    "dereverb_mel_sbig": "dereverb_super_big_mbr_ep_346.ckpt",
    "dereverb_bs": "deverb_bs_roformer_8_384dim_10depth.ckpt",
    "dereverb_vr": "UVR-De-Reverb-aufr33-jarredou.pth",
    "dereverb_mdx23c": "MDX23C-De-Reverb-aufr33-jarredou.ckpt",

    # De-reverb + de-echo
    "dereverb_echo": "dereverb-echo_mel_band_roformer_sdr_13.4843_v2.ckpt",
    "dereverb_echo_fused": "dereverb_echo_mbr_fused.ckpt",
    "dereverb_echo_v1": "dereverb-echo_mel_band_roformer_sdr_10.0169.ckpt",
    "deecho_dereverb_vr": "UVR-DeEcho-DeReverb.pth",

    # De-echo
    "deecho_aggressive": "UVR-De-Echo-Aggressive.pth",
    "deecho_normal": "UVR-De-Echo-Normal.pth",
    "reverb_hq": "Reverb_HQ_By_FoxJoy.onnx",

    # De-noise
    "denoise": "UVR-DeNoise.pth",
    "denoise_lite": "UVR-DeNoise-Lite.pth",
    "denoise_mel_aufr33": "denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt",
    "denoise_mel_aggr": "denoise_mel_band_roformer_aufr33_aggr_sdr_27.9768.ckpt",

    # Crowd / audiencia
    "crowd_mel": "mel_band_roformer_crowd_aufr33_viperx_sdr_8.7144.ckpt",
    "crowd_mdx": "UVR-MDX-NET_Crowd_HQ_1.onnx",

    # Aspiracion / breath
    "aspiration": "aspiration_mel_band_roformer_sdr_18.9845.ckpt",
    "aspiration_la": "aspiration_mel_band_roformer_less_aggr_sdr_18.1201.ckpt",

    # Bleed suppressor
    "bleed_suppressor": "mel_band_roformer_bleed_suppressor_v1.ckpt",

    # Resurrection
    "vocals_resurrection": "bs_roformer_vocals_resurrection_unwa.ckpt",
    "vocals_revive": "bs_roformer_vocals_revive_unwa.ckpt",
}

VALID_OUTPUT_FORMATS = {"wav", "flac", "mp3"}
GUITAR_SOURCE_MODELS = {"htdemucs_6s"}
GUITAR_DEREVERB_MODELS = {
    "dereverb_mel",
    "dereverb_mel_la",
    "dereverb_mel_mono",
    "dereverb_mel_big",
    "dereverb_mel_sbig",
    "dereverb_bs",
    "dereverb_vr",
    "dereverb_mdx23c",
    "dereverb_echo",
    "dereverb_echo_fused",
    "dereverb_echo_v1",
    "deecho_dereverb_vr",
}
VOCAL_RECONSTRUCT_MODELS = {"vocals_resurrection", "vocals_revive"}
VOCAL_GENDER_SPLIT_MODELS = {"chorus_male_female", "male_female_aufr33"}

jobs: dict = {}


def make_separator(output_dir: Path):
    from audio_separator.separator import Separator
    return Separator(
        output_dir=str(output_dir),
        output_format="wav",
        model_file_dir=str(MODEL_DIR),
        use_autocast=True,
    )


def validate_output_format(output_format: str):
    if output_format not in VALID_OUTPUT_FORMATS:
        allowed = ", ".join(sorted(VALID_OUTPUT_FORMATS))
        raise HTTPException(400, f"output_format debe ser: {allowed}")


def validate_model_key(field_name: str, model_key: str, allowed_models: set[str] | None = None):
    if model_key not in MODELS:
        raise HTTPException(400, f"{field_name} inválido. Opciones: {list(MODELS.keys())}")
    if allowed_models and model_key not in allowed_models:
        raise HTTPException(400, f"{field_name} inválido para este endpoint. Opciones: {sorted(allowed_models)}")


def find_stem(stems: dict, preferred_keys: list[str]) -> Path | None:
    for key in preferred_keys:
        path = stems.get(key)
        if path and path.exists():
            return path
    return None


def require_stem(stems: dict, preferred_keys: list[str], message_prefix: str) -> Path:
    path = find_stem(stems, preferred_keys)
    if path:
        return path
    raise FileNotFoundError(f"{message_prefix}. Stems: {list(stems.keys())}")


def classify_stem(name: str) -> str | None:
    n = name.lower()
    patterns = [
        ("guitar", ("guitar", "gtr")),
        ("drums", ("drum", "perc")),
        ("bass", ("bass",)),
        ("piano", ("piano", "keys")),
        ("other", ("other", "rest")),
        ("female", ("female", "femme")),
        ("male", ("male", "masc")),
        ("instrumental", ("instrumental",)),
        ("backing", ("backing", "no_vocals", "novocal")),
        ("dry", ("dry", "no_reverb", "norev")),
        ("reverb", ("reverb", "wet")),
        ("vocals", ("vocal", "voice")),
    ]
    for stem_key, tokens in patterns:
        if any(token in n for token in tokens):
            return stem_key
    return None


def rename_stems(step_dir: Path, prefix: str) -> dict:
    """Busca audios de salida en step_dir y los renombra a nombres cortos predecibles."""
    all_audio = []
    for ext in ("wav", "flac", "mp3"):
        all_audio.extend(step_dir.glob(f"*.{ext}"))

    logger.info(f"[rename_stems] audios en {step_dir}: {[f.name for f in all_audio]}")

    renamed = {}
    for src in all_audio:
        key = classify_stem(src.name) or f"stem{len(renamed)}"
        dst = step_dir / f"{prefix}_{key}{src.suffix}"
        if dst.exists() and dst != src:
            dst = step_dir / f"{prefix}_{key}_{src.stem[-6:]}{src.suffix}"
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
        sep.separate(str(file_path))
        stems = rename_stems(job_out, "s1")
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
        sep.separate(str(file_path))
        step1_stems = rename_stems(step_dirs[1], "s1")
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
        sep.separate(str(vocals_path))
        step2_stems = rename_stems(step_dirs[2], "s2")
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
        sep.separate(str(lead_path))
        step3_stems = rename_stems(step_dirs[3], "s3")
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


def run_guitar_pipeline(job_id: str, file_path: Path, output_format: str,
                        split_model: str, dereverb_model: str):
    step_dirs = {i: OUTPUT_DIR / job_id / f"step{i}" for i in range(1, 3)}
    for d in step_dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    jobs[job_id]["status"] = "processing"
    jobs[job_id]["pipeline"] = {}

    try:
        sep = make_separator(step_dirs[1])
        sep.output_format = output_format

        # Paso 1: separar guitarra del mix
        jobs[job_id]["pipeline"]["step1"] = "running"
        sep.load_model(MODELS[split_model])
        sep.separate(str(file_path))
        step1_stems = rename_stems(step_dirs[1], "s1")
        jobs[job_id]["pipeline"]["step1"] = {k: v.name for k, v in step1_stems.items()}

        guitar_raw_path = require_stem(
            step1_stems,
            ["guitar"],
            "No se encontró stem guitar en paso 1",
        )
        other_ref_path = find_stem(step1_stems, ["other"])

        # Paso 2: limpiar reverb de la guitarra
        jobs[job_id]["pipeline"]["step2"] = "running"
        sep.output_dir = str(step_dirs[2])
        sep.load_model(MODELS[dereverb_model])
        sep.separate(str(guitar_raw_path))
        step2_stems = rename_stems(step_dirs[2], "s2")
        jobs[job_id]["pipeline"]["step2"] = {k: v.name for k, v in step2_stems.items()}

        guitar_clean_path = find_stem(step2_stems, ["dry", "guitar", "vocals", "instrumental"])
        if not guitar_clean_path and step2_stems:
            guitar_clean_path = next(iter(step2_stems.values()))
        if not guitar_clean_path:
            raise FileNotFoundError(
                f"No se encontró stem limpio en paso 2. Stems: {list(step2_stems.keys())}"
            )

        jobs[job_id]["status"] = "done"
        jobs[job_id]["summary"] = {
            "guitar_raw": guitar_raw_path.name,
            "guitar_clean": guitar_clean_path.name,
            "other_reference": other_ref_path.name if other_ref_path else None,
        }
        jobs[job_id]["download_base"] = f"/download/{job_id}"

    except Exception as e:
        logger.error(f"[{job_id}] Guitar pipeline error: {e}")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
    finally:
        file_path.unlink(missing_ok=True)


def run_vocals_reconstruct(job_id: str, file_path: Path, output_format: str,
                           extract_model: str, reconstruct_model: str):
    step_dirs = {i: OUTPUT_DIR / job_id / f"step{i}" for i in range(1, 3)}
    for d in step_dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    jobs[job_id]["status"] = "processing"
    jobs[job_id]["pipeline"] = {}

    try:
        sep = make_separator(step_dirs[1])
        sep.output_format = output_format

        # Paso 1: extraer vocal principal
        jobs[job_id]["pipeline"]["step1"] = "running"
        sep.load_model(MODELS[extract_model])
        sep.separate(str(file_path))
        step1_stems = rename_stems(step_dirs[1], "s1")
        jobs[job_id]["pipeline"]["step1"] = {k: v.name for k, v in step1_stems.items()}

        vocals_path = require_stem(
            step1_stems,
            ["vocals"],
            "No se encontró stem vocals en paso 1",
        )

        # Paso 2: reconstruir/recuperar voces
        jobs[job_id]["pipeline"]["step2"] = "running"
        sep.output_dir = str(step_dirs[2])
        sep.load_model(MODELS[reconstruct_model])
        sep.separate(str(vocals_path))
        step2_stems = rename_stems(step_dirs[2], "s2")
        jobs[job_id]["pipeline"]["step2"] = {k: v.name for k, v in step2_stems.items()}

        vocals_rebuilt_path = find_stem(step2_stems, ["vocals", "dry"])
        if not vocals_rebuilt_path and step2_stems:
            vocals_rebuilt_path = next(iter(step2_stems.values()))
        if not vocals_rebuilt_path:
            raise FileNotFoundError(
                f"No se encontró stem reconstruido en paso 2. Stems: {list(step2_stems.keys())}"
            )

        jobs[job_id]["status"] = "done"
        jobs[job_id]["summary"] = {
            "vocals_raw": vocals_path.name,
            "vocals_reconstructed": vocals_rebuilt_path.name,
            "instrumental_reference": step1_stems.get("instrumental").name if step1_stems.get("instrumental") else None,
        }
        jobs[job_id]["download_base"] = f"/download/{job_id}"

    except Exception as e:
        logger.error(f"[{job_id}] Vocals reconstruct error: {e}")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
    finally:
        file_path.unlink(missing_ok=True)


def run_vocals_gender_split(job_id: str, file_path: Path, output_format: str,
                            extract_model: str, split_model: str):
    step_dirs = {i: OUTPUT_DIR / job_id / f"step{i}" for i in range(1, 3)}
    for d in step_dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    jobs[job_id]["status"] = "processing"
    jobs[job_id]["pipeline"] = {}

    try:
        sep = make_separator(step_dirs[1])
        sep.output_format = output_format

        # Paso 1: extraer vocal principal
        jobs[job_id]["pipeline"]["step1"] = "running"
        sep.load_model(MODELS[extract_model])
        sep.separate(str(file_path))
        step1_stems = rename_stems(step_dirs[1], "s1")
        jobs[job_id]["pipeline"]["step1"] = {k: v.name for k, v in step1_stems.items()}

        vocals_path = require_stem(
            step1_stems,
            ["vocals"],
            "No se encontró stem vocals en paso 1",
        )

        # Paso 2: split hombre / mujer
        jobs[job_id]["pipeline"]["step2"] = "running"
        sep.output_dir = str(step_dirs[2])
        sep.load_model(MODELS[split_model])
        sep.separate(str(vocals_path))
        step2_stems = rename_stems(step_dirs[2], "s2")
        jobs[job_id]["pipeline"]["step2"] = {k: v.name for k, v in step2_stems.items()}

        male_path = find_stem(step2_stems, ["male"])
        female_path = find_stem(step2_stems, ["female"])

        if not male_path and not female_path:
            raise FileNotFoundError(
                f"No se encontraron stems male/female en paso 2. Stems: {list(step2_stems.keys())}"
            )

        jobs[job_id]["status"] = "done"
        jobs[job_id]["summary"] = {
            "vocals_raw": vocals_path.name,
            "male_vocals": male_path.name if male_path else None,
            "female_vocals": female_path.name if female_path else None,
        }
        jobs[job_id]["download_base"] = f"/download/{job_id}"

    except Exception as e:
        logger.error(f"[{job_id}] Vocals male/female error: {e}")
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
        "guitar_pipeline_default": {"step1": "htdemucs_6s", "step2": "dereverb_mel"},
        "vocals_reconstruct_default": {"step1": "mel_roformer", "step2": "vocals_resurrection"},
        "vocals_male_female_default": {"step1": "mel_roformer", "step2": "chorus_male_female"},
    }


def serve_asset_file(path: Path, media_type: str):
    if not path.exists():
        raise HTTPException(404, f"Archivo no encontrado: {path.name}")
    return FileResponse(str(path), media_type=media_type)


@app.get(
    "/models-explorer",
    include_in_schema=False,
    responses={404: {"description": "Archivo no encontrado"}},
)
def models_explorer_page():
    return serve_asset_file(MODELS_EXPLORER_HTML, "text/html")


@app.get(
    "/models-explorer.html",
    include_in_schema=False,
    responses={404: {"description": "Archivo no encontrado"}},
)
def models_explorer_page_alias():
    return models_explorer_page()


@app.get(
    "/models-explorer.css",
    include_in_schema=False,
    responses={404: {"description": "Archivo no encontrado"}},
)
def models_explorer_css():
    return serve_asset_file(MODELS_EXPLORER_CSS, "text/css")


@app.get(
    "/models-explorer.js",
    include_in_schema=False,
    responses={404: {"description": "Archivo no encontrado"}},
)
def models_explorer_js():
    return serve_asset_file(MODELS_EXPLORER_JS, "application/javascript")


@app.get(
    "/models.json",
    include_in_schema=False,
    responses={404: {"description": "Archivo no encontrado"}},
)
def models_explorer_data():
    return serve_asset_file(MODELS_EXPLORER_JSON, "application/json")


@app.post(
    "/separate",
    summary="Separar con un modelo (asíncrono)",
    responses={400: {"description": "Parámetros inválidos"}},
)
async def separate(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(..., description="Archivo de audio (mp3, wav, flac)")],
    model: Annotated[str, Form(description="Modelo a usar")] = "mel_roformer",
    output_format: Annotated[str, Form(description="Formato salida: wav, flac, mp3")] = "wav",
):
    validate_model_key("model", model)
    validate_output_format(output_format)
    job_id = str(uuid.uuid4())
    dest = INPUT_DIR / f"{job_id}.wav"
    with dest.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)
    jobs[job_id] = {"status": "queued", "model": model, "type": "single", "files": {}}
    background_tasks.add_task(run_separation, job_id, dest, model, output_format)
    return {"job_id": job_id, "status": "queued", "model": model}


@app.post(
    "/separate/pipeline",
    summary="Pipeline 3 pasos: stem → backing → de-reverb",
    responses={400: {"description": "Parámetros inválidos"}},
)
async def separate_pipeline(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(..., description="Archivo de audio (mp3, wav, flac)")],
    step1_model: Annotated[str, Form(description="Paso 1 — vocal/instrumental")] = "mel_roformer",
    step2_model: Annotated[str, Form(description="Paso 2 — lead vs backing vocals")] = "mel_karaoke",
    step3_model: Annotated[str, Form(description="Paso 3 — de-reverb/de-echo")] = "dereverb_mel",
    output_format: Annotated[str, Form(description="Formato salida: wav, flac, mp3")] = "wav",
):
    validate_output_format(output_format)
    validate_model_key("step1_model", step1_model)
    validate_model_key("step2_model", step2_model)
    validate_model_key("step3_model", step3_model)
    job_id = str(uuid.uuid4())
    dest = INPUT_DIR / f"{job_id}.wav"
    with dest.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)
    jobs[job_id] = {"status": "queued", "type": "pipeline", "pipeline": {}}
    background_tasks.add_task(run_pipeline, job_id, dest, output_format,
                               step1_model, step2_model, step3_model)
    return {"job_id": job_id, "status": "queued",
            "pipeline": {"step1": step1_model, "step2": step2_model, "step3": step3_model}}


@app.post(
    "/separate/guitar/pipeline",
    summary="Separar guitarra + limpiar reverb",
    responses={400: {"description": "Parámetros inválidos"}},
)
async def separate_guitar_pipeline(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(..., description="Archivo de audio (mp3, wav, flac)")],
    split_model: Annotated[str, Form(description="Modelo para extraer guitarra")] = "htdemucs_6s",
    dereverb_model: Annotated[str, Form(description="Modelo para limpiar reverb en guitarra")] = "dereverb_mel",
    output_format: Annotated[str, Form(description="Formato salida: wav, flac, mp3")] = "wav",
):
    validate_output_format(output_format)
    validate_model_key("split_model", split_model, GUITAR_SOURCE_MODELS)
    validate_model_key("dereverb_model", dereverb_model, GUITAR_DEREVERB_MODELS)

    job_id = str(uuid.uuid4())
    dest = INPUT_DIR / f"{job_id}.wav"
    with dest.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)

    jobs[job_id] = {
        "status": "queued",
        "type": "guitar_pipeline",
        "pipeline": {},
        "models": {"split_model": split_model, "dereverb_model": dereverb_model},
    }
    background_tasks.add_task(run_guitar_pipeline, job_id, dest, output_format, split_model, dereverb_model)

    return {
        "job_id": job_id,
        "status": "queued",
        "pipeline": {"step1": split_model, "step2": dereverb_model},
    }


@app.post(
    "/separate/vocals/reconstruct",
    summary="Reconstruir voces",
    responses={400: {"description": "Parámetros inválidos"}},
)
async def separate_vocals_reconstruct(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(..., description="Archivo de audio (mp3, wav, flac)")],
    extract_model: Annotated[str, Form(description="Modelo para extraer vocal principal")] = "mel_roformer",
    reconstruct_model: Annotated[str, Form(description="Modelo para reconstruir voces")] = "vocals_resurrection",
    output_format: Annotated[str, Form(description="Formato salida: wav, flac, mp3")] = "wav",
):
    validate_output_format(output_format)
    validate_model_key("extract_model", extract_model)
    validate_model_key("reconstruct_model", reconstruct_model, VOCAL_RECONSTRUCT_MODELS)

    job_id = str(uuid.uuid4())
    dest = INPUT_DIR / f"{job_id}.wav"
    with dest.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)

    jobs[job_id] = {
        "status": "queued",
        "type": "vocals_reconstruct",
        "pipeline": {},
        "models": {"extract_model": extract_model, "reconstruct_model": reconstruct_model},
    }
    background_tasks.add_task(
        run_vocals_reconstruct,
        job_id,
        dest,
        output_format,
        extract_model,
        reconstruct_model,
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "pipeline": {"step1": extract_model, "step2": reconstruct_model},
    }


@app.post(
    "/separate/vocals/male-female",
    summary="Separar voces por hombre/mujer",
    responses={400: {"description": "Parámetros inválidos"}},
)
async def separate_vocals_male_female(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(..., description="Archivo de audio (mp3, wav, flac)")],
    extract_model: Annotated[str, Form(description="Modelo para extraer vocal principal")] = "mel_roformer",
    split_model: Annotated[str, Form(description="Modelo para split hombre/mujer")] = "chorus_male_female",
    output_format: Annotated[str, Form(description="Formato salida: wav, flac, mp3")] = "wav",
):
    validate_output_format(output_format)
    validate_model_key("extract_model", extract_model)
    validate_model_key("split_model", split_model, VOCAL_GENDER_SPLIT_MODELS)

    job_id = str(uuid.uuid4())
    dest = INPUT_DIR / f"{job_id}.wav"
    with dest.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)

    jobs[job_id] = {
        "status": "queued",
        "type": "vocals_male_female",
        "pipeline": {},
        "models": {"extract_model": extract_model, "split_model": split_model},
    }
    background_tasks.add_task(
        run_vocals_gender_split,
        job_id,
        dest,
        output_format,
        extract_model,
        split_model,
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "pipeline": {"step1": extract_model, "step2": split_model},
    }


@app.get(
    "/jobs/{job_id}",
    summary="Estado de un job",
    responses={404: {"description": "Job no encontrado"}},
)
def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job no encontrado")
    return jobs[job_id]


@app.get("/jobs", summary="Listar todos los jobs")
def list_jobs():
    return {"total": len(jobs), "jobs": {jid: j["status"] for jid, j in jobs.items()}}


@app.get(
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


@app.delete(
    "/jobs/{job_id}",
    summary="Eliminar job y sus archivos",
    responses={404: {"description": "Job no encontrado"}},
)
def delete_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job no encontrado")
    job_dir = OUTPUT_DIR / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir)
    del jobs[job_id]
    return {"deleted": job_id}