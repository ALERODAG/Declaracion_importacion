# =============================
#   factuta_adk.py (MODULAR)
# =============================

import pdfplumber
import pandas as pd
import re

MARCAS = ["GMB", "NSK", "KOYO", "SKF", "FAG"]

pat_inicio = re.compile(r"^(?P<item>\d{1,3})\s+(?P<codigo>[A-Za-z0-9\-\/]+)")
pat_fin = re.compile(
    r"(?P<marca>{})\s+(?P<cantidad>\d+)\s+(?P<precio>\d+,\d+)".format("|".join(MARCAS))
)


def detect_product_end(line):
    return bool(pat_fin.search(line))


def process_block(block, pdf_path, rows):
    full = " ".join(block)

    ini = pat_inicio.search(full)
    fin = pat_fin.search(full)

    if not ini or not fin:
        return

    item = ini.group("item")
    codigo = ini.group("codigo")

    marca = fin.group("marca")
    cantidad = int(fin.group("cantidad"))
    precio = float(fin.group("precio").replace(",", "."))

    mid = full[ini.end():fin.start()].strip()

    partes = mid.split(" ", 1)
    codigo2 = partes[0] if len(partes) > 1 and re.match(r"^[A-Za-z0-9\-\/]+$", partes[0]) else ""
    descripcion = partes[1] if len(partes) > 1 else mid

    rows.append({
        "Line_Number": item,
        "Referencia": codigo,
        "Code_2": codigo2,
        "Description": descripcion.strip(),
        "Brand": marca,
        "Cantidad": cantidad,
        "Precio_Unitario": precio,
        "Valor_Total": round(cantidad * precio, 2)
    })


def procesar_factura_adk(pdf_path: str):
    rows = []

    with pdfplumber.open(pdf_path) as pdf:
        block = []

        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.split("\n"):
                line = line.strip()

                if pat_inicio.match(line):
                    if block:
                        process_block(block, pdf_path, rows)
                        block = []
                    block.append(line)

                else:
                    if block:
                        block.append(line)

                    if block and detect_product_end(line):
                        process_block(block, pdf_path, rows)
                        block = []

        if block:
            process_block(block, pdf_path, rows)

    if not rows:
        return None

    return pd.DataFrame(rows)
