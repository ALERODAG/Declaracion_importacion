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
    print(texto) 
    


   

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
        
        # Formatear columnas numéricas para visualización (1,234.56)
        for col in columnas_numericas:
            if col in df_decl_display.columns:
                df_decl_display[col] = df_decl_display[col].apply(formatear_numero)

        # with col1:
        st.write("### 📄 Declaración formateada")
        
        # Selector de columnas en expander
        with st.expander("🔧 Seleccionar columnas a mostrar"):
            columnas_decl_seleccionadas = st.multiselect(
                "Columnas", 
                df_decl_display.columns.tolist(),
                default=df_decl_display.columns.tolist(),
                key=f"multiselect_declaraciones_{idx}",
                label_visibility="collapsed"
            )
        
        # Mostrar solo columnas seleccionadas
        if columnas_decl_seleccionadas:
            st.dataframe(df_decl_display[columnas_decl_seleccionadas])
        else:
            st.dataframe(df_decl_display)
        
        # Botón de descarga para declaraciones
        if not df_decl.empty:
            from io import BytesIO
            buffer_decl = BytesIO()
            with pd.ExcelWriter(buffer_decl, engine='openpyxl') as writer:
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
        
        # Selector de columnas en expander
        with st.expander("🔧 Seleccionar columnas a mostrar"):
            columnas_prod_seleccionadas = st.multiselect(
                "Columnas", 
                df_prod.columns.tolist(),
                default=df_prod.columns.tolist(),
                key=f"multiselect_productos_{idx}",
                label_visibility="collapsed"
            )
        
        # Mostrar solo columnas seleccionadas
        if columnas_prod_seleccionadas:
            st.dataframe(df_prod[columnas_prod_seleccionadas])
        else:
            st.dataframe(df_prod)
        
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
                
                # Selector de columnas para mostrar
                columnas_seleccionadas = st.multiselect(
                    "Selecciona las columnas a mostrar", 
                    df.columns.tolist(),
                    default=df.columns.tolist(),
                    key=f"cols_{f.name}"
                )
                
                if columnas_seleccionadas:
                    st.dataframe(df[columnas_seleccionadas])
                else:
                    st.dataframe(df)
                
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