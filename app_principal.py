import streamlit as st
import os

# Importar componentes de UI y Tabs
from utils.ui_components import inject_custom_css, render_header
from utils.tabs.declarations import render_declarations_tab
from utils.tabs.invoices import render_invoices_tab
from utils.tabs.comparison import render_comparison_tab

# ------------------------------------------
# CONFIGURACION DE PAGINA
# ------------------------------------------
st.set_page_config(
    page_title="Comparador de Importaciones",
    layout="wide",
    initial_sidebar_state="expanded"
    
)

# Estilos y Header
inject_custom_css()
render_header()

# ------------------------------------------
# SIDEBAR: Carga de Archivos
# ------------------------------------------
with st.sidebar:
    if os.path.exists("Logo.png"):
        st.image("Logo.png")
    else:
        st.title("ImportApp")
        
    st.markdown("---")
    st.subheader("📁 Carga de Archivos")
    
    subir_declaracion = st.file_uploader(
        "Declaraciones (PDF)", 
        type=["pdf"], 
        accept_multiple_files=True,
        help="Sube uno o varios archivos de declaración de importación"
    )
    
    subir_factura = st.file_uploader(
        "Facturas (PDF)", 
        type=["pdf"], 
        accept_multiple_files=True,
        key="facturas_sidebar",
        help="Sube las facturas comerciales relacionadas"
    )
    
    st.markdown("---")
    if subir_declaracion:
        st.success(f"{len(subir_declaracion)} Declaraciones")
    if subir_factura:
        st.success(f"{len(subir_factura)} Facturas")

# ------------------------------------------
# MAIN AREA: Tabs
# ------------------------------------------
t_decl, t_fact, t_comp = st.tabs(["Declaraciones", "Facturas", "Comparativa"])

with t_decl:
    render_declarations_tab(subir_declaracion)

with t_fact:
    render_invoices_tab(subir_factura)

with t_comp:
    render_comparison_tab(subir_factura, subir_declaracion)
