from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile

from ..config import (
    GUITAR_DEREVERB_MODELS,
    GUITAR_SOURCE_MODELS,
    MODELS,
    VOCAL_GENDER_SPLIT_MODELS,
    VOCAL_RECONSTRUCT_MODELS,
)
from ..http_utils import create_job_with_input
from ..validation import validate_model_key, validate_output_format
from ..workflows import (
    run_guitar_pipeline,
    run_pipeline,
    run_separation,
    run_vocals_gender_split,
    run_vocals_reconstruct,
)

router = APIRouter()


@router.post(
    "/separate",
    summary="Separar con un modelo (asincrono)",
    responses={400: {"description": "Parametros invalidos"}},
)
async def separate(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(..., description="Archivo de audio (mp3, wav, flac)")],
    model: Annotated[str, Form(description="Modelo a usar")] = "mel_roformer",
    output_format: Annotated[str, Form(description="Formato salida: wav, flac, mp3")] = "wav",
):
    validate_model_key("model", model)
    validate_output_format(output_format)

    job_id, dest = create_job_with_input(file, {"status": "queued", "model": model, "type": "single", "files": {}})
    background_tasks.add_task(run_separation, job_id, dest, model, output_format)
    return {"job_id": job_id, "status": "queued", "model": model}


@router.post(
    "/separate/pipeline",
    summary="Pipeline 3 pasos: stem -> backing -> de-reverb",
    responses={400: {"description": "Parametros invalidos"}},
)
async def separate_pipeline(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(..., description="Archivo de audio (mp3, wav, flac)")],
    step1_model: Annotated[str, Form(description="Paso 1 - vocal/instrumental")] = "mel_roformer",
    step2_model: Annotated[str, Form(description="Paso 2 - lead vs backing vocals")] = "mel_karaoke",
    step3_model: Annotated[str, Form(description="Paso 3 - de-reverb/de-echo")] = "dereverb_mel",
    output_format: Annotated[str, Form(description="Formato salida: wav, flac, mp3")] = "wav",
):
    validate_output_format(output_format)
    validate_model_key("step1_model", step1_model)
    validate_model_key("step2_model", step2_model)
    validate_model_key("step3_model", step3_model)

    job_id, dest = create_job_with_input(file, {"status": "queued", "type": "pipeline", "pipeline": {}})
    background_tasks.add_task(run_pipeline, job_id, dest, output_format, step1_model, step2_model, step3_model)
    return {
        "job_id": job_id,
        "status": "queued",
        "pipeline": {"step1": step1_model, "step2": step2_model, "step3": step3_model},
    }


@router.post(
    "/separate/guitar/pipeline",
    summary="Separar guitarra + limpiar reverb",
    responses={400: {"description": "Parametros invalidos"}},
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

    job_id, dest = create_job_with_input(
        file,
        {
            "status": "queued",
            "type": "guitar_pipeline",
            "pipeline": {},
            "models": {"split_model": split_model, "dereverb_model": dereverb_model},
        },
    )
    background_tasks.add_task(run_guitar_pipeline, job_id, dest, output_format, split_model, dereverb_model)
    return {
        "job_id": job_id,
        "status": "queued",
        "pipeline": {"step1": split_model, "step2": dereverb_model},
    }


@router.post(
    "/separate/vocals/reconstruct",
    summary="Reconstruir voces",
    responses={400: {"description": "Parametros invalidos"}},
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

    job_id, dest = create_job_with_input(
        file,
        {
            "status": "queued",
            "type": "vocals_reconstruct",
            "pipeline": {},
            "models": {"extract_model": extract_model, "reconstruct_model": reconstruct_model},
        },
    )
    background_tasks.add_task(run_vocals_reconstruct, job_id, dest, output_format, extract_model, reconstruct_model)
    return {
        "job_id": job_id,
        "status": "queued",
        "pipeline": {"step1": extract_model, "step2": reconstruct_model},
    }


@router.post(
    "/separate/vocals/male-female",
    summary="Separar voces por hombre/mujer",
    responses={400: {"description": "Parametros invalidos"}},
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

    job_id, dest = create_job_with_input(
        file,
        {
            "status": "queued",
            "type": "vocals_male_female",
            "pipeline": {},
            "models": {"extract_model": extract_model, "split_model": split_model},
        },
    )
    background_tasks.add_task(run_vocals_gender_split, job_id, dest, output_format, extract_model, split_model)
    return {
        "job_id": job_id,
        "status": "queued",
        "pipeline": {"step1": extract_model, "step2": split_model},
    }
