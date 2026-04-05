# Stem Separator — Uso y Docker

Proyecto: API y contenedor para separar stems usando `audio-separator` (UVR/MelBand-RoFormer, MDX, Demucs, etc.).

Este repositorio contiene una API FastAPI modular que orquesta separación por modelos, pipeline de 3 pasos, flujos especializados (guitarra, reconstrucción vocal, split hombre/mujer) y endpoints de efectos (dereverb/deecho), además de `Dockerfile` + `docker-compose.yml` para ejecutarlo en contenedor (GPU opcional).

## Estructura relevante

- `main.py` — entrypoint liviano de FastAPI (wire de routers + startup).
- `stem_api/` — paquete principal con configuración, validadores, workers y routers.
- `Dockerfile` — imagen que instala `audio-separator` y levanta `uvicorn main:app`.
- `docker-compose.yml` — servicio `stem-separator` (nombre del servicio y `container_name: stem-separator`).
- `input/`, `models/`, `output/` — carpetas montadas en el contenedor (vacías en el repo).
- `export_models_json.sh` — script auxiliar para exportar el listado de modelos a JSON.
- `scripts/` — un script bash por endpoint de la API.
- `tests/` — pruebas unitarias e integración mínima.

## Quickstart (Docker Compose)

En la carpeta del proyecto:

```bash
cd /teamspace/studios/this_studio/audio-separator-init-stems
```

Levantar en background:

```bash
docker compose up -d
```

Ver estado de los servicios:

```bash
docker compose ps
```

Reconstruir (si editas `Dockerfile`):

```bash
docker compose build --no-cache stem-separator
docker compose up -d
```

Parar y remover:

```bash
docker compose down
```

## Entrar al contenedor (shell)

Si el servicio está corriendo con `docker compose`:

```bash
docker compose exec stem-separator bash
# si no hay bash disponible, usar sh:
docker compose exec -T stem-separator sh
```

Si ejecutaste el contenedor con `docker run` y le diste nombre `stem-separator`:

```bash
docker exec -it stem-separator bash
```

Si tu terminal no soporta TTY (CI), añade `-T` a `exec`.

## Ver logs

Logs en tiempo real (compose):

```bash
docker compose logs -f stem-separator
```

Logs con límite de líneas y seguimiento:

```bash
docker compose logs --tail 200 -f stem-separator
```

Si usas `docker` (no compose):

```bash
docker logs -f stem-separator
```

Nota: la API (`uvicorn`) escribe en stdout, por lo que `docker compose logs` recoge todas las salidas.

## Comandos útiles dentro del contenedor (CLI `audio-separator`)

- Listar modelos disponibles:

```bash
docker compose exec stem-separator audio-separator -l
```

- Listar y guardar JSON de modelos:

```bash
docker compose exec stem-separator audio-separator -l --list_format=json > /tmp/models.json
```

- Comprobar entorno (GPU/ONNXRuntime):

```bash
docker compose exec stem-separator audio-separator --env_info
```

- Ejecutar separación con un modelo (ejemplo usando archivos montados):

```bash
docker compose exec stem-separator audio-separator /app/input/song.wav \
  --output_dir /app/output \
  -m model_bs_roformer_ep_317_sdr_12.9755.ckpt
```

## Uso de la API (endpoints)

- Separación simple (asíncrona):

```bash
curl -X POST "http://localhost:8000/separate" \
  -F "file=@./input/song.wav" \
  -F "model=mel_roformer" \
  -F "output_format=wav"
```

Respuesta: `{ "job_id": "...", "status": "queued", ... }`.

- Pipeline 3 pasos:

```bash
curl -X POST "http://localhost:8000/separate/pipeline" \
  -F "file=@./input/song.wav" \
  -F "step1_model=mel_roformer" \
  -F "step2_model=mel_karaoke" \
  -F "step3_model=dereverb_mel" \
  -F "output_format=wav"
```

- Pipeline guitarra (extraer guitarra + dereverb):

```bash
curl -X POST "http://localhost:8000/separate/guitar/pipeline" \
  -F "file=@./input/song.wav" \
  -F "split_model=htdemucs_6s" \
  -F "dereverb_model=dereverb_mel" \
  -F "output_format=wav"
```

- Reconstrucción de voces:

```bash
curl -X POST "http://localhost:8000/separate/vocals/reconstruct" \
  -F "file=@./input/song.wav" \
  -F "extract_model=mel_roformer" \
  -F "reconstruct_model=vocals_resurrection" \
  -F "output_format=wav"
```

- Split de voces hombre/mujer:

```bash
curl -X POST "http://localhost:8000/separate/vocals/male-female" \
  -F "file=@./input/song.wav" \
  -F "extract_model=mel_roformer" \
  -F "split_model=chorus_male_female" \
  -F "output_format=wav"
```

