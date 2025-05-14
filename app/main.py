from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pdf2image import convert_from_bytes
import base64
import io

app = FastAPI()

@app.post("/convert-pdf")
async def convert_pdf(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        images = convert_from_bytes(pdf_bytes)
        encoded_images = []

        for image in images:
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
            encoded_images.append(img_str)

        return JSONResponse(content={"pages": encoded_images})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})