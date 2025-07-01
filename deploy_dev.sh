#!/bin/bash

set -e

# Opcional: navega al directorio del proyecto
# cd /ruta/a/tu/proyecto || exit 1

echo ">>> Cambiando a la rama develop..."
git checkout develop
git pull origin develop

echo ">>> Deteniendo y eliminando contenedor anterior (si existe)..."
sudo docker stop pdf2image_container 2>/dev/null || true
sudo docker rm pdf2image_container 2>/dev/null || true

echo ">>> Construyendo la nueva imagen Docker (rama develop)..."
sudo docker build -t pdf2image .


echo ">>> Ejecutando el contenedor en background en el puerto 8000..."
sudo docker run -d --restart unless-stopped --name pdf2image_container -p 8000:8000 pdf2image


echo ">>> Despliegue completo (rama develop). La aplicación está corriendo en el puerto 8000."