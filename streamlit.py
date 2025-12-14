import streamlit as st
import pandas as pd
import tempfile
import os
import io


#Importar funciones de otros modulos
from main_simple import extraer_texto_pdf, separar_declaraciones, limpiar_lineas
from main_simple import localizar_template  # for template search logic
from productos import ProductExtractor
from  procesador_universal import procesar_factura

# ------------------------------------------
# CONFIGURACION DE PAGINA Y ESTILOS
# ------------------------------------------
st.set_page_config(
    page_title="Comparador de Importaciones",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inyectar CSS personalizado y fuentes
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    /* Color de fondo principal */
    .stApp {
        background-color: #F8FAFC; /* Gris muy claro, casi blanco */
    }
    
    /* Header Principal Personalizado */
    .main-header {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
        border-left: 6px solid #1E3A8A;
    }
    .main-header h1 {
        color: #1E3A8A;
        margin: 0;
        font-size: 2rem;
    }
    .main-header p {
        color: #64748B;
        margin-top: 0.5rem;
    }

    /* Estilo para los títulos de sección estándar de Streamlit */
    h1, h2, h3 {
        color: #1E3A8A !important;
        font-weight: 600;
    }
    
    /* Cards para secciones */
    div.block-container {
        padding-top: 2rem;
    }
    
    /* Estilo de los File Uploaders */
    section[data-testid="stFileUploader"] {
        background-color: #FFFFFF;
        padding: 2rem;
        border-radius: 12px;
        border: 2px dashed #CBD5E1;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: border-color 0.3s;
    }
    section[data-testid="stFileUploader"]:hover {
        border-color: #1E3A8A;
    }
    
    /* Forzar texto oscuro en el uploader incluso si el tema base falla */
    section[data-testid="stFileUploader"] small, 
    section[data-testid="stFileUploader"] span,
    section[data-testid="stFileUploader"] div {
        color: #334155 !important; 
    }
    
    /* Hack para el botón interno del uploader para que se vea bien */
    section[data-testid="stFileUploader"] button {
        background-color: #F1F5F9;
        color: #1E3A8A;
        border-color: #CBD5E1;
    }

    /* Tablas */
    div[data-testid="stDataFrame"] {
        background-color: #FFFFFF;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* Centrar encabezados de tabla */
    th {
        text-align: center !important;
        vertical-align: middle !important;
        text-transform: capitalize; /* Refuerzo visual */
        color: #1E3A8A !important;
    }
    td {
        color: #1E293B !important;
    }

    /* Ajuste de contenedores expander */
    div[data-testid="stExpander"] {
        background-color: #FFFFFF;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
    }
    
    /* Botones primarios */
    button[kind="primary"] {
        background-color: #1E3A8A !important;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# Header visible en la app
st.markdown("""
<div class="main-header">
    <p>Sube tus archivos PDF para extraer, procesar y comparar datos de importación automáticamente. <span style="font-size:0.8rem; color:#94a3b8; float:right;">v2.9.1 (Light Fix)</span></p>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------
# CONFIG: template path (auto‑fallback-ready)
# ------------------------------------------
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
    # print(texto) # DEBUG removed for production
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

    #*******************************************************
    # Extraer productos usando script productos.py
    #*******************************************************
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

    # Usar splitext para manejar .pdf y .PDF correctamente
    nombre_base = os.path.splitext(nombre_pdf)[0]
    excel_path = os.path.join(folder, f"{nombre_base}.xlsx")

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        if not df_decl.empty:
            df_decl.to_excel(writer, sheet_name="Declaraciones", index=False)
        if not df_prod.empty:
            df_prod.to_excel(writer, sheet_name="Productos", index=False)

    return excel_path



# ------------------------------------------
# STREAMLIT UI
# ------------------------------------------


# Crear dos columnas

col1, col2 = st.columns(2)

#with col1:
st.subheader("📥 Declaraciones en Descargas")
    
subir_declaracion = st.file_uploader("Sube PDFs", type=["pdf"], accept_multiple_files=True)

if subir_declaracion:
    for idx, f in enumerate(subir_declaracion):

        df_decl, df_prod, texto = procesar_pdf_filelike(f)

        # Función para convertir correctamente los números (Lógica robusta)
        import re
        def convertir_numero(valor):
            if pd.isna(valor) or valor == "" or valor is None:
                return None
            
            s = str(valor).strip()
            # Dejar solo dígitos, puntos, comas y signo menos
            s = re.sub(r'[^\d.,-]', '', s)
            if not s: return None

            last_comma = s.rfind(',')
            last_point = s.rfind('.')

            try:
                # Caso A: No hay separadores -> Entero
                if last_comma == -1 and last_point == -1:
                    return float(s)

                # Caso B: Punto está después de coma (o no hay coma) -> Formato 1,234.56
                # El punto es el decimal.
                if last_point > last_comma:
                    # Eliminar todas las comas (separadores de miles)
                    clean_s = s.replace(',', '')
                    # Asegurar que solo hay un punto (el último)
                    # Si input era 1.234.567.89 -> 1234567.89
                    # Split por punto
                    parts = clean_s.split('.')
                    if len(parts) > 2:
                        # Unir todo menos el último decimal
                        integer_part = "".join(parts[:-1])
                        decimal_part = parts[-1]
                        clean_s = f"{integer_part}.{decimal_part}"
                    
                    return float(clean_s)
                
                # Caso C: Coma está después de punto (o no hay punto) -> Formato 1.234,56
                # La coma es el decimal.
                else: 
                     # Eliminar todos los puntos (separadores de miles)
                    clean_s = s.replace('.', '')
                    # Reemplazar la coma decimal por punto para Python
                    parts = clean_s.split(',')
                    if len(parts) > 2:
                        integer_part = "".join(parts[:-1])
                        decimal_part = parts[-1]
                        # Reemplazar ultima coma por punto
                        clean_s = f"{integer_part}.{decimal_part}"
                    else:
                        clean_s = clean_s.replace(',', '.')
                    
                    return float(clean_s)

            except (ValueError, TypeError):
                return None
        
        # Función para formatear números
        def formatear_numero(valor):
            if pd.isna(valor) or valor is None:
                return ""
            try:
                num = float(valor)
                # Formato solicitado: decimales con punto
                return f"{num:,.2f}" # 1,234.56
            except (ValueError, TypeError):
                return str(valor) if valor else ""
        
        # Aplicar conversión a columnas numéricas probables
        columnas_numericas = []
        for col in df_decl.columns:
            col_upper = str(col).upper()
            if any(k in col_upper for k in ['VALOR', 'USD', 'FLETES', 'SEGUROS', 'GASTOS', 'AJUSTE', 'PESO', 'TASA', 'ARANCEL', 'IVA', 'LIQUIDADO', 'BASE']):
                columnas_numericas.append(col)
                df_decl[col] = df_decl[col].apply(convertir_numero)
        
        # Calcular valor seguros (necesita VALOR FOB numerico)
        if "VALOR FOB USD" in df_decl.columns:
             fob_series = df_decl['VALOR FOB USD'].fillna(0.0)
             df_decl['valor_calculado'] = (fob_series * 0.00085).round(2)
             columnas_numericas.append('valor_calculado')

        # Preparar DF para display
        df_decl_display = df_decl.copy()
        
        # Capitalizar columnas para visualización
        df_decl_display.columns = [str(c).title() for c in df_decl_display.columns]

        # Formatear columnas numéricas para visualización (1,234.56)
        # IMPORTANTE: Al renombrar columnas, el mapeo original se pierde si no ajustamos columnas_numericas
        # Primero formateamos, y LUEGO renombramos para evitar líos, O ajustamos la lógica.
        # Mejor estrategia: Formatear PRIMERO (líneas anteriores), LUEGO Capitalizar justo antes de mostrar.
        # Pero espera, el código original formatea sobre df_decl_display.
        
        # Corrección: El código original ya tenía df_decl_display.
        # Vamos a insertar la capitalización JUSTO ANTES de mostrar los dataframes y los selectores.
        
        # ---- REEMPLAZO INTELIGENTE BLOQUE COMPLETO DESDE LA COPIA ----
        
        # Formatear columnas numéricas para visualización (1,234.56)
        for col in columnas_numericas:
            if col in df_decl_display.columns:
                df_decl_display[col] = df_decl_display[col].apply(formatear_numero)

        # with col1:
        st.write("### 📄 Declaración formateada")
        
        # Capitalizar nombres de columnas para el selector y visualización
        df_display_final = df_decl_display.copy()
        df_display_final.columns = [str(c).title() for c in df_display_final.columns]
        
        # Selector de columnas en expander
        with st.expander("🔧 Seleccionar columnas a mostrar"):
            columnas_decl_seleccionadas = st.multiselect(
                "Columnas", 
                df_display_final.columns.tolist(),
                default=df_display_final.columns.tolist(),
                key=f"multiselect_declaraciones_{idx}",
                label_visibility="collapsed"
            )
        
        # Mostrar solo columnas seleccionadas
        if columnas_decl_seleccionadas:
            st.dataframe(df_display_final[columnas_decl_seleccionadas], use_container_width=True)
        else:
            st.dataframe(df_display_final, use_container_width=True)
        
        # Botón de descarga para declaraciones (usa el DF original sin capitalizar headers si así se desea, o capitalizado?)
        # User request "colocar los nombres de los campos con mayuscyla inicial y centrados" -> likely for display. 
        # Excel usually keeps original keys unless specified. keeping output clean.
        
        if not df_decl.empty:
            from io import BytesIO
            buffer_decl = BytesIO()
            with pd.ExcelWriter(buffer_decl, engine='openpyxl') as writer:
                # Si quiere que el excel también tenga mayusculas, descomentar:
                # df_decl_export = df_decl.copy()
                # df_decl_export.columns = [c.title() for c in df_decl_export.columns]
                # df_decl_export.to_excel...
                df_decl.to_excel(writer, sheet_name='Declaraciones', index=False)
            buffer_decl.seek(0)
            
            nombre_base = os.path.splitext(f.name)[0]
            st.download_button(
                label="📥 Descargar Declaraciones en Excel",
                data=buffer_decl,
                file_name=f"{nombre_base}_declaraciones.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_decl_{idx}"
            )
        
        # with col2:
        st.write("### 📊 Productos encontrados")
        
        # Capitalizar columnas productos visualización
        df_prod_display = df_prod.copy()
        df_prod_display.columns = [str(c).title() for c in df_prod_display.columns]

        # Selector de columnas en expander
        with st.expander("🔧 Seleccionar columnas a mostrar"):
            columnas_prod_seleccionadas = st.multiselect(
                "Columnas", 
                df_prod_display.columns.tolist(),
                default=df_prod_display.columns.tolist(),
                key=f"multiselect_productos_{idx}",
                label_visibility="collapsed"
            )
        
        # Mostrar solo columnas seleccionadas
        if columnas_prod_seleccionadas:
            st.dataframe(df_prod_display[columnas_prod_seleccionadas], use_container_width=True)
        else:
            st.dataframe(df_prod_display, use_container_width=True)
        
        # Botón de descarga para productos
        if not df_prod.empty:
            from io import BytesIO
            buffer_prod = BytesIO()
            with pd.ExcelWriter(buffer_prod, engine='openpyxl') as writer:
                df_prod.to_excel(writer, sheet_name='Productos', index=False)
            buffer_prod.seek(0)
            
            nombre_base = os.path.splitext(f.name)[0]
            st.download_button(
                label="📥 Descargar Productos en Excel",
                data=buffer_prod,
                file_name=f"{nombre_base}_productos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_prod_{idx}"
            )
        

        # Guardar Excel igual a main_simple
        saved_path = guardar_excel_por_pdf(f.name, df_decl, df_prod)
        st.success(f"Excel generado: {saved_path}")

# with col2:
    st.subheader("📄 Facturas")    
    subir_factura = st.file_uploader("Sube PDFs de Facturas", type=["pdf"], accept_multiple_files=True, key="facturas")
    
    if subir_factura:
        for f in subir_factura:
            # Guardar archivo temporalmente para procesar
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(f.read())
                temp_path = tmp.name
            
            # Procesar factura
            df = procesar_factura(temp_path)
            
            if df is not None and not df.empty:
                st.write(f"### 📋 Factura procesada: {f.name}")
                st.write(f"**Productos encontrados:** {len(df)}")
                st.write(f"**Campos detectados:** {len(df.columns)}")
                
                # Mostrar columnas detectadas
                with st.expander("Ver campos detectados"):
                    st.write(", ".join(df.columns.tolist()))
                
                # Capitalizar columnas para visualización
                df_factura_display = df.copy()
                df_factura_display.columns = [str(c).title() for c in df_factura_display.columns]

                # Selector de columnas para mostrar
                columnas_seleccionadas = st.multiselect(
                    "Selecciona las columnas a mostrar", 
                    df_factura_display.columns.tolist(),
                    default=df_factura_display.columns.tolist(),
                    key=f"cols_{f.name}"
                )
                
                if columnas_seleccionadas:
                    st.dataframe(df_factura_display[columnas_seleccionadas], use_container_width=True)
                else:
                    st.dataframe(df_factura_display, use_container_width=True)
                
                # Guardar Excel con estructura dinámica
                folder = os.path.join(os.getcwd(), "PDF_A_LEER", "EXCEL_PDF_LEIDOS")
                os.makedirs(folder, exist_ok=True)
                
                # Usar splitext para manejar .pdf y .PDF correctamente
                nombre_base = os.path.splitext(f.name)[0]
                excel_path = os.path.join(folder, f"{nombre_base}_factura.xlsx")
                
                df.to_excel(excel_path, index=False, sheet_name="Productos")
                st.success(f"✅ Excel guardado: {excel_path}")
                
                # Botón de descarga
                with open(excel_path, "rb") as file:
                    st.download_button(
                        label="⬇️ Descargar Excel",
                        data=file,
                        file_name=f"{f.name.replace('.pdf', '')}_factura.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"download_{f.name}"
                    )
                
                # Limpiar archivo temporal
                os.unlink(temp_path)
            else:
                st.warning(f"⚠️ No se pudo procesar la factura: {f.name}")
                # Limpiar archivo temporal
                os.unlink(temp_path)