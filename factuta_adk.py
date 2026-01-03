# =============================
# factura_adk.py (UNIVERSAL)
# =============================

import pdfplumber
import pandas as pd
import re

# Marcas conocidas (puedes ampliar)
MARCAS = ["GMB", "NSK", "KOYO", "SKF", "FAG"]

# Inicio de producto: LN + Código
PAT_INICIO = re.compile(
    r"^(?P<ln>\d{1,4})\s+(?P<ref>[A-Z0-9\-\/]+)"
)

# Fin de producto: Marca + Cantidad + Precio
PAT_FIN = re.compile(
    rf"(?P<marca>{'|'.join(MARCAS)})\s+(?P<cantidad>\d+)\s+(?P<precio>\d+,\d+)"
)


def procesar_factura_adk(pdf_path: str) -> pd.DataFrame | None:
    rows = []
    bloque = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.split("\n"):
                line = line.strip()

                # 1️⃣ Detectar inicio de nuevo producto
                if PAT_INICIO.match(line):
                    if bloque:
                        _procesar_bloque(bloque, rows)
                        bloque = []
                    bloque.append(line)
                    # No hacemos continue, permitimos que PAT_FIN verifique si está en la misma línea

                # 2️⃣ Acumular líneas intermedias o verificar fin
                elif bloque:
                    bloque.append(line)

                # 3️⃣ Detectar fin del producto (siempre que haya un bloque abierto)
                if bloque and PAT_FIN.search(line):
                    _procesar_bloque(bloque, rows)
                    bloque = []

        # Cierre final
        if bloque:
            _procesar_bloque(bloque, rows)

    if not rows:
        return None

    return pd.DataFrame(rows)


def _procesar_bloque(bloque: list[str], rows: list[dict]):
    texto = " ".join(bloque)

    ini = PAT_INICIO.search(texto)
    fin = PAT_FIN.search(texto)

    if not ini or not fin:
        return

    ln = int(ini.group("ln"))
    referencia = ini.group("ref")

    marca = fin.group("marca")
    cantidad = int(fin.group("cantidad"))
    precio = float(fin.group("precio").replace(",", "."))

    # Texto intermedio (códigos + descripción)
    cuerpo = texto[ini.end():fin.start()].strip()
    partes = cuerpo.split(" ", 1)
    
    code_2 = ""
    descripcion = cuerpo

    if len(partes) == 2 and re.fullmatch(r"[A-Z0-9\-\/]+", partes[0]):
        code_2 = partes[0]
        descripcion = partes[1]

    rows.append({
        "LN": ln,
        "Referencia": referencia,
        "Code_2": code_2,
        "Description": descripcion.strip(),
        "Brand": marca,
        "Cantidad": cantidad,
        "Precio_Unitario": precio,
        "Valor_Total": round(cantidad * precio, 2),
    })

if __name__ == "__main__":
    import os
    # Ruta específica proporcionada por el usuario + rutas habituales
    ruta_usuario = r"C:\Users\asus\Documents\FACTURA YADAS WT IMPORTACIONES F2510-04037.pdf"
    possible_paths = [ruta_usuario, "facturas_pdf", "PDF_A_LEER", "."]
    test_pdf = None
    
    print("🔍 Buscando un PDF para probar...")
    for p in possible_paths:
        if os.path.exists(p):
            if p.lower().endswith(".pdf"):
                test_pdf = p
                break
            else:
                pdfs = [f for f in os.listdir(p) if f.lower().endswith(".pdf")]
                if pdfs:
                    test_pdf = os.path.join(p, pdfs[0])
                    break
    
    if test_pdf:
        print(f"🚀 Procesando: {test_pdf}")
        df = procesar_factura_adk(test_pdf)
        if df is not None:
            print("\n✅ DATOS EXTRAÍDOS:")
            print("="*100)
            print(df.to_string(index=False))
            print("="*100)
            print(f"Total de líneas extraídas: {len(df)}")
        else:
            print("❌ No se pudo extraer información del PDF.")
    else:
        print("⚠️ No se encontró el PDF en la ruta de Documentos ni en carpetas locales.")
