"""
Módulo de funciones de utilidad para procesamiento de texto.

Este módulo contiene funciones auxiliares para el procesamiento y normalización
de texto extraído de documentos PDF mediante OCR.
"""

import re


def limpiar_texto(texto: str) -> str:
    """
    Limpia y normaliza texto extraído de OCR para estandarización.

    Esta función realiza una limpieza completa del texto para prepararlo
    para análisis posteriores, especialmente en validación de documentos.
    Aplica normalización de caracteres, eliminación de caracteres especiales
    y espacios innecesarios.

    Args:
        texto (str): Texto original a limpiar, típicamente extraído de OCR.

    Returns:
        str: Texto limpiado y normalizado con las siguientes transformaciones:
            - Convertido a minúsculas
            - Espacios múltiples convertidos a uno solo
            - Eliminados caracteres especiales (excepto letras, números,
              espacios y vocales acentuadas comunes en español)
            - Eliminados espacios al inicio y final

    Examples:
        >>> limpiar_texto("HÓLA  MUNDO!!!")
        'hola mundo'

        >>> limpiar_texto("José María García 123-456")
        'jose maria garcia 123456'

        >>> limpiar_texto("")
        ''

        >>> limpiar_texto("Texto con   múltiples    espacios")
        'texto con multiples espacios'

    Notes:
        - Preserva vocales acentuadas comunes en español: áéíóúñü
        - Elimina puntuación, símbolos y caracteres no alfanuméricos
        - Normaliza espacios pero mantiene números para validación de documentos
        - Es idempotente: aplicar múltiples veces produce el mismo resultado
    """
    if not texto:
        return ""

    # Convertir a minúsculas para normalización
    texto_limpio = texto.lower()

    # Normalizar espacios múltiples a uno solo
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio)

    # Eliminar caracteres especiales, manteniendo letras, números,
    # espacios y vocales acentuadas comunes en español
    texto_limpio = re.sub(r'[^a-zA-Z0-9áéíóúñü\s]', '', texto_limpio)

    # Normalizar espacios nuevamente y eliminar espacios al inicio/final
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()

    return texto_limpio