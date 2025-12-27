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

    # with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    #     if not df_decl.empty:
    #         df_decl.to_excel(writer, sheet_name="Declaraciones", index=False)
    #     if not df_prod.empty:
    #         df_prod.to_excel(writer, sheet_name="Productos", index=False)

    # return excel_path



# ------------------------------------------
# STREAMLIT UI
# ------------------------------------------


# Crear dos columnas

col1, col2 = st.columns(2)

with col1:
    st.write("Columna 1")
st.subheader("📥 Declaraciones en Descargas")

subir_declaracion = st.file_uploader("Sube PDFs", type=["pdf"], accept_multiple_files=True)

if subir_declaracion:
    # --------------------------------------------------------
    # LIMPIEZA DE ESTADO (Eliminar archivos quitados)
    # --------------------------------------------------------
    # 1. Identificar claves validas actuales
    current_keys = set()
    for f in subir_declaracion:
        current_keys.add(f"data_{f.name}_{f.size}")
    
    # 2. Eliminar lo que sobre en session_state (solo claves de data_)
    for key in list(st.session_state.keys()):
        if key.startswith("data_") and key not in current_keys:
            del st.session_state[key]

    for idx, f in enumerate(subir_declaracion):
        
        # --------------------------------------------------------
        # GESTIÓN DE ESTADO (PERSISTENCIA)
        # --------------------------------------------------------
        # Usamos nombre + tamaño como clave única simple
        file_key = f"data_{f.name}_{f.size}"
        
        if file_key not in st.session_state:
            with st.spinner(f"Procesando {f.name}..."):
                # Procesar PDF (solo si no está en cache)
                d_decl, d_prod, d_text = procesar_pdf_filelike(f)
                
                # Inicializar columna Observaciones si no existe
                if "Observaciones" not in d_prod.columns:
                    d_prod["Observaciones"] = ""
                
                st.session_state[file_key] = {
                    "decl": d_decl,
                    "prod": d_prod,
                    "text": d_text
                }
        
        # Recuperar datos desde el estado
        data_stored = st.session_state[file_key]
        df_decl = data_stored["decl"]
        df_prod = data_stored["prod"]
        texto = data_stored["text"]

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

        # ---------------------------------------------------------
        # BUSQUEDA PERSONALIZADA CON HIGHLIGHT AZUL
        # ---------------------------------------------------------
        search_term = st.text_input(
            "🔍 Buscar en productos", 
            placeholder="Escribe para buscar (ej. referencia, país...)",
            key=f"search_prod_{idx}"
        ).strip()
        
        # Filtrar datos basado en búsqueda
        df_view = df_prod_display[columnas_prod_seleccionadas] if columnas_prod_seleccionadas else df_prod_display
        
        if search_term:
            # 1. Filtrar filas (case insensitive)
            mask = df_view.astype(str).apply(
                lambda x: x.str.contains(search_term, case=False)
            ).any(axis=1)
            df_view = df_view[mask]
            
            # 2. Resaltar celdas coincidentes (Azul #1E3A8A)
            try:
                # Usar applymap para pandas < 2.1, map para > 2.1 (Streamlit maneja Styler)
                def highlight_matches(val):
                    s_val = str(val) if val is not None else ""
                    if search_term.lower() in s_val.lower():
                        return 'background-color: #1E3A8A; color: white; font-weight: bold'
                    return ''
                
                # Aplicar estilo
                df_view = df_view.style.applymap(highlight_matches)
            except Exception:
                # Fallback si falla el styling (ej. version antigua pandas)
                pass

        # Mostrar solo columnas seleccionadas y manejar selección
        # df_view ya está filtrado y estilado si aplica
        
        # Intentar usar on_select (Streamlit >= 1.35)
        try:
            event = st.dataframe(
                df_view,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row",
                key=f"df_prod_sel_{idx}"
            )
            
            # Si hay selección, mostrar editor DEBAJO de la tabla (No modal)
            if event.selection.rows:
                selected_idx_view = event.selection.rows[0]
                
                # Obtener mapeo al indice original
                row_data_view = df_view.iloc[selected_idx_view]
                original_index = row_data_view.name 
                row_original = df_prod.loc[original_index]
                
                # -----------------------------------------------------
                # AREA DE EDICIÓN INDEPENDIENTE
                # -----------------------------------------------------
                st.markdown("---")
                with st.container(border=True):
                    st.write(f"✏️ **Editando observación para:** {row_original.get('Producto', 'Producto')} - *{row_original.get('Referencia', 'SN')}*")
                    
                    # Usamos un key único combinando file_key e indice para el text_area
                    # Importante: Inicializar value con el valor actual del session_state
                    current_obs_val = row_original.get("Observaciones", "")
                    if pd.isna(current_obs_val): current_obs_val = ""
                    
                    new_obs_val = st.text_area(
                        "Observación", 
                        value=str(current_obs_val), 
                        height=100, 
                        key=f"obs_input_{file_key}_{original_index}",
                        label_visibility="collapsed",
                        placeholder="Escribe aquí la observación para este producto..."
                    )
                    
                    if st.button("💾 Guardar Observación", key=f"btn_save_{file_key}_{original_index}", type="primary"):
                        # Guardar en session_state
                        st.session_state[file_key]["prod"].at[original_index, "Observaciones"] = new_obs_val
                        st.success("✅ Observación guardada")
                        # No hacemos rerun forzoso para no perder el foco visual bruscamente, o sí para ver el cambio reflejado en tabla?
                        # Si reruneamos, la tabla se actualiza.
                        st.rerun()

        except TypeError:
            # Fallback para versiones anteriores
            st.dataframe(df_view, use_container_width=True)
            st.info("ℹ️ Actualiza Streamlit para habilitar la edición de observaciones.")
        
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
        all_invoices = []
        
        # 1. Procesamiento individual y recolección
        for f in subir_factura:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(f.read())
                temp_path = tmp.name
            
            try:
                df = procesar_factura(temp_path)
                if df is not None and not df.empty:
                    # Normalizar referencia inmediatamente para consistencia
                    # Normalización de referencia
                    if "Referencia" in df.columns:
                        df["Referencia_Norm"] = df["Referencia"].astype(str).str.strip().str.upper().str.split('/').str[0]
                    else:
                         df["Referencia_Norm"] = "S/R"

                    # Asegurar columnas numéricas
                    for col in ['Cantidad', 'Valor_Total', 'Precio_Unitario']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                        else:
                            df[col] = 0.0

                    df["Archivo_Origen"] = f.name
                    all_invoices.append(df)
                    st.success(f"✅ Procesado: {f.name} ({len(df)} items)")
                else:
                    st.warning(f"⚠️ No se encontraron productos en: {f.name}")
            except Exception as e:
                st.error(f"Error procesando {f.name}: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        # 2. Agregación y Visualización
        if all_invoices:
            df_total_invoices = pd.concat(all_invoices, ignore_index=True)
            
            # MOSTRAR DATA FRAME DE FACTURAS (Detalle con encabezados dinámicos)
            st.write("---")
            st.write("### 🧾 Detalle de Facturas (Items)")
            st.write("A continuación se muestran los items extraídos tal cual se detectaron en las facturas:")
            st.dataframe(df_total_invoices, use_container_width=True)
            
            # Agrupar por Referencia
            # Tomamos la primera descripción y archivo como referencia
            agg_funcs = {
                'Cantidad': 'sum',
                'Valor_Total': 'sum',
                'Precio_Unitario': 'mean', # Promedio inicial, luego recalculamos
                'Description': 'first',
                'Product Number': 'first'
            }
            # Ajustar agg_funcs según columnas existentes
            exist_cols = df_total_invoices.columns
            final_agg = {k: v for k, v in agg_funcs.items() if k in exist_cols}
            
            df_consolidado = df_total_invoices.groupby("Referencia_Norm", as_index=False).agg(final_agg)
            
            # Recalcular Precio Unitario Ponderado si existen datos
            if 'Valor_Total' in df_consolidado.columns and 'Cantidad' in df_consolidado.columns:
                df_consolidado['Precio_Unitario'] = df_consolidado.apply(
                    lambda x: x['Valor_Total'] / x['Cantidad'] if x['Cantidad'] > 0 else 0, axis=1
                )

            st.write("---")
            st.write("### 📋 Facturas Consolidadas")
            st.dataframe(df_consolidado, use_container_width=True)

            # 3. Comparación (Usando el consolidado)
            if 'df' in locals(): del df # Limpiar variables viejas para evitar conflictos
            
            st.write("### ⚖️ Comparación Detallada (Facturas vs Declaraciones)")
            
            # Obtener productos de declaraciones
            all_products_list = []
            for key in st.session_state:
                if key.startswith("data_"):
                    d_prod = st.session_state[key]["prod"]
                    if not d_prod.empty:
                        all_products_list.append(d_prod)
            
            if all_products_list:
                df_decl_total = pd.concat(all_products_list, ignore_index=True)
                
                # Normalizar Declaraciones
                if "Referencia" in df_decl_total.columns:
                    df_decl_total["Referencia_Norm"] = df_decl_total["Referencia"].astype(str).str.strip().str.upper().str.split('/').str[0]
                else:
                    df_decl_total["Referencia_Norm"] = "S/R"
                
                # Agrupar Declaraciones
                df_decl_total["Cantidad"] = pd.to_numeric(df_decl_total["Cantidad"], errors='coerce').fillna(0)
                
                # Intentar buscar columnas de valor en Declaraciones (si existen)
                # NOTA: Por defecto ProductExtractor no extrae precios, así que esto puede ser 0
                has_val_decl = False
                if 'Valor_Total' in df_decl_total.columns:
                    df_decl_total["Valor_Total"] = pd.to_numeric(df_decl_total["Valor_Total"], errors='coerce').fillna(0)
                    has_val_decl = True
                
                agg_decl = {'Cantidad': 'sum'}
                if has_val_decl: agg_decl['Valor_Total'] = 'sum'
                
                df_decl_grouped = df_decl_total.groupby("Referencia_Norm", as_index=False).agg(agg_decl)
                df_decl_grouped.rename(columns={"Cantidad": "Cant_Decl", "Valor_Total": "Valor_Decl"}, inplace=True)
                
                # Merge Comparativo
                df_compare = pd.merge(
                    df_consolidado, 
                    df_decl_grouped, 
                    on="Referencia_Norm", 
                    how="outer"
                ).fillna(0)
                
                # Cálculos de Diferencias
                df_compare["Diff_Cant"] = df_compare["Cantidad"] - df_compare["Cant_Decl"]
                
                # Estado
                def get_status(row):
                    items = []
                    if row["Diff_Cant"] == 0:
                        items.append("✅ Cant OK")
                    elif row["Cant_Decl"] == 0:
                        items.append("⚠️ No en Decl")
                    elif row["Diff_Cant"] > 0:
                        items.append(f"❌ Sobra Fact ({row['Diff_Cant']:.0f})")
                    else:
                        items.append(f"❌ Falta Fact ({abs(row['Diff_Cant']):.0f})")
                    return " | ".join(items)

                df_compare["Estado"] = df_compare.apply(get_status, axis=1)
                
                # Selección de columnas para mostrar
                cols_show = ["Referencia_Norm", "Description", "Cantidad", "Cant_Decl", "Diff_Cant", "Valor_Total", "Precio_Unitario", "Estado"]
                # Filtrar solo las que existen
                cols_final = [c for c in cols_show if c in df_compare.columns]
                
                # Renombrar para display
                rename_display = {
                    "Referencia_Norm": "Referencia",
                    "Cantidad": "Cant. Factura",
                    "Cant_Decl": "Cant. Decl",
                    "Description": "Descripción (Fact)",
                    "Valor_Total": "Valor Total (Fact)",
                    "Precio_Unitario": "Precio Unit. (Calc)"
                }
                
                df_display = df_compare[cols_final].rename(columns=rename_display)
                
                st.dataframe(df_display.style.format({
                    "Cant. Factura": "{:,.0f}",
                    "Cant. Decl": "{:,.0f}",
                    "Diff_Cant": "{:,.0f}",
                    "Valor Total (Fact)": "${:,.2f}",
                    "Precio Unit. (Calc)": "${:,.2f}"
                }), use_container_width=True)
                
            else:
                st.info("ℹ️ Sube archivos de Declaración para ver la comparación.")

        # -----------------------------------------------------------------------------
        # TABLA DE COMPARACIÓN (RESUMEN)
        # -----------------------------------------------------------------------------
        if 'df' in locals() and df is not None and not df.empty:
            st.write("### ⚖️ Comparación con Productos (Declaraciones)")
            
            # 1. Obtener TODOS los productos de las declaraciones cargadas
            all_products_list = []
            for key in st.session_state:
                if key.startswith("data_"):
                    # Extraer DF productos
                    d_prod = st.session_state[key]["prod"]
                    if not d_prod.empty:
                        all_products_list.append(d_prod)
            
            if all_products_list:
                df_all_products = pd.concat(all_products_list, ignore_index=True)
                
                # Normalizar columnas para el merge/comparación
                # Referencia Factura
                if "Referencia" in df.columns:
                    # Limpiar y normalizar (tomar lo que está antes del /)
                    df["Referencia_Norm"] = df["Referencia"].astype(str).str.strip().str.upper().str.split('/').str[0]
                else:
                    st.error("No se encontró columna 'Referencia' en la factura procesada.")
                    df["Referencia_Norm"] = ""

                # Referencia Productos
                if "Referencia" in df_all_products.columns:
                    df_all_products["Referencia_Norm"] = df_all_products["Referencia"].astype(str).str.strip().str.upper().str.split('/').str[0]
                else:
                    st.error("No se encontró columna 'Referencia' en los productos cargados.")
                    df_all_products["Referencia_Norm"] = ""

                # Agrupar productos por Referencia (sumar cantidades)
                # Asumimos que la columna de cantidad en productos es 'Cantidad'
                # Convertir a numérico si es necesario
                def clean_qty(v):
                    try: return float(v)
                    except: return 0.0
                
                df_all_products["Cantidad_Num"] = df_all_products["Cantidad"].apply(clean_qty)
                
                grouped_products = df_all_products.groupby("Referencia_Norm")["Cantidad_Num"].sum().reset_index()
                grouped_products.rename(columns={"Cantidad_Num": "Cant. Declaraciones"}, inplace=True)
                
                # Agrupar Factura por Referencia
                # Asumimos columna 'Qty Ordered' para Gate, 'Cantidad' para otros...
                # Estandarizamos cantidad de factura
                col_qty_factura = "Qty Ordered" if "Qty Ordered" in df.columns else "Cantidad"
                
                if col_qty_factura in df.columns:
                    df["Cantidad_Factura_Num"] = df[col_qty_factura].apply(clean_qty)
                    grouped_invoice = df.groupby("Referencia_Norm")["Cantidad_Factura_Num"].sum().reset_index()
                    grouped_invoice.rename(columns={"Cantidad_Factura_Num": "Cant. Factura"}, inplace=True)
                    
                    # Merge
                    df_compare = pd.merge(grouped_invoice, grouped_products, on="Referencia_Norm", how="outer").fillna(0)
                    
                    # Calcular Diferencia
                    df_compare["Diferencia"] = df_compare["Cant. Factura"] - df_compare["Cant. Declaraciones"]
                    
                    # Estado
                    def get_status(row):
                        if row["Diferencia"] == 0:
                            return "✅ Correcto"
                        elif row["Cant. Declaraciones"] == 0:
                            return "⚠️ No encontrado en Decl."
                        elif row["Diferencia"] > 0:
                            return "❌ Sobra en Factura"
                        else:
                            return "❌ Falta en Factura"

                    df_compare["Estado"] = df_compare.apply(get_status, axis=1)
                    
                    # Formatear para mostrar
                    df_compare_display = df_compare[["Referencia_Norm", "Cant. Factura", "Cant. Declaraciones", "Diferencia", "Estado"]].copy()
                    df_compare_display.columns = ["Referencia", "Cant. Factura", "Cant. Declaraciones", "Diferencia", "Estado"]
                    
                    st.dataframe(df_compare_display, use_container_width=True)
                    
                else:
                    st.warning(f"No se pudo identificar la columna de cantidad en la factura. (Buscado: {col_qty_factura})")
            
            else:
                st.info("Sube primero archivos de declaraciones para ver la tabla comparativa.")
