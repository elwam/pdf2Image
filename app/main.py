from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel # Para definir el cuerpo de la solicitud del nuevo endpoint
from pdf2image import convert_from_bytes
from typing import List
from io import BytesIO
import pytesseract


from .funciones import limpiar_texto
from .merge import merge_pdfs_from_uploadfiles, PdfMergeError

app = FastAPI(title="API OCR/Limpieza/Merge PDF")

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

# --- Endpoint 1: Extracción de texto de PDF (sin cambios) ---
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

@app.post("/merge-pdf", response_class=StreamingResponse)
async def merge_pdf(files: List[UploadFile] = File(..., description="Uno o más PDFs")):
    try:
        if not files: raise HTTPException(400, "Debe enviar al menos un PDF en 'files'.")
        for f in files:
            if f.content_type not in ("application/pdf", "application/octet-stream"):
                raise HTTPException(400, f"'{f.filename}' no parece ser PDF.")
        merged_bytes, total_pages = await merge_pdfs_from_uploadfiles(files)
        headers = {"Content-Disposition": 'attachment; filename="merged.pdf"',
                   "X-Merged-Pages": str(total_pages)}
        return StreamingResponse(BytesIO(merged_bytes), media_type="application/pdf", headers=headers)
    except PdfMergeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error interno al fusionar PDFs: {e}")

