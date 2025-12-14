#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#SCRIPT MAIN_SIMPLE
import os
import re
import pandas as pd
from productos import ProductExtractor  # Asegúrate de que productos.py esté accesible

# =========================
# Utilidades de extracción
# =========================

def extraer_texto_pdf(ruta_pdf: str) -> str:
    import fitz  # PyMuPDF
    texto = ""
    try:
        with fitz.open(ruta_pdf) as doc:
            for page in doc:
                texto += page.get_text("text")
    except Exception as e:
        print(f"Error al leer {ruta_pdf}: {e}")
    return texto

def separar_declaraciones(texto: str, fin_delim="^DO  LAC$") -> list:
    """
    Separa bloques de 'DECLARACION <num> DE <año>' hasta que encuentre fin_delim
    o hasta la siguiente DECLARACION.
    """
    pattern = re.compile(r"DECLARACION\s+(\d+)\s+DE\s+(\d+)", re.IGNORECASE)
    matches = list(pattern.finditer(texto))
    declaraciones = []
    for i, match in enumerate(matches):
        numero = int(match.group(1))
        start = match.start()
        fin_match = re.search(re.escape(fin_delim), texto[start:], re.IGNORECASE)
        if fin_match:
            end = start + fin_match.end()
        elif i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(texto)
        contenido = texto[start:end].strip()
        declaraciones.append({"numero": numero, "contenido": contenido})
    return sorted(declaraciones, key=lambda x: x["numero"])

def limpiar_lineas(texto: str):
    lines = texto.splitlines()
    lines = [line.strip() for line in lines if line.strip()]
    lines = [line.replace(",", ".") for line in lines]
    return lines

# =========================
# Búsqueda robusta template
# =========================

def localizar_template(base_path: str, pdf_directory: str, nombre_template: str) -> str:
    """
    Busca el template en:
      1) PDF_A_LEER/
      2) junto al script
      3) ./plantillas/
    Devuelve la ruta encontrada o lanza FileNotFoundError.
    """
    candidatos = [
        os.path.join(pdf_directory, nombre_template),
        os.path.join(base_path, nombre_template),
        os.path.join(base_path, "plantillas", nombre_template),
    ]

    print("Buscando template en:")
    for c in candidatos:
        print("  -", c)

    for c in candidatos:
        if os.path.exists(c):
            return c

    raise FileNotFoundError(
        "No se encuentra el template en ninguna de las rutas probadas.\n"
        f"Nombre esperado: '{nombre_template}'\n"
        + "\n".join(f" - {c}" for c in candidatos)
    )

# =========================
# Programa principal
# =========================

