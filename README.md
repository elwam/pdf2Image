# pdf2Image

Este proyecto implementa una **API** basada en **FastAPI** para extraer texto de archivos PDF mediante OCR y clasificar el texto obtenido con reglas simples. Incluye funciones para clasificación de facturas médicas y limpieza de texto.

---

## Requisitos

- Python 3.10 o superior  
- Dependencias listadas en `requirements.txt`  
- **Tesseract** y **Poppler** para el OCR (ver `Dockerfile` para ejemplo de instalación)  

Instala las dependencias de Python con:

pip install -r requirements.txt

> Nota: En algunos sistemas operativos deberás instalar Tesseract y Poppler manualmente. Consulta el Dockerfile o la documentación de Tesseract (https://github.com/tesseract-ocr/tesseract) para más información.

---

## Ejecución local

Inicia la API de desarrollo con:

uvicorn app.main:app --reload

Por defecto la aplicación estará disponible en http://localhost:8000, donde puedes probar los endpoints desde la interfaz de Swagger.

---

## Docker

Para construir y ejecutar la aplicación en Docker:

docker build -t pdf2image .
docker run -d --name pdf2image_container -p 8000:8000 pdf2image

---

## Endpoints principales

- POST /convert-pdf: recibe un PDF y devuelve el texto extraído de cada página mediante OCR.
- POST /clasificar-texto-adicional: clasifica bloques de texto según reglas predefinidas.
- POST /clasificar-factura-examenes: determina si una factura incluye exámenes médicos.
- POST /limpiar-texto: limpia el texto (elimina espacios extra, pasa a minúsculas, etc.).

La raíz / muestra un listado resumido de estos endpoints.

---

## Estructura del proyecto

app/
  main.py            # Inicialización de FastAPI y rutas principales
  classifier.py      # Reglas de clasificación
  funciones.py       # Funciones utilitarias y OCR
notebooks/
  ...                # Ejemplos y pruebas manuales en Jupyter
requirements.txt
Dockerfile
README.md

---

## Despliegue: Desarrollo y Producción

El proyecto utiliza dos ramas principales:
- main: para producción
- develop: para desarrollo y pruebas

Existen dos scripts para facilitar el despliegue mediante Docker:

### Despliegue en Producción
Utiliza la rama main y levanta el contenedor en el puerto 8000:
./deploy.sh
Este script:
- Hace checkout a la rama main
- Actualiza el repositorio
- Reconstruye la imagen Docker (pdf2image)
- Elimina el contenedor anterior (si existe)
- Lanza el nuevo contenedor en el puerto 8000

### Despliegue en Desarrollo
Utiliza la rama develop. Si quieres correr ambos ambientes simultáneamente, cambia el nombre del contenedor y el puerto de host en el script:
./deploy-dev.sh
Por ejemplo, puedes lanzar el desarrollo en el puerto 8001:

sudo docker build -t pdf2image:dev .
sudo docker run -d --restart unless-stopped --name pdf2image_container_dev -p 8001:8000 pdf2image:dev

---

## Gestión de Contenedores Docker

- Para ver los contenedores en ejecución:
  sudo docker ps
- Para ver el comando completo con el que se lanzó cada contenedor:
  sudo docker ps --no-trunc
- Para inspeccionar un contenedor específico y ver su comando de inicio:
  sudo docker inspect --format '{{.Path}} {{range .Args}} {{.}} {{end}}' <container_name_or_id>

---

## Notas adicionales

- Los ejemplos y pruebas manuales están en la carpeta notebooks/.
- Es necesario que los binarios de Tesseract y Poppler estén disponibles en el entorno de ejecución.

---

¿Dudas o sugerencias? ¡Contribuciones y PRs son bienvenidos!
