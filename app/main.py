from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from pdf2image import convert_from_bytes
from typing import List, Optional
from io import BytesIO
import pytesseract
import base64


from .funciones import limpiar_texto
from .merge import merge_pdfs_from_uploadfiles, PdfMergeError, merge_pdfs_from_bytes
from .funcionesValidacionAnexos import verificar_persona 

app = FastAPI(title="API OCR/Limpieza/Merge PDF")

class TextoLimpiezaRequest(BaseModel):
    texto: str

class VerificacionRequest(BaseModel):
    nombre: str
    documento: str
    texto_evaluar: str  # Se espera texto YA LIMPIO

# Definición de las Clases para el Merge de PDF
class PdfJson(BaseModel):
    name: Optional[str] = None
    data_b64: str
    mime_type: Optional[str] = "application/pdf"

class MergeJsonRequest(BaseModel):
    files: List[PdfJson]

@app.get("/")
async def root():
    return {
        "message": "API de OCR y Limpieza de texto",
        "endpoints": {
            "POST /convert-pdf": "multipart/form-data 'file': PDF -> texto por página",
            "POST /limpiar-texto": "json {'texto': 'string'} -> texto normalizado",
            "POST /verificar-persona": "json {'nombre','documento','texto_evaluar(limpio)'} -> score (80 nombre + 20 doc -20 penalización)",  # <---
            "POST /merge-pdf": "multipart/form-data 'files': [PDF...] -> PDF fusionado",
            "POST /merge-pdf-json": "json {'files':[{'name','data_b64','mime_type'}]} -> PDF fusionado"
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

@app.post("/verificar-persona")
async def endpoint_verificar_persona(payload: VerificacionRequest):
    """
    Verifica si el nombre/documento del payload están presentes en 'texto_evaluar' (ya limpio).
    Score = Nombre (80) + Documento (20) + Penalización (-20 si no hay documento).
    El objetivo es pasar con 60+ si hay buena coincidencia de nombre O documento.
    Si no se detecta documento, siempre se penaliza fuertemente.
    Solo se aceptan coincidencias exactas (sin fuzzy matching).
    """
    try:
        resultado = verificar_persona(
            nombre=payload.nombre,
            documento=payload.documento,
            texto_limpio=payload.texto_evaluar
        )
        return JSONResponse(content=resultado)
    except Exception as e:
        raise HTTPException(500, f"Error al verificar persona: {e}")

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


@app.post("/merge-pdf-json", response_class=StreamingResponse)
async def merge_pdf_json(req: MergeJsonRequest):
    try:
        if not req.files:
            raise HTTPException(400, "Debe enviar al menos un archivo en 'files'.")

        blobs: List[bytes] = []
        for item in req.files:
            if item.mime_type not in ("application/pdf", "application/octet-stream", None):
                raise HTTPException(400, f"Tipo no permitido: {item.mime_type}")
            try:
                blobs.append(base64.b64decode(item.data_b64))
            except Exception:
                raise HTTPException(400, "Uno de los 'data_b64' no es base64 válido.")

        merged_bytes, total_pages = merge_pdfs_from_bytes(blobs)

        headers = {
            "Content-Disposition": 'attachment; filename="merged_from_json.pdf"',
            "X-Merged-Pages": str(total_pages),
        }
        return StreamingResponse(BytesIO(merged_bytes), media_type="application/pdf", headers=headers)
    except PdfMergeError as e:
        raise HTTPException(400, str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error interno al fusionar PDFs (JSON): {e}")

@app.post("/pdf-to-images")
async def pdf_to_images(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        
        # Convertimos el PDF a imágenes (una por página)
        # Usamos 200 DPI para que el texto pequeño sea legible pero no pese demasiado
        images = convert_from_bytes(pdf_bytes, dpi=200)
        
        base64_images = []

        for img in images:
            buffered = BytesIO()
            # Guardamos como JPEG para reducir el peso del envío (calidad 85-90 es suficiente)
            img.save(buffered, format="JPEG", quality=85)
            
            # Convertimos a base64
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            # Formateamos como Data URI para que sea fácil de usar en n8n o LLM
            base64_images.append(f"data:image/jpeg;base64,{img_str}")

        return JSONResponse(content={
            "filename": file.filename,
            "total_pages": len(base64_images),
            "images": base64_images
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})