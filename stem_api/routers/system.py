from fastapi import APIRouter, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse

from ..config import (
    DEFAULT_EFFECTS_MODELS,
    DEFAULT_GUITAR_PIPELINE_MODELS,
    DEFAULT_PIPELINE_MODELS,
    DEFAULT_VOCALS_MALE_FEMALE_MODELS,
    DEFAULT_VOCALS_RECONSTRUCT_MODELS,
    MODELS,
)

router = APIRouter()

SWAGGER_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Stem Separator API</title>
  <meta charset=\"utf-8\"/>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <link rel=\"stylesheet\" type=\"text/css\"
        href=\"https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css\">
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
  <div id=\"swagger-ui\"></div>
  <script src=\"https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js\"></script>
  <script>
    window.onload = function() {
      SwaggerUIBundle({
        url: \"/openapi.json\",
        dom_id: \"#swagger-ui\",
        presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
        layout: \"BaseLayout\",
        deepLinking: true,
        tryItOutEnabled: true,
      });
    };
  </script>
</body>
</html>"""


@router.get("/docs", include_in_schema=False)
async def custom_swagger() -> HTMLResponse:
    return HTMLResponse(content=SWAGGER_HTML)


@router.get("/openapi.json", include_in_schema=False)
async def openapi_schema(request: Request) -> dict:
    app = request.app
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )


@router.get("/", summary="Estado del servidor")
def root() -> dict:
    return {"status": "ok", "version": "2.0.0", "message": "Stem Separator API activa"}


@router.get("/models", summary="Modelos disponibles")
def list_models() -> dict:
    return {
        "models": list(MODELS.keys()),
        "pipeline_default": DEFAULT_PIPELINE_MODELS,
        "guitar_pipeline_default": DEFAULT_GUITAR_PIPELINE_MODELS,
        "vocals_reconstruct_default": DEFAULT_VOCALS_RECONSTRUCT_MODELS,
        "vocals_male_female_default": DEFAULT_VOCALS_MALE_FEMALE_MODELS,
        "effects_default": DEFAULT_EFFECTS_MODELS,
    }