- Efecto: eliminar reverb:

```bash
curl -X POST "http://localhost:8000/effects/dereverb" \
  -F "file=@./input/song.wav" \
  -F "model=dereverb_mel" \
  -F "output_format=wav"
```

- Efecto: eliminar echo:

```bash
curl -X POST "http://localhost:8000/effects/deecho" \
  -F "file=@./input/song.wav" \
  -F "model=deecho_normal" \
  -F "output_format=wav"
```

- Efecto: eliminar reverb + echo (fused con fallback secuencial):

```bash
curl -X POST "http://localhost:8000/effects/dereverb-deecho" \
  -F "file=@./input/song.wav" \
  -F "combined_model=dereverb_echo" \
  -F "fallback_sequential=true" \
  -F "fallback_dereverb_model=dereverb_mel" \
  -F "fallback_deecho_model=deecho_normal" \
  -F "output_format=wav"
```

- Consultar estado del job:

```bash
curl http://localhost:8000/jobs/<JOB_ID>
```

- Descargar un stem resultante:

```bash
curl -O http://localhost:8000/download/<JOB_ID>/<filename.wav>
```

- Borrar job y archivos:

```bash
curl -X DELETE http://localhost:8000/jobs/<JOB_ID>
```

## Scripts bash por endpoint

Todos los scripts viven en `./scripts` y ya vienen listos para ejecutar.

Preparacion:

```bash
cd /teamspace/studios/this_studio/audio-separator-init-stems
cp -n .env.example .env
chmod +x scripts/*.bash
chmod +x scripts/validate_endpoints.bash
```

Endpoints de lectura/metadata:

- `scripts/endpoint_root.bash` → `GET /`
- `scripts/endpoint_models.bash` → `GET /models`
- `scripts/endpoint_docs.bash` → `GET /docs`
- `scripts/endpoint_openapi_json.bash` → `GET /openapi.json`
- `scripts/endpoint_models_explorer.bash` → `GET /models-explorer`
- `scripts/endpoint_models_explorer_html.bash` → `GET /models-explorer.html`
- `scripts/endpoint_models_explorer_css.bash` → `GET /models-explorer.css`
- `scripts/endpoint_models_explorer_js.bash` → `GET /models-explorer.js`
- `scripts/endpoint_models_json.bash` → `GET /models.json`
- `scripts/endpoint_jobs_list.bash` → `GET /jobs`

Endpoints asíncronos de separación:

- `scripts/endpoint_separate.bash` → `POST /separate`
- `scripts/endpoint_separate_pipeline.bash` → `POST /separate/pipeline`
- `scripts/endpoint_separate_guitar_pipeline.bash` → `POST /separate/guitar/pipeline`
- `scripts/endpoint_separate_vocals_reconstruct.bash` → `POST /separate/vocals/reconstruct`
- `scripts/endpoint_separate_vocals_male_female.bash` → `POST /separate/vocals/male-female`

Endpoints asíncronos de efectos:

- `scripts/endpoint_effects_dereverb.bash` → `POST /effects/dereverb`
- `scripts/endpoint_effects_deecho.bash` → `POST /effects/deecho`
- `scripts/endpoint_effects_dereverb_deecho.bash` → `POST /effects/dereverb-deecho`

Endpoints de job/resultados:

- `scripts/endpoint_job_status.bash` → `GET /jobs/{job_id}`
- `scripts/endpoint_download.bash` → `GET /download/{job_id}/{filename}`
- `scripts/endpoint_job_delete.bash` → `DELETE /jobs/{job_id}`

Configuracion centralizada con `.env`:

- Los scripts cargan automaticamente `./.env` (si existe).
- Puedes sobreescribir cualquier valor por ejecucion, por ejemplo:

```bash
BASE=http://127.0.0.1:9000 AUDIO=./input/song.wav ./scripts/endpoint_separate.bash
```

Variables comunes:

- `DEFAULT_BASE`, `DEFAULT_AUDIO`, `DEFAULT_OUTPUT_FORMAT`, `DEFAULT_POLL_SECONDS`

Variables por endpoint (ejemplos):

- `SEPARATE_AUDIO`, `SEPARATE_MODEL`
- `PIPELINE_STEP1_MODEL`, `PIPELINE_STEP2_MODEL`, `PIPELINE_STEP3_MODEL`
- `GUITAR_SPLIT_MODEL`, `GUITAR_DEREVERB_MODEL`
- `VOCALS_RECONSTRUCT_EXTRACT_MODEL`, `VOCALS_RECONSTRUCT_MODEL`
- `VOCALS_MALE_FEMALE_EXTRACT_MODEL`, `VOCALS_MALE_FEMALE_SPLIT_MODEL`
- `EFFECTS_DEREVERB_MODEL`, `EFFECTS_DEECHO_MODEL`, `EFFECTS_COMBINED_MODEL`
- `EFFECTS_FALLBACK_SEQUENTIAL`, `EFFECTS_FALLBACK_DEREVERB_MODEL`, `EFFECTS_FALLBACK_DEECHO_MODEL`

