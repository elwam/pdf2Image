# Dockerfile para la aplicación FastAPI con Tesseract y Poppler
FROM python:3.10-slim

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libglib2.0-0 libsm6 libxrender1 libxext6 \
    && apt-get clean

# Crea directorio de trabajo
WORKDIR /app

# Copia e instala dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la app
COPY app/ ./app

# Limites conservadores para evitar que OCR sature la maquina completa.
ENV WEB_CONCURRENCY=2 \
    OMP_THREAD_LIMIT=1 \
    OCR_CONCURRENCY=1 \
    OCR_QUEUE_TIMEOUT_SECONDS=20 \
    TESSERACT_TIMEOUT_SECONDS=60 \
    PDF_DPI=150 \
    MAX_PDF_PAGES=20

# Ejecuta Gunicorn con workers Uvicorn
# OCR es CPU-bound: subir workers puede crear demasiados procesos tesseract.
CMD ["sh", "-c", "exec gunicorn -w \"${WEB_CONCURRENCY}\" -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000 --timeout 300 --graceful-timeout 240 --limit-request-line 8190 --limit-request-field_size 8190"]
