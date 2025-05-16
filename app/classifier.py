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
        dict: Un diccionario con la forma {"examenesFacturados": 1} o {"examenesFacturados": 0}.
              Podríamos añadir una clave "decision_source": "rules" para indicar que fue por reglas.
    """
    texto_limpio = limpiar_texto_factura(texto_factura)

    # Indicador primario muy fuerte
    if "procedimientos diagnostico" in texto_limpio:
        # Si encontramos esto, es muy probable que sean exámenes.
        # Podríamos añadir verificaciones adicionales si fuera necesario,
        # por ejemplo, si "consultas" también aparece prominentemente cerca,
        # pero por ahora, "procedimientos diagnostico" es un buen indicador.
        return {"examenesFacturados": 1, "decision_source": "rules", "texto_limpio": texto_limpio}

    # Palabras clave secundarias indicativas de exámenes
    # Esta lista puede crecer. Considera sinónimos o variaciones.
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

    if any(clave in texto_limpio for clave in palabras_clave_examenes):
        # Si encontramos alguna de estas palabras, pero NO "procedimientos diagnostico",
        # aún es probable que sea un examen. Sin embargo, hay que tener cuidado
        # si estas palabras pueden aparecer en contextos de consulta (ej. "discutir resultados de la ecografía").
        # Por ahora, si alguna de estas está, lo contamos como examen,
        # PERO si "consultas" es la sección dominante, "consultas" debería ganar.

        # Si "consultas" aparece de forma prominente y no "procedimientos diagnostico",
        # es menos probable que la factura sea *principalmente* de exámenes.
        if "consultas" in texto_limpio and "procedimientos diagnostico" not in texto_limpio:
             # Aquí podrías tener una lógica más compleja. Si "consultas" y alguna palabra de examen
             # aparecen, ¿qué decides? Por ahora, si "consultas" está y "proc diag" no, es 0.
            return {"examenesFacturados": 0, "decision_source": "rules_consultas_presentes", "texto_limpio": texto_limpio}
        return {"examenesFacturados": 1, "decision_source": "rules_palabras_clave_examen", "texto_limpio": texto_limpio}

    # Si la palabra "consultas" está presente y ninguna de las anteriores se cumplió
    if "consultas" in texto_limpio:
        return {"examenesFacturados": 0, "decision_source": "rules_consultas", "texto_limpio": texto_limpio}
        
    # Si no se cumple ninguna de las condiciones anteriores, asumimos que no son exámenes.
    # Opcionalmente, podrías tener un caso para enviar a LLM aquí si la confianza es baja.
    # return {"examenesFacturados": "REVISAR_CON_LLM"} # Si quisieras un fallback a LLM
    return {"examenesFacturados": 0, "decision_source": "rules_no_indicadores", "texto_limpio": texto_limpio}