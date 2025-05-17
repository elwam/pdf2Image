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
   

# --- Endpoint 2: Clasificación de texto (AJUSTADO) ---
@app.post("/clasificar-texto-adicional") # O considera un nombre como /clasificar-documento-por-reglas
async def clasificar_texto_endpoint(request_data: TextoParaClasificarRequest):
    try:
        texto_a_clasificar = request_data.texto_documento

        resultado_clasificacion, texto_devuelto = clasificar_texto_por_reglas(texto_a_clasificar)

        accion_sugerida = "ninguna" # Default
        texto_final_para_llm = ""

        if resultado_clasificacion == "REVISAR_CON_LLM":
            accion_sugerida = "enviar_a_llm"
            texto_final_para_llm = texto_devuelto # Se asume que texto_devuelto es el texto limpio para LLM
        elif resultado_clasificacion not in ["sin_clasificacion", "documento_vacio"]: # Asumiendo que estos no van a LLM
            accion_sugerida = "usar_clasificacion"
        # Si es "sin_clasificacion" o "documento_vacio", accion_sugerida permanece "ninguna"


        return JSONResponse(content={
            "clasificacion": resultado_clasificacion,
            "accion_sugerida": accion_sugerida,
            "texto_para_llm": texto_final_para_llm,
            "texto_analizado_original": texto_a_clasificar # Útil para que el cliente sepa qué texto se procesó
        })

    except Exception as e:
        # import traceback
        # print(f"Error en /clasificar-texto-adicional: {traceback.format_exc()}") # Para depuración
        # Para producción, considera un logging más detallado
        # import logging
        # logging.exception("Error en /clasificar-texto-adicional")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor en clasificación: {str(e)}")

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
        "endpoints": { # Usar un diccionario para mejor legibilidad
            "/convert-pdf": "POST, multipart/form-data, 'file' -> Extrae texto de un PDF.",
            "/clasificar-texto-adicional": "POST, json, {'texto_documento': 'string'} -> Clasifica texto general por reglas.",
            "/clasificar-factura-examenes": "POST, json, {'texto_documento': 'string'} -> Clasifica si una factura tiene exámenes."
        }
    }