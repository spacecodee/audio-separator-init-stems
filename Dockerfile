# Base CUDA 12 + Ubuntu 22.04
FROM nvidia/cuda:12.3.1-devel-ubuntu22.04

WORKDIR /app
# Instala dependencias del sistema, paquetes Python y crea carpetas
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip install --upgrade pip \
    && pip install --no-cache-dir onnxruntime-gpu \
        --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/ \
    && pip install --no-cache-dir "audio-separator" fastapi uvicorn python-multipart \
    && mkdir -p /app/input /app/output

COPY main.py /app/main.py
COPY models-explorer.html /app/models-explorer.html
COPY models-explorer.css /app/models-explorer.css
COPY models-explorer.js /app/models-explorer.js
COPY models.json /app/models.json

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]