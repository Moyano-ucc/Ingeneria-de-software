#!/bin/bash

PORT=${PORT:-8000}

echo "=========================================="
echo "🚀 Iniciando FastAPI en el puerto $PORT"
echo "📁 Archivo principal: Proyecto.py"
echo "🔧 Instancia de FastAPI: app"
echo "=========================================="

python -m gunicorn \
  -w 2 \
  -k uvicorn.workers.UvicornWorker \
  --bind "0.0.0.0:$PORT" \
  Proyecto:app
