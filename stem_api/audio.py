from __future__ import annotations

import logging
from pathlib import Path

from .config import MODEL_DIR

logger = logging.getLogger(__name__)


def make_separator(output_dir: Path):
    from audio_separator.separator import Separator

    return Separator(
        output_dir=str(output_dir),
        output_format="wav",
        model_file_dir=str(MODEL_DIR),
        use_autocast=True,
    )


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


def pick_clean_stem(stems: dict) -> Path | None:
    clean = find_stem(
        stems,
        ["dry", "vocals", "instrumental", "guitar", "piano", "bass", "drums", "other", "backing"],
    )
    if clean:
        return clean
    if stems:
        return next(iter(stems.values()))
    return None


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
        ("dry", ("dry", "no_reverb", "norev", "no_echo", "noecho", "no-echo", "no echo", "clean")),
        ("echo", ("echo",)),
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

    logger.info("[rename_stems] audios en %s: %s", step_dir, [f.name for f in all_audio])

    renamed = {}
    for src in all_audio:
        key = classify_stem(src.name) or f"stem{len(renamed)}"
        dst = step_dir / f"{prefix}_{key}{src.suffix}"
        if dst.exists() and dst != src:
            dst = step_dir / f"{prefix}_{key}_{src.stem[-6:]}{src.suffix}"
        src.rename(dst)
        renamed[key] = dst
        logger.info("  %s -> %s", src.name, dst.name)

    return renamed
