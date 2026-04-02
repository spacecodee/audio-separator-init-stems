from fastapi import APIRouter

from ..config import (
    MODELS_EXPLORER_CSS,
    MODELS_EXPLORER_HTML,
    MODELS_EXPLORER_JS,
    MODELS_EXPLORER_JSON,
)
from ..http_utils import serve_asset_file

router = APIRouter()


@router.get(
    "/models-explorer",
    include_in_schema=False,
    responses={404: {"description": "Archivo no encontrado"}},
)
def models_explorer_page():
    return serve_asset_file(MODELS_EXPLORER_HTML, "text/html")


@router.get(
    "/models-explorer.html",
    include_in_schema=False,
    responses={404: {"description": "Archivo no encontrado"}},
)
def models_explorer_page_alias():
    return models_explorer_page()


@router.get(
    "/models-explorer.css",
    include_in_schema=False,
    responses={404: {"description": "Archivo no encontrado"}},
)
def models_explorer_css():
    return serve_asset_file(MODELS_EXPLORER_CSS, "text/css")


@router.get(
    "/models-explorer.js",
    include_in_schema=False,
    responses={404: {"description": "Archivo no encontrado"}},
)
def models_explorer_js():
    return serve_asset_file(MODELS_EXPLORER_JS, "application/javascript")


@router.get(
    "/models.json",
    include_in_schema=False,
    responses={404: {"description": "Archivo no encontrado"}},
)
def models_explorer_data():
    return serve_asset_file(MODELS_EXPLORER_JSON, "application/json")
