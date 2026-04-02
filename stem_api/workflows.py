from __future__ import annotations

import logging
from pathlib import Path

from .audio import find_stem, make_separator, pick_clean_stem, rename_stems, require_stem
from .config import MODELS, OUTPUT_DIR
from .store import job_store

logger = logging.getLogger(__name__)

ERR_MISSING_VOCALS_STEP1 = "No se encontro stem vocals en paso 1"


def _set_job_error(job_id: str, label: str, error: Exception) -> None:
    logger.error("[%s] %s: %s", job_id, label, error)
    job = job_store.get(job_id)
    job["status"] = "error"
    job["error"] = str(error)


def _ensure_step_dirs(job_id: str, step_count: int) -> dict[int, Path]:
    step_dirs = {i: OUTPUT_DIR / job_id / f"step{i}" for i in range(1, step_count + 1)}
    for directory in step_dirs.values():
        directory.mkdir(parents=True, exist_ok=True)
    return step_dirs


def _run_step(separator, output_dir: Path, model_key: str, input_path: Path, prefix: str) -> dict:
    separator.output_dir = str(output_dir)
    separator.load_model(MODELS[model_key])
    separator.separate(str(input_path))
    return rename_stems(output_dir, prefix)


def _finalize_job_files(job_id: str, stems: dict) -> None:
    job = job_store.get(job_id)
    job["status"] = "done"
    job["files"] = {k: v.name for k, v in stems.items()}
    job["download_base"] = f"/download/{job_id}"


def run_separation(job_id: str, file_path: Path, model_key: str, output_format: str) -> None:
    step1_dir = OUTPUT_DIR / job_id / "step1"
    step1_dir.mkdir(parents=True, exist_ok=True)

    try:
        job = job_store.get(job_id)
        job["status"] = "processing"

        sep = make_separator(step1_dir)
        sep.output_format = output_format
        model_name = MODELS.get(model_key, MODELS["mel_roformer"])
        sep.load_model(model_name)
        sep.separate(str(file_path))

        stems = rename_stems(step1_dir, "s1")
        _finalize_job_files(job_id, stems)
    except Exception as error:
        _set_job_error(job_id, "Error", error)
    finally:
        file_path.unlink(missing_ok=True)


def run_effect_single(job_id: str, file_path: Path, model_key: str, output_format: str, error_label: str) -> None:
    step1_dir = OUTPUT_DIR / job_id / "step1"
    step1_dir.mkdir(parents=True, exist_ok=True)

    try:
        job = job_store.get(job_id)
        job["status"] = "processing"

        sep = make_separator(step1_dir)
        sep.output_format = output_format
        sep.load_model(MODELS[model_key])
        sep.separate(str(file_path))

        stems = rename_stems(step1_dir, "s1")
        clean_path = pick_clean_stem(stems)
        if not clean_path:
            raise FileNotFoundError(f"No se encontro stem limpio. Stems: {list(stems.keys())}")

        _finalize_job_files(job_id, stems)
        job["summary"] = {
            "clean_audio": clean_path.name,
            "clean_source": model_key,
        }
    except Exception as error:
        _set_job_error(job_id, error_label, error)
    finally:
        file_path.unlink(missing_ok=True)


def run_pipeline(job_id: str, file_path: Path, output_format: str, step1_model: str, step2_model: str, step3_model: str) -> None:
    step_dirs = _ensure_step_dirs(job_id, 3)
    job = job_store.get(job_id)
    job["status"] = "processing"
    job["pipeline"] = {}

    try:
        sep = make_separator(step_dirs[1])
        sep.output_format = output_format

        job["pipeline"]["step1"] = "running"
        step1_stems = _run_step(sep, step_dirs[1], step1_model, file_path, "s1")
        job["pipeline"]["step1"] = {k: v.name for k, v in step1_stems.items()}

        vocals_path = require_stem(step1_stems, ["vocals"], ERR_MISSING_VOCALS_STEP1)

        job["pipeline"]["step2"] = "running"
        step2_stems = _run_step(sep, step_dirs[2], step2_model, vocals_path, "s2")
        job["pipeline"]["step2"] = {k: v.name for k, v in step2_stems.items()}

        lead_path = require_stem(step2_stems, ["vocals"], "No se encontro lead vocals en paso 2")

        job["pipeline"]["step3"] = "running"
        step3_stems = _run_step(sep, step_dirs[3], step3_model, lead_path, "s3")
        job["pipeline"]["step3"] = {k: v.name for k, v in step3_stems.items()}

        _finalize_job_files(job_id, step3_stems)
        job["summary"] = {
            "instrumental": job["pipeline"]["step1"].get("instrumental"),
            "backing_vocals": job["pipeline"]["step2"].get("backing"),
            "lead_vocal_clean": job["pipeline"]["step3"].get("dry") or job["pipeline"]["step3"].get("vocals"),
        }
    except Exception as error:
        _set_job_error(job_id, "Pipeline error", error)
    finally:
        file_path.unlink(missing_ok=True)


