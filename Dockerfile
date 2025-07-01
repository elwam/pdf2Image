# Usa imagen oficial ligera de Python 3.10
FROM python:3.10-slim

# Evita preguntas de configuración durante la instalación de paquetes
ENV DEBIAN_FRONTEND=noninteractive

# Instala dependencias del sistema necesarias para Tesseract y Poppler
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia los requirements y luego instala las dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente de la app al contenedor
COPY app/ ./app

# Expone el puerto 8000 (por convención para FastAPI/Uvicorn)
EXPOSE 8000

# Comando de inicio del servidor: 4 workers Gunicorn usando UvicornWorker
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000", "--timeout", "300", "--graceful-timeout", "240", "--limit-request-line", "8190", "--limit-request-field_size", "8190"]