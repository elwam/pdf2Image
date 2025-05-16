import re

def limpiar_texto(texto: str) -> str:
    """Limpia el texto convirtiéndolo a minúsculas y eliminando espacios extra."""
    texto_limpio = texto.lower()
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()
    return texto_limpio

def clasificar_texto_por_reglas(texto_ocr: str) -> tuple[str, str]:
    """
    Clasifica el texto basado en reglas predefinidas.

    Args:
        texto_ocr (str): El texto extraído por OCR.

    Returns:
        tuple[str, str]: Una tupla conteniendo (clasificacion, texto_limpio_para_llm).
                         Si la clasificación es por reglas, texto_limpio_para_llm puede ser el texto original o limpiado.
                         Si necesita LLM, clasificación será "REVISAR_CON_LLM" y texto_limpio_para_llm será el texto para enviar al LLM.
    """
    texto_limpio_original = limpiar_texto(texto_ocr) # Limpiamos una vez para las reglas

    # Regla de autorización
    if "autorización" in texto_limpio_original or "autorizacion" in texto_limpio_original:
        return "autorizacion", texto_ocr # Devolvemos texto OCR original por si se necesita

    # Regla de soporte de recibido
    if "formato de recibido usuario" in texto_limpio_original or \
       "certifico que recibí a satisfaccion" in texto_limpio_original or \
       "certifico que recibi a satisfaccion" in texto_limpio_original:
        return "soporte_de_recibido", texto_ocr

    # Regla de orden médica
    palabras_clave_orden = [
        "orden médica", "orden medica", "plan de manejo", "consulta externa",
        "diagnóstico", "diagnostico", "observaciones", "cita de control",
        "consulta especializada", "formulación", "formulacion", "remisión", "remision"
    ]
    codigos_medicos_regex = r"\b([A-Z][0-9]{2,6}|[A-Z]{2,3}[0-9]{1,4})\b" # Ajusta según necesidad

    # Para las palabras clave, usamos el texto limpiado (minúsculas)
    # Para el regex de códigos, es mejor usar el texto OCR original si la capitalización importa
    if any(clave in texto_limpio_original for clave in palabras_clave_orden) or \
       re.search(codigos_medicos_regex, texto_ocr, re.IGNORECASE):
        return "orden_medica", texto_ocr

    # Si ninguna regla coincide, indicamos que necesita revisión por LLM
    # Devolvemos el texto OCR original para el LLM
    return "REVISAR_CON_LLM", texto_ocr


def limpiar_texto_factura(texto: str) -> str:
    """Limpia el texto convirtiéndolo a minúsculas y eliminando espacios extra."""
    texto_limpio = texto.lower()
    # Reemplazar saltos de línea y tabulaciones con espacios para normalizar
    texto_limpio = re.sub(r'[\n\t]+', ' ', texto_limpio)
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()
    return texto_limpio


def clasificar_factura_examenes(texto_factura: str) -> dict:
    """
    Analiza el texto de una factura para determinar si contiene ítems de exámenes médicos.

    Args:
        texto_factura (str): El texto extraído de la factura.

    Returns:
        dict: Un diccionario con la clasificación.
              Si no se puede identificar con reglas:
              {"examenesFacturados": -1, "decision_source": "REVISAR_CON_LLM", "texto_limpio": "..."}
              Si se identifica por reglas:
              {"examenesFacturados": 0 o 1, "decision_source": "rules_...", "texto_limpio": "..."}
    """
    texto_limpio = limpiar_texto_factura(texto_factura)

    # Indicador primario muy fuerte
    if "procedimientos diagnostico" in texto_limpio:
        return {"examenesFacturados": 1, "decision_source": "rules_procedimientos_diagnostico", "texto_limpio": texto_limpio}

    palabras_clave_examenes = [
        "radiografia", "radiografía", "rayos x",
        "ecografia", "ecografía", "ultrasonido",
        "tomografia", "tomografía", "tac",
        "resonancia magnetica", "resonancia magnética", "rmn",
        "mamografia", "mamografía",
        "hemoglobina", "hematocrito", "cuadro hematico", "hemograma",
        "glicemia", "glucosa", "hemoglobina glicosilada",
        "colesterol", "trigliceridos", "triglicéridos", "perfil lipidico", "perfil lipídico",
        "parcial de orina", "uroanalisis", "uroanálisis",
        "creatinina", "bun", "nitrogeno ureico",
        "cultivo", "antibiograma",
        "biopsia",
        "electrocardiograma", "ekg",
        "electroencefalograma", "eeg",
        "prueba de esfuerzo",
        "doppler",
        "endoscopia", "colonoscopia",
        "antigeno prostatico", "antígeno prostático", "psa",
        "microalbuminuria",
        "potasio", "sodio", "electrolitos", "electrólitos"
        # Añade más según los tipos de exámenes que suelas encontrar
    ]

    encontrada_palabra_clave_examen = any(clave in texto_limpio for clave in palabras_clave_examenes)

    if encontrada_palabra_clave_examen:
        # Si encontramos palabras clave de exámenes, revisamos si "consultas" es dominante
        # y "procedimientos diagnostico" no está (ya cubierto arriba).
        if "consultas" in texto_limpio and "procedimientos diagnostico" not in texto_limpio:
             # Palabras de examen presentes, pero "consultas" también y sin "procedimientos diagnostico".
             # Decidimos que "consultas" tiene más peso en este escenario para marcarla como NO examen.
            return {"examenesFacturados": 0, "decision_source": "rules_consultas_sobre_exam_keywords", "texto_limpio": texto_limpio}
        # Si no, y hay palabras clave de examen, es examen.
        return {"examenesFacturados": 1, "decision_source": "rules_palabras_clave_examen", "texto_limpio": texto_limpio}

    # Si la palabra "consultas" está presente y NINGUNA palabra clave de examen fue encontrada
    if "consultas" in texto_limpio: # y no encontrada_palabra_clave_examen (implícito por el flujo)
        return {"examenesFacturados": 0, "decision_source": "rules_solo_consultas", "texto_limpio": texto_limpio}
        
    # Si no se cumple ninguna de las condiciones anteriores, no podemos identificarla con reglas.
    # Marcamos para revisión con LLM.
    return {"examenesFacturados": -1, "decision_source": "REVISAR_CON_LLM", "texto_limpio": texto_limpio}