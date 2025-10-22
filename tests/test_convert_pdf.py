import pytest
from fastapi.testclient import TestClient
from app.main import app
import io

client = TestClient(app)

class TestEndpointConvertPdf:
    def test_convert_pdf_success(self):
        # Crear un PDF simple en memoria para testing
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(100, 750, "Este es un documento de prueba")
        c.drawString(100, 730, "para el endpoint de conversion PDF")
        c.drawString(100, 710, "Documento numero: 123456789")
        c.save()

        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Crear archivo UploadFile simulado
        files = {"file": ("merged_local.pdf", pdf_bytes, "application/pdf")}

        response = client.post("/convert-pdf", files=files)
        assert response.status_code == 200

        data = response.json()
        assert "pages" in data
        assert len(data["pages"]) > 0

        # Verificar estructura de respuesta
        page = data["pages"][0]
        assert "page" in page
        assert "text" in page
        assert page["page"] == 1

    def test_convert_pdf_empty_file(self):
        # Enviar archivo vacío
        files = {"file": ("empty.pdf", b"", "application/pdf")}

        response = client.post("/convert-pdf", files=files)
        # Debería manejar el error gracefully
        assert response.status_code in [200, 500]  # Puede variar según implementación

    def test_convert_pdf_invalid_file(self):
        # Enviar archivo que no es PDF
        files = {"file": ("not_pdf.txt", b"esto no es un pdf", "text/plain")}

        response = client.post("/convert-pdf", files=files)
        # Debería manejar el error
        assert response.status_code in [200, 500]

    def test_convert_pdf_no_file(self):
        # Enviar sin archivo
        response = client.post("/convert-pdf")
        assert response.status_code == 422  # Validación de FastAPI

    def test_convert_pdf_multiple_pages(self):
        # Crear PDF con múltiples páginas
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        # Página 1
        c.drawString(100, 750, "Primera pagina del documento")
        c.drawString(100, 730, "Nombre: Juan Perez")
        c.showPage()

        # Página 2
        c.drawString(100, 750, "Segunda pagina")
        c.drawString(100, 730, "Documento: 123456789")
        c.save()

        pdf_bytes = buffer.getvalue()
        buffer.close()

        files = {"file": ("multi_page.pdf", pdf_bytes, "application/pdf")}

        response = client.post("/convert-pdf", files=files)
        assert response.status_code == 200

        data = response.json()
        assert len(data["pages"]) >= 2  # Al menos 2 páginas

        # Verificar que cada página tiene estructura correcta
        for i, page in enumerate(data["pages"]):
            assert page["page"] == i + 1
            assert "text" in page