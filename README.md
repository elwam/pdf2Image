# pdf2Image API (FastAPI) – OCR, Limpieza de texto, Fusión de PDFs y Validación de Documentos

API en FastAPI para:
- Extraer texto (OCR) desde PDFs.
- Limpiar/normalizar texto.
- Fusionar múltiples PDFs en uno solo.
- **Validar presencia de nombre y documento en texto** (nueva funcionalidad).

Basada en pdf2image, pytesseract y pypdf. Incluye Dockerfile para despliegue, pruebas unitarias/integración y ejemplos de uso.

## Características
- OCR página por página desde archivos PDF.
- Normalización básica de texto: minúsculas y colapso de espacios.
- Fusión de múltiples PDFs, devolviendo un PDF descargable y un header con el total de páginas.
- Fusión vía multipart/form-data o vía JSON con base64 (/merge-pdf-json).
- **Validación de documentos**: Verifica presencia de nombre y documento en texto con scoring inteligente (80% nombre, 20% documento).
- Documentación automática con Swagger en /docs.
- **Suite completa de pruebas**: 46 pruebas unitarias e integración con pytest.

## Endpoints
- GET / → Estado del servicio y descripción.
- POST /convert-pdf → multipart/form-data con 'file' (PDF). Devuelve JSON con texto por página.
- POST /limpiar-texto → JSON {"texto":"..."} Devuelve texto_limpio y longitud.
- **POST /verificar-persona → JSON {"nombre":"...", "documento":"...", "texto_evaluar":"..."} Devuelve score de validación (0-100).**
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
  - pytest, httpx (para testing)

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

3) Ejecutar pruebas (opcional):

```
pytest tests/ -v
```

4) Abrir la documentación interactiva:

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

Validación de persona (nueva funcionalidad):

```
curl -X POST http://localhost:8000/verificar-persona \
  -H "Content-Type: application/json" \
  -d "{\"nombre\":\"juan perez\",\"documento\":\"123456789\",\"texto_evaluar\":\"juan perez documento 123456789\"}"
```

Respuesta esperada:
```json
{
  "score": 100,
  "componentes": {
    "documento": 20,
    "nombre": 80,
    "penalizacion_documento": 0
  },
  "doc_match": {...},
  "nombre_match": {...},
  "tokens_encontrados": ["juan", "perez"],
  "documento_encontrado": "123456789"
}
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
  - main.py → Endpoints FastAPI (/convert-pdf, /limpiar-texto, /verificar-persona, /merge-pdf)
  - funciones.py → Utilidades de limpieza de texto
  - funcionesValidacionAnexos.py → **Lógica de validación de documentos (nueva)**
  - merge.py → Lógica de fusión de PDFs (pypdf)
- tests/ → **Suite completa de pruebas (46 tests)**
  - test_convert_pdf.py → Pruebas OCR
  - test_funcionesValidacionAnexos.py → **Pruebas unitarias validación**
  - test_limpiar_texto.py → Pruebas limpieza
  - test_verificar_persona.py → **Pruebas integración endpoint**
- requirements.txt
- Dockerfile
- test_verificar_persona_api.ipynb → **Notebook interactivo para pruebas**
- .gitignore (incluye regla para ignorar todos los *.pdf)

## Lógica de Validación de Documentos (/verificar-persona)

### Sistema de Scoring (0-100 puntos):
- **Nombre**: 80 puntos máximo (solo coincidencias exactas)
  - Cada token útil del nombre vale puntos proporcionales
  - Excluye stopwords ("de", "la", "del", etc.)
- **Documento**: 20 puntos máximo
  - 20 pts: documento completo encontrado
  - 15 pts: primeros 6 dígitos encontrados
  - 0 pts: no encontrado
- **Penalización**: -20 puntos si NO se detecta documento
- **Total**: Score final entre 0-100

### Ejemplos de Scores:
- ✅ Nombre completo + documento completo → **100 puntos**
- ✅ Nombre completo + documento parcial → **95 puntos**
- ✅ Nombre completo + sin documento → **60 puntos** (penalización aplicada)
- ❌ Sin nombre + documento completo → **20 puntos**
- ❌ Sin coincidencias → **0 puntos**

### Notas Técnicas:
- Solo acepta **coincidencias exactas** (sin fuzzy matching)
- El texto debe estar **previamente limpiado** (minúsculas, sin acentos)
- Los nombres se limpian automáticamente antes del matching

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
- **Nueva funcionalidad**: Ejecuta `pytest tests/ -v` para validar todas las funcionalidades (46 pruebas).

## Licencia
No se ha definido una licencia en este repositorio. Añade una si corresponde.