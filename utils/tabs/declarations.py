import streamlit as st
import pandas as pd
import os
from io import BytesIO
from utils.pdf_orchestrator import procesar_pdf_filelike, guardar_excel_por_pdf
from utils.formatting import convertir_numero, formatear_numero

def render_declarations_tab(subir_declaracion):
    if subir_declaracion:
        # 1. Identificar claves validas actuales
        current_keys = set()
        for f in subir_declaracion:
            current_keys.add(f"data_{f.name}_{f.size}")
        
        # 2. Eliminar lo que sobre en session_state (solo claves de data_)
        for key in list(st.session_state.keys()):
            if key.startswith("data_") and key not in current_keys:
                del st.session_state[key]

        for idx, f in enumerate(subir_declaracion):
            file_key = f"data_{f.name}_{f.size}"
            
            if file_key not in st.session_state:
                with st.spinner(f"Procesando {f.name}..."):
                    d_decl, d_prod, d_text = procesar_pdf_filelike(f)
                    if "Observaciones" not in d_prod.columns:
                        d_prod["Observaciones"] = ""
                    st.session_state[file_key] = {"decl": d_decl, "prod": d_prod, "text": d_text}
            
            data_stored = st.session_state[file_key]
            df_decl = data_stored["decl"]
            df_prod = data_stored["prod"]

            # Aplicar conversión a columnas numéricas
            columnas_numericas = []
            for col in df_decl.columns:
                col_upper = str(col).upper()
                if any(k in col_upper for k in ['VALOR', 'USD', 'FLETES', 'SEGUROS', 'GASTOS', 'AJUSTE', 'PESO', 'TASA', 'ARANCEL', 'IVA', 'LIQUIDADO', 'BASE']):
                    columnas_numericas.append(col)
                    df_decl[col] = df_decl[col].apply(convertir_numero)
            
            if "VALOR FOB USD" in df_decl.columns:
                 fob_series = df_decl['VALOR FOB USD'].fillna(0.0)
                 df_decl['valor_calculado'] = (fob_series * 0.00085).round(2)
                 columnas_numericas.append('valor_calculado')

            df_decl_display = df_decl.copy()
            for col in columnas_numericas:
                if col in df_decl_display.columns:
                    df_decl_display[col] = df_decl_display[col].apply(formatear_numero)

            st.write(f"### 📄 Declaración: {f.name}")
            df_display_final = df_decl_display.copy()
            df_display_final.columns = [str(c).title() for c in df_display_final.columns]
            
            with st.expander("🔧 Seleccionar columnas a mostrar"):
                columnas_decl_seleccionadas = st.multiselect(
                    "Columnas", df_display_final.columns.tolist(),
                    default=df_display_final.columns.tolist(),
                    key=f"ms_decl_{idx}", label_visibility="collapsed"
                )
            
            st.dataframe(df_display_final[columnas_decl_seleccionadas] if columnas_decl_seleccionadas else df_display_final, width="stretch")
            
            if not df_decl.empty:
                buffer_decl = BytesIO()
                with pd.ExcelWriter(buffer_decl, engine='openpyxl') as writer:
                    df_decl.to_excel(writer, sheet_name='Declaraciones', index=False)
                st.download_button(
                    label="Descargar Declaraciones en Excel", data=buffer_decl.getvalue(),
                    file_name=f"{os.path.splitext(f.name)[0]}_declaraciones.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_decl_{idx}"
                )

            st.write("### Productos encontrados")
            df_prod_display = df_prod.copy()
            df_prod_display.columns = [str(c).title() for c in df_prod_display.columns]

            with st.expander("🔧 Seleccionar columnas a mostrar"):
                columnas_prod_seleccionadas = st.multiselect(
                    "Columnas", df_prod_display.columns.tolist(),
                    default=df_prod_display.columns.tolist(),
                    key=f"ms_prod_{idx}", label_visibility="collapsed"
                )

            search_term = st.text_input("🔍 Buscar en productos", key=f"v_search_{idx}").strip()
            df_view = df_prod_display[columnas_prod_seleccionadas] if columnas_prod_seleccionadas else df_prod_display
            
            if search_term:
                mask = df_view.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
                df_view = df_view[mask]
                try:
                    def highlight(val):
                        return 'background-color: #1E3A8A; color: white; font-weight: bold' if search_term.lower() in str(val).lower() else ''
                    df_view = df_view.style.applymap(highlight)
                except: pass

            try:
                event = st.dataframe(df_view, width="stretch", on_select="rerun", selection_mode="single-row", key=f"df_p_sel_{idx}")
                if event.selection.rows:
                    selected_idx = event.selection.rows[0]
                    original_index = df_view.iloc[selected_idx].name 
                    row_original = df_prod.loc[original_index]
                    
                    st.markdown("---")
                    with st.container(border=True):
                        st.write(f"✏️ **Editando observación para:** {row_original.get('Producto', 'P')} - *{row_original.get('Referencia', 'SN')}*")
                        new_obs = st.text_area("Obs", value=str(row_original.get("Observaciones", "")), key=f"obs_in_{file_key}_{original_index}", label_visibility="collapsed")
                        if st.button("💾 Guardar", key=f"sv_{file_key}_{original_index}", type="primary"):
                            st.session_state[file_key]["prod"].at[original_index, "Observaciones"] = new_obs
                            st.rerun()
            except:
                st.dataframe(df_view, width="stretch")

            if not df_prod.empty:
                buffer_prod = BytesIO()
                with pd.ExcelWriter(buffer_prod, engine='openpyxl') as writer:
                    df_prod.to_excel(writer, sheet_name='Productos', index=False)
                st.download_button(
                    label="📥 Descargar Productos en Excel", data=buffer_prod.getvalue(),
                    file_name=f"{os.path.splitext(f.name)[0]}_productos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_prod_{idx}"
                )
            
            guardar_excel_por_pdf(f.name, df_decl, df_prod)
    else:
        st.info("👋 Bienvenido. Para comenzar, sube tus archivos de **Declaración** en la barra lateral.")
