# =================================
#   factura_sofabex.py (MODULAR)
# =================================

import pdfplumber
import pandas as pd
import re

# -----------------------------
#   Extraer líneas
# -----------------------------
def extraer_lineas(pdf_path):
    lineas = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(
                keep_blank_chars=False,
                use_text_flow=False
            )

            agrupadas = {}
            for w in words:
                y = round(w["top"] / 3) * 3
                agrupadas.setdefault(y, []).append(w)

            for y in sorted(agrupadas.keys()):
                linea = sorted(agrupadas[y], key=lambda w: w["x0"])
                lineas.append(linea)

    return lineas


# -----------------------------
#   Detección formato (simple)
# -----------------------------
def detectar_formato(lineas):
    texto = " ".join([" ".join(w["text"] for w in ln) for ln in lineas])
    if "Cantidad" in texto or "TENSOR" in texto:
        return "es"
    if "ITEM" in texto:
        return "en"
    if "Libellé" in texto:
        return "fr"
    return "es"


# -----------------------------
#   Parser español
# -----------------------------
def parse_es(lineas):
    patron = re.compile(
        r"^\s*(\d+)\s+([A-Z0-9\-]+)\s+([A-Z0-9\-]*)?\s+(.+?)\s+([A-Z]{2,10})?\s+(\d{1,10})\s+(\d+[,\.]\d+)$"
    )

    filas = []

    for ln in lineas:
        linea = " ".join(w["text"] for w in ln)
        m = patron.match(linea)
        if m:
            cantidad = int(m.group(6))
            precio = float(m.group(7).replace(",", "."))

            filas.append({
                "LN": m.group(1),
                "Código": m.group(2),
                "Código2": m.group(3) or "",
                "Descripción": m.group(4),
                "Marca": m.group(5) or "",
                "Cantidad": cantidad,
                "Precio": precio,
                "Total": cantidad * precio
            })

    return pd.DataFrame(filas)


# -----------------------------
#   FUNCIÓN PRINCIPAL (MODULAR)
# -----------------------------
def procesar_factura_sofabex(pdf_path: str):
    lineas = extraer_lineas(pdf_path)
    formato = detectar_formato(lineas)

    if formato != "es":
        return None  # No es Sofabex

    df = parse_es(lineas)
    if df.empty:
        return None

    return df
