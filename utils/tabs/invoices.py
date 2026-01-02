import streamlit as st
import pandas as pd
import tempfile
import os
from procesador_universal import procesar_factura
from utils.comparador import normalizar_df_referencia

def render_invoices_tab(subir_factura):
    df_consolidado = None
    if subir_factura:
        all_invoices = []
        for f in subir_factura:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(f.read())
                temp_path = tmp.name
            try:
                df = procesar_factura(temp_path)
                if df is not None and not df.empty:
                    df = normalizar_df_referencia(df, "Referencia")
                    for col in ['Cantidad', 'Valor_Total', 'Precio_Unitario']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    df["Archivo_Origen"] = f.name
                    all_invoices.append(df)
                    st.success(f"✅ Procesado: {f.name}")
            except Exception as e:
                st.error(f"Error procesando {f.name}: {e}")
            finally:
                if os.path.exists(temp_path): os.unlink(temp_path)

        if all_invoices:
            df_total_invoices = pd.concat(all_invoices, ignore_index=True)
            st.write("### 🧾 Detalle de Facturas (Items)")
            st.dataframe(df_total_invoices, width="stretch")
            
            df_total_invoices['Description'] = df_total_invoices['Description'].astype(str) if 'Description' in df_total_invoices.columns else "S/D"
            agg_funcs = {'Cantidad': 'sum', 'Valor_Total': 'sum', 'Precio_Unitario': 'mean', 'Description': 'first', 'Archivo_Origen': lambda x: ", ".join(sorted(set(x)))}
            df_consolidado = df_total_invoices.groupby("Referencia_Norm", as_index=False).agg({k: v for k, v in agg_funcs.items() if k in df_total_invoices.columns})
            
            if 'Valor_Total' in df_consolidado.columns and 'Cantidad' in df_consolidado.columns:
                df_consolidado['Precio_Unitario'] = df_consolidado.apply(lambda x: x['Valor_Total'] / x['Cantidad'] if x['Cantidad'] > 0 else 0, axis=1)

            st.write("### 📋 Resumen Consolidado")
            format_dict = {'Cantidad': "{:,.2f}", 'Valor_Total': "${:,.2f}", 'Precio_Unitario': "${:,.2f}"}
            st.dataframe(df_consolidado.style.format({k: v for k, v in format_dict.items() if k in df_consolidado.columns}), width="stretch")
            st.session_state['df_consolidado'] = df_consolidado
    else:
        st.info("👋 Sube tus **Facturas** en la barra lateral para procesarlas.")
    return df_consolidado
