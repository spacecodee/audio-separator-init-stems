from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile

from ..config import COMBINED_DEREVERB_DEECHO_MODELS, DEECHO_MODELS, DEREVERB_MODELS
from ..http_utils import create_job_with_input
from ..validation import validate_model_key, validate_output_format
from ..workflows import run_effect_single, run_effects_dereverb_deecho

router = APIRouter()


@router.post(
    "/effects/dereverb",
    summary="Eliminar reverb",
    responses={400: {"description": "Parametros invalidos"}},
)
async def effects_dereverb(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(..., description="Archivo de audio (mp3, wav, flac)")],
    model: Annotated[str, Form(description="Modelo para eliminar reverb")] = "dereverb_mel",
    output_format: Annotated[str, Form(description="Formato salida: wav, flac, mp3")] = "wav",
):
    validate_output_format(output_format)
    validate_model_key("model", model, DEREVERB_MODELS)

    job_id, dest = create_job_with_input(
        file,
        {"status": "queued", "type": "dereverb_single", "model": model, "files": {}},
    )
    background_tasks.add_task(run_effect_single, job_id, dest, model, output_format, "Dereverb error")
    return {
        "job_id": job_id,
        "status": "queued",
        "type": "dereverb_single",
        "model": model,
    }


@router.post(
    "/effects/deecho",
    summary="Eliminar echo",
    responses={400: {"description": "Parametros invalidos"}},
)
async def effects_deecho(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(..., description="Archivo de audio (mp3, wav, flac)")],
    model: Annotated[str, Form(description="Modelo para eliminar echo")] = "deecho_normal",
    output_format: Annotated[str, Form(description="Formato salida: wav, flac, mp3")] = "wav",
):
    validate_output_format(output_format)
    validate_model_key("model", model, DEECHO_MODELS)

    job_id, dest = create_job_with_input(
        file,
        {"status": "queued", "type": "deecho_single", "model": model, "files": {}},
    )
    background_tasks.add_task(run_effect_single, job_id, dest, model, output_format, "Deecho error")
    return {
        "job_id": job_id,
        "status": "queued",
        "type": "deecho_single",
        "model": model,
    }


@router.post(
    "/effects/dereverb-deecho",
    summary="Eliminar reverb y echo",
    responses={400: {"description": "Parametros invalidos"}},
)
async def effects_dereverb_deecho(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(..., description="Archivo de audio (mp3, wav, flac)")],
    combined_model: Annotated[str, Form(description="Modelo combinado (fused)")] = "dereverb_echo",
    fallback_sequential: Annotated[bool, Form(description="Si fused falla, usar fallback secuencial")] = True,
    fallback_dereverb_model: Annotated[str, Form(description="Modelo dereverb para fallback")] = "dereverb_mel",
    fallback_deecho_model: Annotated[str, Form(description="Modelo deecho para fallback")] = "deecho_normal",
    output_format: Annotated[str, Form(description="Formato salida: wav, flac, mp3")] = "wav",
):
    validate_output_format(output_format)
    validate_model_key("combined_model", combined_model, COMBINED_DEREVERB_DEECHO_MODELS)
    validate_model_key("fallback_dereverb_model", fallback_dereverb_model, DEREVERB_MODELS)
    validate_model_key("fallback_deecho_model", fallback_deecho_model, DEECHO_MODELS)

    job_id, dest = create_job_with_input(
        file,
        {
            "status": "queued",
            "type": "dereverb_deecho_combined",
            "pipeline": {},
            "processing_mode": "fused",
            "models": {
                "combined_model": combined_model,
                "fallback_dereverb_model": fallback_dereverb_model,
                "fallback_deecho_model": fallback_deecho_model,
            },
            "options": {"fallback_sequential": fallback_sequential},
        },
    )
    background_tasks.add_task(
        run_effects_dereverb_deecho,
        job_id,
        dest,
        output_format,
        combined_model,
        fallback_sequential,
        fallback_dereverb_model,
        fallback_deecho_model,
    )
    return {
        "job_id": job_id,
        "status": "queued",
        "type": "dereverb_deecho_combined",
        "combined_model": combined_model,
        "fallback_sequential": fallback_sequential,
    }
