import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestEndpointLimpiarTexto:
    def test_limpiar_texto_success(self):
        payload = {
            "texto": "Este es un TEXTO con CARACTERES especiales: @#$%&*()"
        }

        response = client.post("/limpiar-texto", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "texto_limpio" in data
        assert "longitud" in data

        # Verificar que el texto fue limpiado (minúsculas, etc.)
        texto_limpio = data["texto_limpio"]
        assert texto_limpio.islower()  # Debe estar en minúsculas
        assert "@" not in texto_limpio  # Sin caracteres especiales
        assert data["longitud"] == len(texto_limpio)

    def test_limpiar_texto_empty(self):
        payload = {"texto": ""}

        response = client.post("/limpiar-texto", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["texto_limpio"] == ""
        assert data["longitud"] == 0

    def test_limpiar_texto_only_special_chars(self):
        payload = {"texto": "@#$%&*()[]{}"}

        response = client.post("/limpiar-texto", json=payload)
        assert response.status_code == 200

        data = response.json()
        # Debería quedar vacío o solo espacios
        assert data["longitud"] >= 0

    def test_limpiar_texto_with_numbers(self):
        payload = {"texto": "Documento 123-456-789 válido"}

        response = client.post("/limpiar-texto", json=payload)
        assert response.status_code == 200

        data = response.json()
        texto_limpio = data["texto_limpio"]
        assert "123" in texto_limpio  # Los números deben mantenerse
        assert "456" in texto_limpio
        assert "789" in texto_limpio

    def test_limpiar_texto_mixed_content(self):
        payload = {
            "texto": "Jose Maria Garcia vive en Bogota. Documento: 123.456.789-0"
        }

        response = client.post("/limpiar-texto", json=payload)
        assert response.status_code == 200

        data = response.json()
        texto_limpio = data["texto_limpio"]

        # Verificar normalización
        assert "jose maria garcia" in texto_limpio  # Minúsculas
        assert "vive en bogota" in texto_limpio
        assert "1234567890" in texto_limpio  # Números limpios

    def test_limpiar_texto_no_texto_field(self):
        payload = {"otro_campo": "texto"}

        response = client.post("/limpiar-texto", json=payload)
        assert response.status_code == 422  # Validación de Pydantic

    def test_limpiar_texto_null_input(self):
        payload = {"texto": None}

        response = client.post("/limpiar-texto", json=payload)
        # Debería manejar None gracefully
        assert response.status_code in [200, 422]

    def test_limpiar_texto_long_text(self):
        # Texto largo para probar rendimiento
        long_text = "Este es un texto muy largo. " * 100
        payload = {"texto": long_text}

        response = client.post("/limpiar-texto", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert len(data["texto_limpio"]) > 0
        assert data["longitud"] == len(data["texto_limpio"])