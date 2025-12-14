# ============================
#   facturas_gate.py (MODULAR)
# ============================

import re
import pdfplumber
import pandas as pd

# -----------------------------
#   LECTURA PDF
# -----------------------------
def read_pdf_text(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text


# -----------------------------
#   EXTRACCIÓN HEADER
# -----------------------------
def extract_header_fields(text: str):
    patterns = {
        "Invoice": r"INVOICE NO\..*?\n.*?(\b[0-9]+I\b)",
        "Date": r"INVOICE DATE.*?\n.*?(\b[0-9]{2}-[A-Z]{3}-[0-9]{4}\b)",
        "Shipment No": r"SHIPMENT NO:.*?\n.*?(\b[0-9]{7}\b)",
        "Purchase Order": r"PURCHASE ORD NO:.*?\n.*?(\b[0-9]{2}-[0-9]{4}\s+[A-Za-z0-9]+)",
        "Customer Number": r"CUSTOMER NO:.*?\n.*?(\b[0-9]{6}\b)"
    }

    extracted = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.MULTILINE)
        extracted[key] = match.group(1).strip() if match else None

    return extracted


# -----------------------------
#   EXTRACCIÓN PRODUCTOS
# -----------------------------
def extract_product_lines(text: str):
    line_pattern = re.compile(
        r"(\d+)\s+EA\s+([A-Z0-9\- ]+)\s+([0-9]{5,12})\s+\d+\s+([\d\.]+)\s+([\d\.]+)",
        re.MULTILINE
    )

    items = []

    for match in line_pattern.finditer(text):
        items.append({
            "Qty Ordered": int(match.group(1)),
            "Description": match.group(2).strip(),
            "Product Number": match.group(3),
            "Unit Price": float(match.group(4)),
            "Total Price": float(match.group(5)),
        })

    return items


# -----------------------------
#   FUNCIÓN PRINCIPAL (MODULAR)
# -----------------------------
def procesar_factura_gate(pdf_path: str):
    text = read_pdf_text(pdf_path)
    header = extract_header_fields(text)
    products = extract_product_lines(text)

    if not products:
        return None  # Indica: "este parser no aplica"

    df = pd.DataFrame([{**header, **prod} for prod in products])
    return df