def run_guitar_pipeline(job_id: str, file_path: Path, output_format: str, split_model: str, dereverb_model: str) -> None:
    step_dirs = _ensure_step_dirs(job_id, 2)
    job = job_store.get(job_id)
    job["status"] = "processing"
    job["pipeline"] = {}

    try:
        sep = make_separator(step_dirs[1])
        sep.output_format = output_format

        job["pipeline"]["step1"] = "running"
        step1_stems = _run_step(sep, step_dirs[1], split_model, file_path, "s1")
        job["pipeline"]["step1"] = {k: v.name for k, v in step1_stems.items()}

        guitar_raw_path = require_stem(step1_stems, ["guitar"], "No se encontro stem guitar en paso 1")
        other_ref_path = find_stem(step1_stems, ["other"])

        job["pipeline"]["step2"] = "running"
        step2_stems = _run_step(sep, step_dirs[2], dereverb_model, guitar_raw_path, "s2")
        job["pipeline"]["step2"] = {k: v.name for k, v in step2_stems.items()}

        guitar_clean_path = find_stem(step2_stems, ["dry", "guitar", "vocals", "instrumental"]) or pick_clean_stem(step2_stems)
        if not guitar_clean_path:
            raise FileNotFoundError(f"No se encontro stem limpio en paso 2. Stems: {list(step2_stems.keys())}")

        _finalize_job_files(job_id, step2_stems)
        job["summary"] = {
            "guitar_raw": guitar_raw_path.name,
            "guitar_clean": guitar_clean_path.name,
            "other_reference": other_ref_path.name if other_ref_path else None,
        }
    except Exception as error:
        _set_job_error(job_id, "Guitar pipeline error", error)
    finally:
        file_path.unlink(missing_ok=True)


def run_vocals_reconstruct(job_id: str, file_path: Path, output_format: str, extract_model: str, reconstruct_model: str) -> None:
    step_dirs = _ensure_step_dirs(job_id, 2)
    job = job_store.get(job_id)
    job["status"] = "processing"
    job["pipeline"] = {}

    try:
        sep = make_separator(step_dirs[1])
        sep.output_format = output_format

        job["pipeline"]["step1"] = "running"
        step1_stems = _run_step(sep, step_dirs[1], extract_model, file_path, "s1")
        job["pipeline"]["step1"] = {k: v.name for k, v in step1_stems.items()}

        vocals_path = require_stem(step1_stems, ["vocals"], ERR_MISSING_VOCALS_STEP1)

        job["pipeline"]["step2"] = "running"
        step2_stems = _run_step(sep, step_dirs[2], reconstruct_model, vocals_path, "s2")
        job["pipeline"]["step2"] = {k: v.name for k, v in step2_stems.items()}

        vocals_rebuilt_path = find_stem(step2_stems, ["vocals", "dry"]) or pick_clean_stem(step2_stems)
        if not vocals_rebuilt_path:
            raise FileNotFoundError(f"No se encontro stem reconstruido en paso 2. Stems: {list(step2_stems.keys())}")

        _finalize_job_files(job_id, step2_stems)
        job["summary"] = {
            "vocals_raw": vocals_path.name,
            "vocals_reconstructed": vocals_rebuilt_path.name,
            "instrumental_reference": step1_stems.get("instrumental").name if step1_stems.get("instrumental") else None,
        }
    except Exception as error:
        _set_job_error(job_id, "Vocals reconstruct error", error)
    finally:
        file_path.unlink(missing_ok=True)


