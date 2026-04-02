import pytest
from fastapi import HTTPException

from stem_api.validation import validate_model_key, validate_output_format


def test_validate_output_format_accepts_known_formats() -> None:
    for fmt in ("wav", "flac", "mp3"):
        validate_output_format(fmt)


def test_validate_output_format_rejects_unknown_format() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_output_format("ogg")
    assert exc.value.status_code == 400


def test_validate_model_key_rejects_unknown_model() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_model_key("model", "not_a_model")
    assert exc.value.status_code == 400


def test_validate_model_key_respects_allowed_set() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_model_key("model", "mel_roformer", {"dereverb_mel"})
    assert exc.value.status_code == 400
