from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel # Para definir el cuerpo de la solicitud del nuevo endpoint
from pdf2image import convert_from_bytes
import pytesseract

from .classifier import clasificar_texto_por_reglas, clasificar_factura_examenes


app = FastAPI()

# --- Modelo Pydantic para la entrada del endpoint de clasificación ---
class TextoParaClasificarRequest(BaseModel):
    texto_documento: str # El texto completo del documento a clasificar

# --- Endpoint 1: Extracción de texto de PDF (sin cambios) ---
@app.post("/convert-pdf")
async def convert_pdf(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()

        # Convierte todas las páginas del PDF a imágenes con alta resolución
        images = convert_from_bytes(pdf_bytes, dpi=300)

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
    

# --- Endpoint 2: Clasificación de texto (nuevo endpoint) ---
@app.post("/clasificar-texto-adicional")
async def clasificar_texto_endpoint(request_data: TextoParaClasificarRequest):
    try:
        texto_a_clasificar = request_data.texto_documento

        if not texto_a_clasificar or texto_a_clasificar.isspace():
            # Si el texto está vacío, decidimos cómo clasificarlo.
            # Podría ser 'sin_clasificacion' o 'REVISAR_CON_LLM' si prefieres que LLM lo vea.
            # O una categoría específica como 'documento_vacio'.
            return JSONResponse(content={
                "clasificacion_reglas": "sin_clasificacion", # O "REVISAR_CON_LLM"
                "texto_analizado": texto_a_clasificar,
                "texto_para_llm": texto_a_clasificar # Si es REVISAR_CON_LLM, pasaría este texto vacío
            })

        clasificacion, texto_devuelto_para_llm = clasificar_texto_por_reglas(texto_a_clasificar)

        return JSONResponse(content={
            "clasificacion_reglas": clasificacion,
            "texto_analizado": texto_a_clasificar, # Devolvemos el texto que se analizó
            "texto_para_llm": texto_devuelto_para_llm # El texto que se debe pasar al LLM si es REVISAR_CON_LLM
        })
    except Exception as e:
        # import traceback
        # print(f"Error en /clasificar-texto: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"error": f"Error interno del servidor en clasificación: {str(e)}"})

# --- Endpoint 3: Clasificación de Factura para Exámenes (NUEVO) ---
@app.post("/clasificar-factura-examenes")
async def clasificar_factura_endpoint(request_data: TextoParaClasificarRequest):
    try:
        texto_factura_a_clasificar = request_data.texto_documento

        if not texto_factura_a_clasificar or texto_factura_a_clasificar.isspace():
            # Si el texto está vacío, asumimos que no hay exámenes
            return JSONResponse(content={"examenesFacturados": 0, "decision_source": "empty_text"})

        # Llamar a la nueva función de clasificación de facturas
        resultado_clasificacion = clasificar_factura_examenes(texto_factura_a_clasificar)
        
        return JSONResponse(content=resultado_clasificacion)

    except Exception as e:
        # import traceback
        # print(f"Error en /clasificar-factura-examenes: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"error": f"Error interno del servidor en clasificación de factura: {str(e)}"})

@app.get("/")
async def root():
    return {
        "message": "API de OCR y Clasificación de Textos Médicos.",
        "endpoints": [
            "/convert-pdf (POST, multipart/form-data, 'file')",
            "/clasificar-texto (POST, json, {'texto_documento': 'string'})",
            "/clasificar-factura-examenes (POST, json, {'texto_documento': 'string'})"
        ]
    }