Archivos de salida para endpoints de descarga/metadata:

- `DOCS_OUT`, `MODELS_EXPLORER_OUT`, `MODELS_EXPLORER_HTML_OUT`
- `MODELS_EXPLORER_CSS_OUT`, `MODELS_EXPLORER_JS_OUT`
- `MODELS_JSON_OUT`, `OPENAPI_JSON_OUT`, `DOWNLOAD_OUT_DIR`

Validacion de endpoints en scripts:

```bash
./scripts/validate_endpoints.bash
```

El validador comprueba que todos los `endpoint_*.bash` apunten a las rutas esperadas de la API, incluyendo el polling a `/jobs/$JOB_ID` en scripts asincronos.

## Exportar listado de modelos a JSON (script)

Ya existe el script `export_models_json.sh` en la raíz del proyecto. Uso rápido:

```bash
# por defecto intenta usar el servicio 'stem-separator' y escribe ./models.json
./export_models_json.sh

# especificando servicio y archivo de salida
./export_models_json.sh stem-separator ./models.json
```

El script detecta si el servicio está corriendo y usa `docker compose exec -T` o, en su defecto, `docker compose run --rm`.

## Models Explorer UI (dark mode)

Se agrego una pagina interactiva para explorar `models.json` con enfoque user-friendly:

- filtros por arquitectura, stem, metrica y score minimo
- resumen estadistico de cobertura y distribucion
- graficas de arquitectura, stems y top modelos
- tabla paginada con detalle por modelo
- comparador de varios modelos por stem/metrica

Archivos:

- `models-explorer.html`
- `models-explorer.css`
- `models-explorer.js`
- `run_models_explorer.sh`

### Opcion recomendada: integrado en FastAPI

Con el servicio levantado, abre directamente:

```text
http://127.0.0.1:8000/models-explorer
```

Assets y datos servidos por la API:

- `/models-explorer.css`
- `/models-explorer.js`
- `/models.json`

Para abrirla localmente:

```bash
cd /teamspace/studios/this_studio/audio-separator-init-stems
chmod +x run_models_explorer.sh
./run_models_explorer.sh 8088
```

Luego abre en tu navegador:

```text
http://127.0.0.1:8088/models-explorer.html
```

Tambien puedes cargar un JSON custom con el boton `Cargar JSON custom`.

## Ejecutar la imagen oficial del proyecto (one-shot)

Si prefieres usar la imagen oficial `beveradb/audio-separator` en lugar de tu API:

GPU:

```bash
docker run --rm -it --gpus all \
  -v "$PWD/input:/workdir/input" \
  -v "$PWD/output:/workdir/output" \
  -v "$PWD/models:/tmp/audio-separator-models" \
  beveradb/audio-separator:gpu \
  /workdir/input/song.wav --output_dir /workdir/output --model_file_dir /tmp/audio-separator-models
```

CPU:

```bash
docker run --rm -it \
  -v "$PWD/input:/workdir/input" \
  -v "$PWD/output:/workdir/output" \
  -v "$PWD/models:/tmp/audio-separator-models" \
  beveradb/audio-separator \
  /workdir/input/song.wav --output_dir /workdir/output --model_file_dir /tmp/audio-separator-models
```

## GPU / Troubleshooting

- Comprueba que `nvidia-container-toolkit` esté instalado y que el daemon Docker soporte `--gpus`.
- Dentro del contenedor, ejecuta `audio-separator --env_info` para verificar que ONNXRuntime detecta CUDA.
- Si los modelos no se descargan, revisa permisos y espacio en disco en `./models` (montado como `/root/.cache/audio-separator` en el contenedor).

## Tests

Ejecutar pruebas locales:

```bash
cd /teamspace/studios/this_studio/audio-separator-init-stems
pytest -q
```

## Archivos importantes

- [main.py](main.py) — inicializa FastAPI y registra routers.
- [stem_api](stem_api) — configuración, workers, validadores y routers.
- [docker-compose.yml](docker-compose.yml) — define el servicio `stem-separator`.
- [export_models_json.sh](export_models_json.sh) — script de exportación de modelos.

---

Si quieres, puedo:

- Añadir más ejemplos concretos de `curl`/JSON con respuestas.
- Incluir instrucciones para ejecutar en entornos sin `docker compose` (solo `docker`).
- Comitear este `README.md` por ti si me lo pides.
