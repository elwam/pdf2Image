import re

def limpiar_texto(texto: str) -> str:
    if not texto:
        return ""
    texto_limpio = texto.lower()
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()
    return texto_limpio