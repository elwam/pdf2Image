from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import JSONResponse
from pdf2image import convert_from_bytes
import pytesseract

from .funciones import limpiar_texto

app = FastAPI(title="API OCR & Limpieza")

class TextoLimpiezaRequest(BaseModel):
    texto: str

@app.get("/")
async def root():
    return {
        "message": "API de OCR y Limpieza de texto",
        "endpoints": {
            "POST /convert-pdf": "multipart/form-data 'file': PDF -> texto por página",
            "POST /limpiar-texto": "json {'texto': 'string'} -> texto normalizado",
        }
    }


# --- Endpoint 1: Extracción de texto de PDF ---
@app.post("/convert-pdf")
async def convert_pdf(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        # Convierte todas las páginas del PDF a imágenes con alta resolución
        images = convert_from_bytes(pdf_bytes, dpi=200)
        ocr_results = []

        for i, image in enumerate(images):
            # Opcional: convertir a escala de grises + mejorar contraste
            gray = image.convert("L")
            # Ejecutar OCR
            text = pytesseract.image_to_string(gray)
            # Agregar resultado al array
            ocr_results.append({
                "page": i + 1,
                "text": text.strip()
            })

        return JSONResponse(content={"pages": ocr_results})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- Endpoint 2: Limpieza de texto ---
@app.post("/limpiar-texto")
async def endpoint_limpiar_texto(data: TextoLimpiezaRequest):
    texto_limpio = limpiar_texto(data.texto)
    return {
        "texto_limpio": texto_limpio,
        "longitud": len(texto_limpio)
    }


