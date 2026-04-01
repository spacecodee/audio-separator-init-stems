# Stem Separator — Uso y Docker

Proyecto: API y contenedor para separar stems usando `audio-separator` (UVR/MelBand-RoFormer, MDX, Demucs, etc.).

Este repositorio contiene una pequeña API FastAPI (`main.py`) que orquesta un pipeline de 3 pasos (separación → backing vocals → de-reverb) y un `Dockerfile` + `docker-compose.yml` para ejecutarlo en contenedor (GPU opcional).

## Estructura relevante

- `main.py` — FastAPI que expone endpoints `/separate` y `/separate/pipeline`.
- `Dockerfile` — imagen que instala `audio-separator` y levanta `uvicorn main:app`.
- `docker-compose.yml` — servicio `stem-separator` (nombre del servicio y `container_name: stem-separator`).
- `input/`, `models/`, `output/` — carpetas montadas en el contenedor (vacías en el repo).
- `export_models_json.sh` — script auxiliar para exportar el listado de modelos a JSON.

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

## Archivos importantes

- [main.py](main.py) — implementa la API y el pipeline.
- [docker-compose.yml](docker-compose.yml) — define el servicio `stem-separator`.
- [export_models_json.sh](export_models_json.sh) — script de exportación de modelos.

---

Si quieres, puedo:

- Añadir más ejemplos concretos de `curl`/JSON con respuestas.
- Incluir instrucciones para ejecutar en entornos sin `docker compose` (solo `docker`).
- Comitear este `README.md` por ti si me lo pides.
