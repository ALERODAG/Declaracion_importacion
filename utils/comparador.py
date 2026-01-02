import pandas as pd

def normalizar_referencia(valor):
    """Normaliza una referencia (strip, upper, split por /)."""
    return str(valor).strip().str.upper().str.split('/').str[0]

def normalizar_df_referencia(df, col_name="Referencia"):
    """Crea una columna Referencia_Norm en el DataFrame."""
    if col_name in df.columns:
        df["Referencia_Norm"] = df[col_name].astype(str).str.strip().str.upper().str.split('/').str[0]
    else:
        df["Referencia_Norm"] = "S/R"
    return df

def get_status_comparativo(row):
    """Calcula el estado basado en la diferencia de cantidad."""
    diff = row["Diff_Cant"]
    cant_decl = row["Cant_Decl"]
    if diff == 0: return "✅ OK"
    if cant_decl == 0: return "⚠️ No en Decl"
    if diff > 0: return f"❌ Sobra Fact ({diff:.0f})"
    return f"❌ Falta Fact ({abs(diff):.0f})"
