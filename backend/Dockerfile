# Build a partir da raiz do repo (precisa enxergar backend/ e model/ juntos):
#   docker build -f backend/Dockerfile -t tcc-backend .
FROM node:20-bookworm-slim

# libzbar0: dependência nativa do pyzbar (leitura de código de barras)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip libzbar0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Node deps
COPY backend/package*.json backend/
RUN cd backend && npm ci --omit=dev

# Python deps do model/ (venv, igual ao setup local) — CPU-only torch,
# não faz sentido baixar a build CUDA (~2GB) numa VPS sem GPU
COPY model/requirements.txt model/
RUN python3 -m venv model/.venv \
    && model/.venv/bin/pip install --no-cache-dir --upgrade pip \
    && model/.venv/bin/pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && model/.venv/bin/pip install --no-cache-dir -r model/requirements.txt

COPY backend/src backend/src
COPY model/src model/src
COPY model/kernel-metadata.json model/kernel-metadata.json

# model/checkpoints é montado como volume (ver docker-compose.yml) — os
# pesos (~1GB) não fazem parte da imagem, senão todo build reenvia tudo

ENV NODE_ENV=production
EXPOSE 3000
CMD ["node", "backend/src/server.js"]
