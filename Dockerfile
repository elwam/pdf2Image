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

# Ejecuta Gunicorn con workers Uvicorn
# CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000", "--timeout", "300", "--graceful-timeout", "60", "--limit-request-line", "8190", "--limit-request-field_size", "8190"]