if __name__ == "__main__":
    # --- rutas base dinámicas (relativas al archivo .py)
    base_path = os.path.dirname(os.path.abspath(__file__))

    # Carpeta donde están los PDFs (crea si no existe)
    pdf_directory = os.path.join(base_path, "PDF_A_LEER")
    os.makedirs(pdf_directory, exist_ok=True)

    # Carpeta de salida
    output_dir = os.path.join(pdf_directory, "EXCEL_PDF_LEIDOS")
    os.makedirs(output_dir, exist_ok=True)

    # --- localizar template
    TEMPLATE_NAME = "FORMATO DECLARACION IMPORTACION.xlsx"
    template_path = localizar_template(base_path, pdf_directory, TEMPLATE_NAME)
    print(f"Usando template: {template_path}")

    # --- leer encabezados del template
    try:
        template_df = pd.read_excel(template_path, header=0)
    except ImportError as e:
        raise RuntimeError(
            "Para leer archivos .xlsx necesitas 'openpyxl'.\n"
            "Instala con: pip install openpyxl"
        ) from e

    headers = template_df.columns.tolist()
    if not headers:
        raise RuntimeError("El template no tiene encabezados en la primera fila.")

    # --- listar PDFs
    pdf_files = [
        os.path.join(pdf_directory, f)
        for f in os.listdir(pdf_directory)
        if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        print(f"No se encontraron archivos PDF en: {pdf_directory}")
        raise SystemExit(0)

    extractor = ProductExtractor()

    # --- procesar cada PDF → 1 Excel por PDF
    for ruta_pdf in pdf_files:
        base = os.path.basename(ruta_pdf)
        nombre_sin_ext, _ = os.path.splitext(base)
        print(f"\nProcesando: {base}")

        texto_extraido = extraer_texto_pdf(ruta_pdf)

        # ---- Declaraciones (solo de ESTE PDF)
        declaraciones = separar_declaraciones(texto_extraido)
        all_rows = []
        for decl in declaraciones:
            print(f"   -> Extrayendo DECLARACION {decl['numero']}...")
            lines = limpiar_lineas(decl["contenido"])
            data = [None] * len(headers)
            for i in range(min(len(lines), len(headers))):
                data[i] = lines[i]
            all_rows.append(data)

        df_decl = None
        if all_rows:
            df_decl = pd.DataFrame(all_rows, columns=headers).dropna(axis=1, how="all")
            # Renombres según tu lógica original
            df_decl.rename(columns={"Columna79": "VALOR FOB USD"}, inplace=True)
            df_decl.rename(columns={"Columna80": "VALOR FLETES USD"}, inplace=True)
            df_decl.rename(columns={"Columna68": "COD_PAIS_COMPRA"}, inplace=True)
            df_decl.rename(columns={"Columna69": "PESO_BRUTO"}, inplace=True)
            df_decl.rename(columns={"Columna70": "DMS_PESO_BRUTO_KG"}, inplace=True)
            df_decl.rename(columns={"Columna71": "PESO_NETO_KG"}, inplace=True)
            df_decl.rename(columns={"Columna72": "DMS_PESO_NETO_KG"}, inplace=True)
            df_decl.rename(columns={"Columna73": "CODIGO_EMBALAJE"}, inplace=True)
            df_decl.rename(columns={"Columna74": "NUMERO_BULTOS"}, inplace=True)
            df_decl.rename(columns={"Columna75": "SUBPARTIDAS"}, inplace=True)
            df_decl.rename(columns={"Columna76": "COD_UNIDAD_CAL"}, inplace=True)
            df_decl.rename(columns={"Columna77": "CANTIDAD"}, inplace=True)
            df_decl.rename(columns={"Columna78": "DMS_CANTIDAD"}, inplace=True)
            df_decl.rename(columns={"Columna81": "VALOR_SEGUROS_USD"}, inplace=True)
            df_decl.rename(columns={"Columna82": "VALOR_OTROS_GASTOS"}, inplace=True)
            df_decl.rename(columns={"Columna83": "SUMATORIA_FLETES_SEGUROS_OTROS_USD"}, inplace=True)
            df_decl.rename(columns={"Columna84": "AJUSTE_VALOR_USD"}, inplace=True)
            df_decl.rename(columns={"Columna85": "VALOR_ADUANA_USD"}, inplace=True)
            df_decl.rename(columns={"Columna88": "COD_OFICINA"}, inplace=True)

        # ---- Productos (solo de ESTE PDF)
        df_products = pd.DataFrame()
        try:
            df_prod_tmp = extractor.extract_products_from_text(texto_extraido, base)
            if df_prod_tmp is not None and not df_prod_tmp.empty:
                # Quitar columnas prohibidas si aparecen
                columnas_prohibidas = [
                    "Moneda", "Valor_FOB", "Incoterm",
                    "Peso_Neto", "Peso_Bruto", "API", "ACEA"
                ]
                for col in columnas_prohibidas:
                    if col in df_prod_tmp.columns:
                        df_prod_tmp.drop(columns=[col], inplace=True)

                # Podar columnas totalmente vacías
                vacias = [
                    c for c in df_prod_tmp.columns
                    if df_prod_tmp[c].astype(str).str.strip().eq("").all() or df_prod_tmp[c].isna().all()
                ]
                if vacias:
                    df_prod_tmp.drop(columns=vacias, inplace=True)

                df_products = df_prod_tmp
                print(f"   -> Productos extraídos: {len(df_products)}")
            else:
                print("   -> No se encontraron productos en este PDF.")
        except Exception as e:
            print(f"   -> Error al extraer productos: {e}")

        # ---- Guardado: UN EXCEL POR PDF con el MISMO NOMBRE
        excel_name = f"{nombre_sin_ext}.xlsx"
        excel_path = os.path.join(output_dir, excel_name)

        if (df_decl is None or df_decl.empty) and (df_products is None or df_products.empty):
            print(f"   -> No hay datos para guardar en {excel_name}.")
            continue

        try:
            with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
                if df_decl is not None and not df_decl.empty:
                    df_decl.to_excel(writer, sheet_name="Declaraciones", index=False)
                if df_products is not None and not df_products.empty:
                    df_products.to_excel(writer, sheet_name="Productos", index=False)
        except ImportError as e:
            raise RuntimeError(
                "Para escribir .xlsx necesitas 'openpyxl'.\n"
                "Instala con: pip install openpyxl"
            ) from e

        print(f"   -> Archivo Excel generado: {excel_path}")
        print(f"      Declaraciones: {0 if df_decl is None else len(df_decl)} | Productos: {0 if df_products is None else len(df_products)}")

    print("\nProceso completado (un Excel por PDF).")
