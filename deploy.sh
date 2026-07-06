#!/bin/bash

# Navega al directorio del proyecto
#cd /ruta/a/tu/proyecto || exit

# Actualiza el repositorio
#git pull

# Detiene y elimina el contenedor actual
sudo docker stop pdf2image_container
sudo docker rm pdf2image_container

# Reconstruye la imagen
sudo docker build -t pdf2image .

# Ejecuta el contenedor
sudo docker run -d \
  --restart unless-stopped \
  --name pdf2image_container \
  --cpus="5.0" \
  -e WEB_CONCURRENCY=2 \
  -e OMP_THREAD_LIMIT=1 \
  -e OCR_CONCURRENCY=1 \
  -e OCR_QUEUE_TIMEOUT_SECONDS=20 \
  -e TESSERACT_TIMEOUT_SECONDS=60 \
  -e PDF_DPI=150 \
  -e MAX_PDF_PAGES=20 \
  -p 8000:8000 \
  pdf2image
