import re

def limpiar_texto(texto: str) -> str:
    if not texto:
        return ""
    texto_limpio = texto.lower()
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip() # Elimina espacios extra y convierte a minúsculas
    return texto_limpio

def clasificar_texto_por_reglas(texto_original_de_fuente: str) -> tuple[str, str]:
    """
    Clasifica el texto basado en reglas predefinidas.
    Devuelve (clasificacion, texto_para_siguiente_paso).
    - Si la clasificacion es por reglas: (categoria, texto_original_de_fuente)
    - Si necesita LLM: ("REVISAR_CON_LLM", texto_limpio_para_llm)
    - Si el texto es vacío/inválido: ("sin_clasificacion", "") o ("documento_vacio", "")
    """
    # --- AJUSTE PARA TEXTO VACÍO O SOLO ESPACIOS ---
    if not texto_original_de_fuente or texto_original_de_fuente.isspace():
        return "sin_clasificacion", "" # O "documento_vacio", ""

    # Limpiamos el texto para la comparación de keywords
    # Guardamos el original para devolverlo si la clasificación es por reglas (para auditoría)
    texto_limpio_para_reglas = limpiar_texto(texto_original_de_fuente)

    # Regla de autorización
    if "autorización" in texto_limpio_para_reglas or "autorizacion" in texto_limpio_para_reglas:
        return "autorizacion", texto_original_de_fuente

    # Regla de soporte de recibido
    # Normalizamos la búsqueda de "satisfaccion"
    palabras_clave_recibido = [
        "formato de recibido usuario",
        "certifico que recibí a satisfaccion", # con tilde
        "certifico que recibi a satisfaccion"  # sin tilde
    ]
    if any(clave in texto_limpio_para_reglas for clave in palabras_clave_recibido):
        return "soporte_de_recibido", texto_original_de_fuente

    # Regla de orden médica
    palabras_clave_orden = [
        "orden médica", "orden medica", "plan de manejo", "consulta externa",
        "diagnóstico", "diagnostico", "observaciones", "cita de control",
        "consulta especializada", "formulación", "formulacion", "remisión", "remision"
    ]
    
    # Aplicar regex de códigos al texto original (case-insensitive) ya que los códigos pueden tener mayúsculas/minúsculas
    # y la limpieza a minúsculas podría perder esa distinción si no se maneja el regex apropiadamente.
    # El patrón que tenías es bueno para esto: r"\b([A-Z][0-9]{2,6}|[A-Z]{2,3}[0-9]{1,4})\b"
    encontro_codigo_medico = re.search(r"\b([A-Z][0-9]{2,6}|[A-Z]{2,3}[0-9]{1,4})\b", texto_original_de_fuente, re.IGNORECASE)

    if any(clave in texto_limpio_para_reglas for clave in palabras_clave_orden) or encontro_codigo_medico:
        return "orden_medica", texto_original_de_fuente

    # Si ninguna regla coincide, indicamos que necesita revisión por LLM.
    # Devolvemos el texto LIMPIO para el LLM, que ya tenemos en texto_limpio_para_reglas.
    return "REVISAR_CON_LLM", texto_limpio_para_reglas


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