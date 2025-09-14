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
sudo docker run -d --restart unless-stopped --name pdf2image_container -p 8000:8000 pdf2image