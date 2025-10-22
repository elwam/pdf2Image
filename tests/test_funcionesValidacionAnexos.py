import pytest
from app.funcionesValidacionAnexos import (
    verificar_persona,
    score_document,
    score_nombre,
    document_penalty,
    digits_only,
    tokenize_words,
    fuzzy_ratio,
    limpiar_texto_validacion
)

class TestDigitsOnly:
    def test_digits_only_normal(self):
        assert digits_only("123-456-789") == "123456789"

    def test_digits_only_empty(self):
        assert digits_only("") == ""

    def test_digits_only_no_digits(self):
        assert digits_only("abc") == ""

class TestTokenizeWords:
    def test_tokenize_words_normal(self):
        assert tokenize_words("hola mundo 123") == ["hola", "mundo", "123"]

    def test_tokenize_words_empty(self):
        assert tokenize_words("") == []

    def test_tokenize_words_special_chars(self):
        assert tokenize_words("hola, mundo!") == ["hola", "mundo"]

class TestLimpiarTextoValidacion:
    def test_limpiar_texto_validacion_basic(self):
        assert limpiar_texto_validacion("HÓLA MUNDO") == "hola mundo"

    def test_limpiar_texto_validacion_acentos(self):
        assert limpiar_texto_validacion("José María García") == "jose maria garcia"

    def test_limpiar_texto_validacion_special_chars(self):
        assert limpiar_texto_validacion("Documento: 123-456.789!") == "documento 123456789"

    def test_limpiar_texto_validacion_empty(self):
        assert limpiar_texto_validacion("") == ""

class TestFuzzyRatio:
    def test_fuzzy_ratio_exact(self):
        assert fuzzy_ratio("test", "test") == 1.0

    def test_fuzzy_ratio_different(self):
        assert fuzzy_ratio("test", "abcd") < 1.0

class TestScoreDocument:
    def test_score_document_full_match(self):
        result = score_document("123456789", "documento 123456789 encontrado")
        assert result["puntos"] == 20
        assert result["coincidencia"] == "full"

    def test_score_document_first6_match(self):
        result = score_document("123456789", "documento 123456 encontrado")
        assert result["puntos"] == 15
        assert result["coincidencia"] == "first6"

    def test_score_document_no_match(self):
        result = score_document("123456789", "otro documento")
        assert result["puntos"] == 0

class TestScoreNombre:
    def test_score_nombre_exact_match(self):
        result = score_nombre("juan perez", "juan perez vive aqui")
        assert result["puntos"] == 80
        assert "juan" in result["tokens_encontrados"]
        assert "perez" in result["tokens_encontrados"]

    def test_score_nombre_exact_match_only(self):
        # Sin fuzzy matching: "juan" no encuentra "juanito" (debe ser exacto)
        result = score_nombre("juan", "juanito vive aqui")
        # Como no hay match exacto, no obtiene puntos
        assert result["puntos"] == 0
        assert len(result["tokens_encontrados"]) == 0
        assert len(result["tokens_fallidos"]) == 1
        assert result["tokens_fallidos"][0] == "juan"

    def test_score_nombre_no_match(self):
        result = score_nombre("juan", "pedro vive aqui")
        assert result["puntos"] == 0

class TestDocumentPenalty:
    def test_document_penalty_with_doc(self):
        doc_info = {"puntos": 20}
        assert document_penalty(doc_info) == 0

    def test_document_penalty_no_doc(self):
        doc_info = {"puntos": 0}
        assert document_penalty(doc_info) == -20

class TestVerificarPersona:
    def test_verificar_persona_full_match(self):
        result = verificar_persona(
            nombre="juan perez",
            documento="123456789",
            texto_limpio="juan perez documento 123456789"
        )
        assert result["score"] == 100
        assert result["componentes"]["documento"] == 20
        assert result["componentes"]["nombre"] == 80
        assert result["componentes"]["penalizacion_documento"] == 0

    def test_verificar_persona_partial_match(self):
        result = verificar_persona(
            nombre="juan",
            documento="123456789",  # Documento completo
            texto_limpio="juan documento 123456"  # Solo primeros 6 dígitos en texto
        )
        # 80 (nombre completo) + 15 (primeros 6 dígitos) + 0 penalización = 95
        assert result["score"] == 95
        assert result["componentes"]["documento"] == 15
        assert result["componentes"]["nombre"] == 80
        assert result["componentes"]["penalizacion_documento"] == 0

    def test_verificar_persona_no_match(self):
        result = verificar_persona(
            nombre="pedro",
            documento="999999999",
            texto_limpio="juan documento 123456"
        )
        assert result["score"] == 0

    def test_verificar_persona_nombre_only_penalty(self):
        # Caso importante: nombre completo pero sin documento -> penalización
        result = verificar_persona(
            nombre="juan perez",
            documento="999999999",
            texto_limpio="juan perez vive aqui sin documento"
        )
        assert result["score"] == 60  # 80 nombre + 0 documento - 20 penalización = 60

    def test_verificar_persona_documento_only(self):
        # Solo documento, sin nombre
        result = verificar_persona(
            nombre="xxx",
            documento="123456789",
            texto_limpio="documento 123456789 sin nombre"
        )
        assert result["score"] == 20  # 0 nombre + 20 documento + 0 penalización