def run_vocals_gender_split(job_id: str, file_path: Path, output_format: str, extract_model: str, split_model: str) -> None:
    step_dirs = _ensure_step_dirs(job_id, 2)
    job = job_store.get(job_id)
    job["status"] = "processing"
    job["pipeline"] = {}

    try:
        sep = make_separator(step_dirs[1])
        sep.output_format = output_format

        job["pipeline"]["step1"] = "running"
        step1_stems = _run_step(sep, step_dirs[1], extract_model, file_path, "s1")
        job["pipeline"]["step1"] = {k: v.name for k, v in step1_stems.items()}

        vocals_path = require_stem(step1_stems, ["vocals"], ERR_MISSING_VOCALS_STEP1)

        job["pipeline"]["step2"] = "running"
        step2_stems = _run_step(sep, step_dirs[2], split_model, vocals_path, "s2")
        job["pipeline"]["step2"] = {k: v.name for k, v in step2_stems.items()}

        male_path = find_stem(step2_stems, ["male"])
        female_path = find_stem(step2_stems, ["female"])
        if not male_path and not female_path:
            raise FileNotFoundError(f"No se encontraron stems male/female en paso 2. Stems: {list(step2_stems.keys())}")

        _finalize_job_files(job_id, step2_stems)
        job["summary"] = {
            "vocals_raw": vocals_path.name,
            "male_vocals": male_path.name if male_path else None,
            "female_vocals": female_path.name if female_path else None,
        }
    except Exception as error:
        _set_job_error(job_id, "Vocals male/female error", error)
    finally:
        file_path.unlink(missing_ok=True)


def run_effects_dereverb_deecho(
    job_id: str,
    file_path: Path,
    output_format: str,
    combined_model: str,
    fallback_sequential: bool,
    fallback_dereverb_model: str,
    fallback_deecho_model: str,
) -> None:
    step_dirs = _ensure_step_dirs(job_id, 2)
    job = job_store.get(job_id)
    job["status"] = "processing"
    job["pipeline"] = {}
    job["processing_mode"] = "fused"

    try:
        sep = make_separator(step_dirs[1])
        sep.output_format = output_format

        job["pipeline"]["step1"] = "running"
        fused_stems = _run_step(sep, step_dirs[1], combined_model, file_path, "s1")
        job["pipeline"]["step1"] = {
            "model": combined_model,
            "files": {k: v.name for k, v in fused_stems.items()},
        }

        fused_clean = pick_clean_stem(fused_stems)
        if not fused_clean:
            raise FileNotFoundError(f"No se encontro stem limpio con modelo fused. Stems: {list(fused_stems.keys())}")

        _finalize_job_files(job_id, fused_stems)
        job["summary"] = {
            "clean_audio": fused_clean.name,
            "clean_source": combined_model,
        }
    except Exception as fused_error:
        if not fallback_sequential:
            _set_job_error(job_id, "Combined dereverb/deecho error", fused_error)
            return

        try:
            logger.warning("[%s] Fused fallo, aplicando fallback secuencial: %s", job_id, fused_error)
            job["processing_mode"] = "sequential"
            job["fallback_reason"] = str(fused_error)

            sep = make_separator(step_dirs[1])
            sep.output_format = output_format

            job["pipeline"]["step1"] = "running"
            step1_stems = _run_step(sep, step_dirs[1], fallback_dereverb_model, file_path, "s1")
            job["pipeline"]["step1"] = {
                "model": fallback_dereverb_model,
                "files": {k: v.name for k, v in step1_stems.items()},
            }

            step1_clean = require_stem(
                step1_stems,
                ["dry", "vocals", "instrumental", "guitar", "other"],
                "No se encontro stem limpio tras dereverb en fallback",
            )

            job["pipeline"]["step2"] = "running"
            step2_stems = _run_step(sep, step_dirs[2], fallback_deecho_model, step1_clean, "s2")
            job["pipeline"]["step2"] = {
                "model": fallback_deecho_model,
                "files": {k: v.name for k, v in step2_stems.items()},
            }

            final_clean = pick_clean_stem(step2_stems)
            if not final_clean:
                raise FileNotFoundError(
                    f"No se encontro stem limpio tras deecho en fallback. Stems: {list(step2_stems.keys())}"
                )

            _finalize_job_files(job_id, step2_stems)
            job["summary"] = {
                "clean_audio": final_clean.name,
                "clean_source": f"{fallback_dereverb_model}->{fallback_deecho_model}",
            }
        except Exception as fallback_error:
            logger.error("[%s] Fallback secuencial fallo: %s", job_id, fallback_error)
            job["status"] = "error"
            job["error"] = f"Fused failed: {fused_error}. Sequential fallback failed: {fallback_error}"
    finally:
        file_path.unlink(missing_ok=True)


def run_preload_models(models_to_download: list[str]) -> None:
    from audio_separator.separator import Separator
    from .config import MODEL_DIR

    sep = Separator(output_dir="/tmp", model_file_dir=str(MODEL_DIR))
    for key in models_to_download:
        model_name = MODELS.get(key)
        if not model_name:
            continue
        try:
            logger.info("[preload] Descargando: %s", model_name)
            sep.load_model(model_name)
            logger.info("[preload] OK: %s", model_name)
        except Exception as error:
            logger.warning("[preload] Error %s: %s", model_name, error)
