import streamlit as st
import pandas as pd
import tempfile
import os
import io

#Importar funciones de otros modulos
from main_simple import extraer_texto_pdf, separar_declaraciones, limpiar_lineas
from main_simple import localizar_template  # for template search logic
from productos import ProductExtractor
from facturas_gate import main

# ------------------------------------------
# CONFIG: template path (auto‑fallback-ready)
# ------------------------------------------
TEMPLATE_CANDIDATES = [
    r"C:/Users/asus/Documents/Declaracion-de-importacion_V_290/RESULTADO_FORMATO_DECLARACION.xlsx",
    os.path.join(os.getcwd(), "RESULTADO_FORMATO_DECLARACION.xlsx"),
    os.path.join(os.getcwd(), "plantillas", "RESULTADO_FORMATO_DECLARACION.xlsx"),
]

def cargar_plantilla():
    """Carga la plantilla desde varias rutas posibles."""
    for path in TEMPLATE_CANDIDATES:
        if os.path.exists(path):
            return pd.read_excel(path)
    raise FileNotFoundError("No se encontró la plantilla en rutas alternativas.")

# ------------------------------------------
# Procesar un PDF “file-like“
# ------------------------------------------
def procesar_pdf_filelike(file):
    """Ejecuta la lógica de main_simple con un archivo subido por Streamlit."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.read())
        temp_path = tmp.name

    # Extraer texto completo
    texto = extraer_texto_pdf(temp_path)

    # Separar declaraciones usando lógica original
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

# ------------------------------------------
# Guardar Excel igual que main_simple
# ------------------------------------------
def guardar_excel_por_pdf(nombre_pdf, df_decl, df_prod):
    folder = os.path.join(os.getcwd(), "PDF_A_LEER", "EXCEL_PDF_LEIDOS")
    os.makedirs(folder, exist_ok=True)

    excel_path = os.path.join(folder, nombre_pdf.replace(".pdf", ".xlsx"))

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        if not df_decl.empty:
            df_decl.to_excel(writer, sheet_name="Declaraciones", index=False)
        if not df_prod.empty:
            df_prod.to_excel(writer, sheet_name="Productos", index=False)

    return excel_path


#==============================================
# Procesar Facturas (esta sección necesita ser integrada en el flujo principal)
#==============================================
# facturas = process_multiple_pdfs([temp_path])  # Comentado hasta integrar correctamente

# ------------------------------------------
# STREAMLIT UI
# ------------------------------------------


# Crear dos columnas
st.write("<h2 style='text-align: center;'>Procesamiento Declaraciones & Productos</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    
    subir_declaracion = st.file_uploader("Sube PDFs", type=["pdf"], accept_multiple_files=True)

if subir_declaracion:
    for f in subir_declaracion:
        st.subheader(f"Procesando: {f.name}")

        df_decl, df_prod, texto = procesar_pdf_filelike(f)

        # with col1:
        st.write("### 📄 Declaración formateada")
        st.dataframe(df_decl)
        # with col2:
        st.write("### 📊 Productos encontrados")
        st.dataframe(df_prod)  

        # Guardar Excel igual a main_simple
        saved_path = guardar_excel_por_pdf(f.name, df_decl, df_prod)
        st.success(f"Excel generado: {saved_path}")

with col2:
        st.file_uploader("Sube la factura")
   