import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestEndpointVerificarPersona:
    def test_verificar_persona_success(self):
        payload = {
            "nombre": "juan perez",
            "documento": "123456789",
            "texto_evaluar": "juan perez documento 123456789"
        }
        response = client.post("/verificar-persona", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert data["score"] == 100
        assert data["componentes"]["documento"] == 20
        assert data["componentes"]["nombre"] == 80
        assert data["componentes"]["penalizacion_documento"] == 0

    def test_verificar_persona_partial_match(self):
        payload = {
            "nombre": "juan",
            "documento": "123456789",  # Documento completo
            "texto_evaluar": "juan documento 123456"  # Solo primeros 6 dígitos en texto
        }
        response = client.post("/verificar-persona", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 95  # 15 doc (6 dígitos) + 80 nombre + 0 penalización

    def test_verificar_persona_nombre_only_with_penalty(self):
        # Caso clave: nombre completo pero sin documento -> penalización
        payload = {
            "nombre": "juan perez",
            "documento": "999999999",
            "texto_evaluar": "juan perez vive aqui"
        }
        response = client.post("/verificar-persona", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 60  # 80 nombre + 0 documento - 20 penalización

    def test_verificar_persona_no_match(self):
        payload = {
            "nombre": "pedro",
            "documento": "999999999",
            "texto_evaluar": "juan documento 123456"
        }
        response = client.post("/verificar-persona", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 0

    def test_verificar_persona_simple_request(self):
        payload = {
            "nombre": "juan perez",
            "documento": "123456789",
            "texto_evaluar": "juan perez documento 123456789"
        }
        response = client.post("/verificar-persona", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 100

    def test_verificar_persona_invalid_data(self):
        payload = {
            "nombre": "",
            "documento": "",
            "texto_evaluar": ""
        }
        response = client.post("/verificar-persona", json=payload)
        assert response.status_code == 200  # La función maneja casos vacíos
        data = response.json()
        assert data["score"] == 0

    def test_verificar_persona_missing_fields(self):
        payload = {
            "nombre": "juan",
            # documento faltante
            "texto_evaluar": "juan"
        }
        response = client.post("/verificar-persona", json=payload)
        assert response.status_code == 422  # Validación de Pydantic

    def test_verificar_persona_exact_match_only(self):
        # Sin fuzzy: "juan" no encuentra "juanito"
        payload = {
            "nombre": "juan",
            "documento": "123456789",
            "texto_evaluar": "juanito documento 123456789"
        }
        response = client.post("/verificar-persona", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 20  # Solo documento completo, sin nombre