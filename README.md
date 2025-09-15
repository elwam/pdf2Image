# pdf2Image API (FastAPI) – OCR, Limpieza de texto y Fusión de PDFs

API en FastAPI para:
- Extraer texto (OCR) desde PDFs.
- Limpiar/normalizar texto.
- Fusionar múltiples PDFs en uno solo.

Basada en pdf2image, pytesseract y pypdf. Incluye Dockerfile para despliegue y ejemplos de uso.

## Características
- OCR página por página desde archivos PDF.
- Normalización básica de texto: minúsculas y colapso de espacios.
- Fusión de múltiples PDFs, devolviendo un PDF descargable y un header con el total de páginas.
- Fusión vía multipart/form-data o vía JSON con base64 (/merge-pdf-json).
- Documentación automática con Swagger en /docs.

## Endpoints
- GET / → Estado del servicio y descripción.
- POST /convert-pdf → multipart/form-data con 'file' (PDF). Devuelve JSON con texto por página.
- POST /limpiar-texto → JSON {"texto":"..."} Devuelve texto_limpio y longitud.
- POST /merge-pdf → multipart/form-data con uno o más 'files' (PDF). Devuelve merged.pdf y header X-Merged-Pages.
- POST /merge-pdf-json → JSON {"files":[{"name":"a.pdf","data_b64":"<base64>","mime_type":"application/pdf"}]}. Devuelve merged_from_json.pdf y header X-Merged-Pages.

## Requisitos
- Python 3.10+
- Dependencias del sistema para OCR y conversión:
  - Tesseract OCR
  - Poppler (para pdf2image)
- Dependencias Python (requirements.txt):
  - fastapi, uvicorn[standard], gunicorn
  - pytesseract, pypdf, pdf2image, pillow, python-multipart

En Linux/Debian (referencia del Dockerfile):

```
apt-get update && apt-get install -y tesseract-ocr poppler-utils
```

En Windows:
- Instalar Tesseract OCR y añadirlo al PATH (ej. C:\Program Files\Tesseract-OCR).
- Instalar Poppler y añadir bin/ al PATH (ej. C:\poppler\bin).

## Ejecución local (desarrollo)
1) Crear entorno e instalar dependencias:

```
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2) Levantar el servidor de desarrollo:

```
uvicorn app.main:app --reload
```

3) Abrir la documentación interactiva:

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## Ejemplos con curl
OCR de un PDF:

```
curl -X POST -F "file=@mi_archivo.pdf" http://localhost:8000/convert-pdf
```

Limpieza de texto:

```
curl -X POST http://localhost:8000/limpiar-texto \
  -H "Content-Type: application/json" \
  -d "{\"texto\":\"Hola    MUNDO\"}"
```

Fusión de múltiples PDFs:

```
curl -X POST http://localhost:8000/merge-pdf \
  -F "files=@a.pdf" \
  -F "files=@b.pdf" \
  -o merged.pdf
```

Nota: /merge-pdf devuelve cabecera X-Merged-Pages con el total de páginas del PDF resultante.

Fusión de múltiples PDFs (JSON base64):

```
curl -X POST http://localhost:8000/merge-pdf-json \
  -H "Content-Type: application/json" \
  -d "{\"files\":[{\"name\":\"a.pdf\",\"data_b64\":\"<BASE64_DEL_PDF>\",\"mime_type\":\"application/pdf\"},{\"name\":\"b.pdf\",\"data_b64\":\"<BASE64_DEL_PDF>\",\"mime_type\":\"application/pdf\"}]}" \
  -o merged_from_json.pdf
```

Nota: en /merge-pdf-json el campo data_b64 debe contener el binario del PDF codificado en base64 (sin prefijos como data:application/pdf;base64,).
## Uso con Docker
Construir imagen:

```
docker build -t pdf2image .
```

Ejecutar contenedor:

```
docker run -d --restart unless-stopped --name pdf2image_container -p 8000:8000 pdf2image
```

También puedes usar el script deploy.sh (Linux) como referencia de despliegue no interactivo.

## Estructura del repositorio
- app/
  - main.py → Endpoints FastAPI (/convert-pdf, /limpiar-texto, /merge-pdf)
  - funciones.py → Utilidades de limpieza de texto
  - merge.py → Lógica de fusión de PDFs (pypdf)
- requirements.txt
- Dockerfile
- *.ipynb (notebooks de prueba)
- .gitignore (incluye regla para ignorar todos los *.pdf)

## Notas y troubleshooting
- pdf2image requiere Poppler instalado y accesible vía PATH.
- pytesseract requiere Tesseract instalado y accesible vía PATH.
- Para mejorar OCR en español, puedes pasar el parámetro de idioma a pytesseract, por ejemplo:

  En el código, ajusta la llamada a pytesseract:

  ```
  pytesseract.image_to_string(gray, lang="spa")
  ```

  Asegúrate de tener instalado el paquete de datos de idioma de Tesseract (spa).

- /merge-pdf-json acepta mime_type "application/pdf", "application/octet-stream" o None; si data_b64 no es base64 válido se responde 400.
- El DPI usado en OCR es 200 por defecto en convert_from_bytes; puedes ajustarlo según calidad/tiempo.
- Se ignoran todos los archivos *.pdf vía .gitignore. Si necesitas adjuntar muestras, renómbralas (por ej. .pdf.sample) o crea excepciones específicas.

## Licencia
No se ha definido una licencia en este repositorio. Añade una si corresponde.