import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
from utils.comparador import normalizar_df_referencia, get_status_comparativo

def render_comparison_tab(subir_factura, subir_declaracion):
    if subir_factura and subir_declaracion:
        st.write("### ⚖️ Comparativa: Facturas vs Declaraciones")
        df_consolidado = st.session_state.get('df_consolidado')
        
        all_products_list = []
        for key in st.session_state:
            if key.startswith("data_"):
                d_prod = st.session_state[key]["prod"]
                if not d_prod.empty: all_products_list.append(d_prod)
        
        if all_products_list and df_consolidado is not None:
            df_decl_total = pd.concat(all_products_list, ignore_index=True)
            df_decl_total = normalizar_df_referencia(df_decl_total, "Referencia")
            df_decl_total["Cantidad"] = pd.to_numeric(df_decl_total["Cantidad"], errors='coerce').fillna(0)
            df_decl_grouped = df_decl_total.groupby("Referencia_Norm", as_index=False).agg({'Cantidad': 'sum'})
            df_decl_grouped.rename(columns={"Cantidad": "Cant_Decl"}, inplace=True)
            
            df_compare = pd.merge(df_consolidado, df_decl_grouped, on="Referencia_Norm", how="outer").fillna(0)
            df_compare["Diff_Cant"] = df_compare.get("Cantidad", 0) - df_compare["Cant_Decl"]
            df_compare["Estado"] = df_compare.apply(get_status_comparativo, axis=1)
            
            rename_display = {"Referencia_Norm": "Referencia", "Cantidad": "Cant. Factura", "Cant_Decl": "Cant. Decl", "Description": "Descripción (Fact)", "Valor_Total": "Valor Total (Fact)", "Precio_Unitario": "Precio Unit. (Calc)"}
            cols_show = ["Referencia_Norm", "Description", "Cantidad", "Cant_Decl", "Diff_Cant", "Estado"]
            df_display = df_compare[[c for c in cols_show if c in df_compare.columns]].rename(columns=rename_display)
            
            st.dataframe(df_display.style.format({"Cant. Factura": "{:,.0f}", "Cant. Decl": "{:,.0f}", "Diff_Cant": "{:,.0f}"}), width="stretch")

            if not df_compare.empty:
                buf = BytesIO()
                with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                    df_compare.to_excel(writer, sheet_name='Comparativo', index=False)
                st.download_button(label="📥 Descargar Comparativo en Excel", data=buf.getvalue(), file_name="comparativo.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            st.write("### 📊 Gráfico de Comparación")
            try:
                c_data = df_compare[['Referencia_Norm', 'Cantidad', 'Cant_Decl']].copy()
                c_data.columns = ['Referencia', 'Factura', 'Declaración']
                c_data = c_data[(c_data['Factura'] > 0) | (c_data['Declaración'] > 0)]
                
                if not c_data.empty:
                    c_data['Inconsistente'] = c_data['Factura'] != c_data['Declaración']
                    melted = c_data.melt(id_vars=['Referencia', 'Inconsistente'], value_vars=['Factura', 'Declaración'], var_name='Fuente', value_name='Cantidad')
                    chart = alt.Chart(melted).mark_bar().encode(
                        x=alt.X('Referencia:N', title='Ref', axis=alt.Axis(labelAngle=-45)),
                        y=alt.Y('Cantidad:Q'), xOffset='Fuente:N',
                        color=alt.condition(alt.datum.Inconsistente, alt.value('#E11D48'), alt.Color('Fuente:N', scale=alt.Scale(range=['#1E3A8A', '#60A5FA']))),
                        tooltip=['Referencia', 'Fuente', 'Cantidad']
                    ).properties(height=400)
                    st.altair_chart(chart, width="stretch")
            except Exception as e: st.error(f"Error gráfico: {e}")
        elif df_consolidado is None: st.warning("⚠️ Procesa las Facturas primero.")
        else: st.info("ℹ️ Sube archivos de Declaración.")
    else: st.info("👋 Sube ambos tipos de archivos.")
