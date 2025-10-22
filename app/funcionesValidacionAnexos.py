# funcionesValidacionAnexos.py
import re
import unicodedata
from difflib import SequenceMatcher
from typing import List, Dict, Any

# Stopwords típicas que aparecen en nombres compuestos
NAME_STOPWORDS = {"de", "del", "la", "las", "los", "y", "da", "das", "do", "dos"}


def limpiar_texto_validacion(texto: str) -> str:
    """
    Limpia y normaliza texto específicamente para validación de documentos.

    Esta función es más estricta que la función general de limpieza,
    removiendo acentos y caracteres especiales para mejorar la precisión
    en comparación de nombres y documentos.

    Args:
        texto (str): Texto a limpiar, típicamente para validación.

    Returns:
        str: Texto completamente normalizado sin acentos ni caracteres especiales.

    Examples:
        >>> limpiar_texto_validacion("José María García")
        'jose maria garcia'

        >>> limpiar_texto_validacion("Documento: 123-456.789")
        'documento 123456789'
    """
    if not texto:
        return ""

    # Convertir a minúsculas
    texto_limpio = texto.lower()

    # Remover acentos y normalizar caracteres unicode
    texto_limpio = unicodedata.normalize('NFD', texto_limpio)
    texto_limpio = ''.join(char for char in texto_limpio if unicodedata.category(char) != 'Mn')

    # Normalizar espacios
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio)

    # Mantener solo letras, números y espacios
    texto_limpio = re.sub(r'[^a-z0-9\s]', '', texto_limpio)

    # Limpiar espacios finales
    texto_limpio = texto_limpio.strip()

    return texto_limpio

def digits_only(s: str) -> str:
    """Deja solo dígitos (para comparar documentos)."""
    return re.sub(r"\D+", "", s or "")

def tokenize_words(s: str) -> List[str]:
    """Separa texto en palabras alfanuméricas, aplicando limpieza previa."""
    if not s:
        return []
    # Aplicar limpieza específica para validación antes de tokenizar
    s_limpio = limpiar_texto_validacion(s)
    return re.findall(r"\b[a-z0-9]+\b", s_limpio)

def fuzzy_ratio(a: str, b: str) -> float:
    """Similaridad difusa para tolerar OCR/typos leves."""
    return SequenceMatcher(None, a, b).ratio()

def score_document(documento: str, texto_limpio: str) -> Dict[str, Any]:
    """
    Puntaje para documento según nueva regla:
    - 20 pts si aparece el documento completo (solo dígitos).
    - 15 pts si no aparece completo, pero sí los PRIMEROS 6 dígitos.
    - 0 pts si no hay coincidencia (penalización aplicada en verificar_persona)
    """
    tgt = digits_only(documento)
    text_digits = digits_only(texto_limpio)
    res = {"puntos": 0, "coincidencia": None, "numero_encontrado": None, "pos": []}

    if not tgt:
        return res

    # Coincidencia completa
    i = text_digits.find(tgt)
    if i != -1:
        res.update(puntos=20, coincidencia="full", numero_encontrado=tgt, pos=[i])
        return res

    # Primeros 6 dígitos
    if len(tgt) >= 6:
        sub6 = tgt[:6]
        j = text_digits.find(sub6)
        if j != -1:
            res.update(puntos=15, coincidencia="first6", numero_encontrado=sub6, pos=[j])
            return res

    return res

def score_nombre(nombre: str, texto_limpio: str) -> Dict[str, Any]:
    """
    80 puntos distribuidos entre tokens útiles del nombre.
    - Solo match exacto de palabra (sin fuzzy matching)
    """
    # Aplicar limpieza específica para validación al nombre de entrada
    nombre_limpio = limpiar_texto_validacion(nombre)
    tokens = [t for t in tokenize_words(nombre_limpio) if t not in NAME_STOPWORDS and len(t) >= 2]
    if not tokens:
        return {"puntos": 0, "tokens_encontrados": [], "tokens_fallidos": [], "detalles": []}

    words = set(tokenize_words(texto_limpio))
    per_token = 80.0 / len(tokens)

    encontrados, fallidos, detalles = [], [], []
    puntos = 0.0

    for tok in tokens:
        exact = tok in words
        if exact:
            puntos += per_token
            encontrados.append(tok)
            detalles.append({"token": tok, "match": tok, "tipo": "exacto"})
        else:
            fallidos.append(tok)
            detalles.append({"token": tok, "match": None, "tipo": "no_encontrado"})

    return {
        "puntos": int(round(puntos)),
        "tokens_encontrados": encontrados,
        "tokens_fallidos": fallidos,
        "detalles": detalles
    }

def document_penalty(doc_info: Dict[str, Any]) -> int:
    """
    Penalización si no se detecta documento:
    - Si documento tiene 0 puntos, penalizar con -20 pts
    - Si tiene puntos parciales o completos, no penalizar
    """
    if doc_info.get("puntos", 0) == 0:
        return -20  # Penalización fuerte por no encontrar documento
    return 0

def verificar_persona(nombre: str, documento: str, texto_limpio: str) -> Dict[str, Any]:
    """
    Calcula score 0-100 = Nombre (80) + Documento (20) + Penalización (-20 si no hay documento).
    El objetivo es que pase con 60+ si hay buena coincidencia de nombre O documento.
    Si no se detecta documento, siempre se penaliza fuertemente.
    Solo se aceptan coincidencias exactas (sin fuzzy matching).
    """
    doc_info = score_document(documento, texto_limpio)
    nombre_info = score_nombre(nombre, texto_limpio)

    # Penalización por no encontrar documento
    penalizacion = document_penalty(doc_info)

    # Cálculo final: asegurar que esté entre 0 y 100
    total = max(0, min(100, nombre_info["puntos"] + doc_info["puntos"] + penalizacion))

    return {
        "score": int(total),
        "componentes": {
            "documento": doc_info["puntos"],
            "nombre": nombre_info["puntos"],
            "penalizacion_documento": penalizacion
        },
        "doc_match": doc_info,
        "nombre_match": nombre_info,
        "tokens_encontrados": nombre_info["tokens_encontrados"],
        "documento_encontrado": doc_info.get("numero_encontrado")
    }

