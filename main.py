"""
Stem Separator API - python-audio-separator + FastAPI
Pipeline completo: separacion -> backing vocals -> de-reverb/de-echo
"""
import logging
import os

from fastapi import FastAPI

from stem_api.config import PRELOAD_MODELS
from stem_api.routers import (
    assets_router,
    effects_router,
    jobs_router,
    separation_router,
    system_router,
)
from stem_api.workflows import run_preload_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Stem Separator API",
    description="Separacion de stems con UVR5 / MelBand-RoFormer en GPU NVIDIA",
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
)

app.include_router(system_router)
app.include_router(assets_router)
app.include_router(separation_router)
app.include_router(effects_router)
app.include_router(jobs_router)


@app.on_event("startup")
async def preload_pipeline_models() -> None:
    if os.getenv("SKIP_MODEL_PRELOAD", "0") == "1":
        logger.info("SKIP_MODEL_PRELOAD=1, omitiendo precarga de modelos.")
        return

    import asyncio

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_preload_models, PRELOAD_MODELS)
    logger.info("Modelos del pipeline listos.")
