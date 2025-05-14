from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import io

app = FastAPI()

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
