import streamlit as st
import pandas as pd
import tempfile
import os
from main_simple import extraer_texto_pdf, separar_declaraciones, limpiar_lineas
from productos import ProductExtractor
from .templating import cargar_plantilla

def procesar_pdf_filelike(file):
    """Ejecuta la lógica de main_simple con un archivo subido por Streamlit."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.read())
        temp_path = tmp.name

    # Extraer texto completo
    texto = extraer_texto_pdf(temp_path)
    declaraciones = separar_declaraciones(texto)

    # Cargar plantilla real
    plantilla = cargar_plantilla()
    headers = plantilla.columns.tolist()

    # Crear filas según plantilla
    decl_rows = []
    for decl in declaraciones:
        líneas = limpiar_lineas(decl["contenido"])
        fila = [None] * len(headers)
        for i in range(min(len(headers), len(líneas))):
            fila[i] = líneas[i]
        decl_rows.append(fila)

    df_decl = pd.DataFrame(decl_rows, columns=headers).dropna(axis=1, how="all")
    df_decl["Archivo"] = file.name

    # Extraer productos usando script productos.py
    extractor = ProductExtractor()
    try:
        df_prod = extractor.extract_products_from_text(texto, file.name)
        if df_prod is None:
            df_prod = pd.DataFrame()
    except Exception as e:
        st.error(f"Error extrayendo productos: {e}")
        df_prod = pd.DataFrame()

    return df_decl, df_prod, texto

def guardar_excel_por_pdf(nombre_pdf, df_decl, df_prod):
    """Guarda los resultados en un archivo Excel en la carpeta de salida."""
    folder = os.path.join(os.getcwd(), "PDF_A_LEER", "EXCEL_PDF_LEIDOS")
    os.makedirs(folder, exist_ok=True)

    nombre_base = os.path.splitext(nombre_pdf)[0]
    excel_path = os.path.join(folder, f"{nombre_base}.xlsx")

    # Nota: la lógica original tenía esto comentado, lo mantenemos igual por ahora
    # o podrías activarlo si el usuario lo requiere.
    return excel_path
