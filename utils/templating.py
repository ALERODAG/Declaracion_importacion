import pandas as pd
import os

TEMPLATE_CANDIDATES = [
    os.path.join(os.getcwd(), "RESULTADO_FORMATO_DECLARACION.xlsx"),
    os.path.join(os.getcwd(), "plantillas", "RESULTADO_FORMATO_DECLARACION.xlsx"),
]

def cargar_plantilla():
    """Carga la plantilla desde varias rutas posibles."""
    for path in TEMPLATE_CANDIDATES:
        if os.path.exists(path):
            return pd.read_excel(path)
    raise FileNotFoundError("No se encontró la plantilla en rutas alternativas.")
