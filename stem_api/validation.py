from fastapi import HTTPException

from .config import MODELS, VALID_OUTPUT_FORMATS


def validate_output_format(output_format: str) -> None:
    if output_format not in VALID_OUTPUT_FORMATS:
        allowed = ", ".join(sorted(VALID_OUTPUT_FORMATS))
        raise HTTPException(400, f"output_format debe ser: {allowed}")


def validate_model_key(field_name: str, model_key: str, allowed_models: set[str] | None = None) -> None:
    if model_key not in MODELS:
        raise HTTPException(400, f"{field_name} invalido. Opciones: {list(MODELS.keys())}")
    if allowed_models and model_key not in allowed_models:
        raise HTTPException(400, f"{field_name} invalido para este endpoint. Opciones: {sorted(allowed_models)}")
