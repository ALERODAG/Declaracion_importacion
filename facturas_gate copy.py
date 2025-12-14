import re
import os
import glob
import json
import pandas as pd
from typing import List, Dict
import PyPDF2
# import plantilla.json


# ============================
#   LECTURA DE PDF
# ============================

import pdfplumber

def read_pdf_text(pdf_path: str) -> str:
    """
    Lee el contenido completo de un archivo PDF y devuelve su texto.
    Usa pdfplumber para mejor conservación del layout.
    
    Args:
        pdf_path (str): Ruta al archivo PDF
        
    Returns:
        str: Texto extraído del PDF
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text



# ============================
#   EXTRACCIÓN DE CAMPOS DE CABECERA
# ============================

def extract_header_fields(text: str) -> Dict:
    """
    Extrae campos generales del encabezado:
    - Invoice
    - Date
    - Shipment No
    - Purchase Order
    - Customer Number
    
    Args:
        text: texto completo del PDF
        
    Returns:
        dict con campos extraídos
    """

    # Patrones ajustados para el layout de pdfplumber donde los valores están debajo de las etiquetas en inglés
    # Se usa re.DOTALL implícitamente al buscar con \n o se puede buscar en el texto completo
    patterns = {
        "Invoice": r"INVOICE NO\..*?\n.*?(\b[0-9]+I\b)",
        "Date": r"INVOICE DATE.*?\n.*?(\b[0-9]{2}-[A-Z]{3}-[0-9]{4}\b)",
        "Shipment No": r"SHIPMENT NO:.*?\n.*?(\b[0-9]{7}\b)",
        "Purchase Order": r"PURCHASE ORD NO:.*?\n.*?(\b[0-9]{2}-[0-9]{4}\s+[A-Za-z0-9]+)",
        "Customer Number": r"CUSTOMER NO:.*?\n.*?(\b[0-9]{6}\b)"
     

    }
    # #usamos la plantilla de plantilla.json para extraer los campos
    # plantilla = json.load(open("plantilla.json"))
    
    # #extraemos los campos del encabezado
    # for key, pattern in plantilla.items():
    #     match = re.search(pattern, text, re.MULTILINE)
    #     extracted[key] = match.group(1).strip() if match else None
    
    # return extracted

    

    
    


    extracted = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.MULTILINE)
        extracted[key] = match.group(1).strip() if match else None

    return extracted



# ============================
#   EXTRACCIÓN DE LÍNEAS DE PRODUCTOS
# ============================

def extract_product_lines(text: str) -> List[Dict]:
    """
    Extrae las líneas de productos del PDF.
    El formato sigue patrones como:
        QTY  U/M  DESCRIPTION  PRODUCT NUMBER  BACKORDER  SHIPPED  UNIT PRICE  TOTAL PRICE

    Usa expresiones regulares para detectar cada fila de producto.

    Args:
        text (str): texto del PDF
    
    Returns:
        List[Dict]: lista de líneas extraídas
    """

    line_pattern = re.compile(
        r"(\d+)\s+EA\s+([A-Z0-9\- ]+)\s+([0-9]{5,12})\s+\d+\s+([\d\.]+)\s+([\d\.]+)",
        re.MULTILINE
    )

    items = []

    for match in line_pattern.finditer(text):
        qty = int(match.group(1))
        desc = match.group(2).strip()
        product_number = match.group(3)
        unit_price = float(match.group(4))
        total_price = float(match.group(5))

        items.append({
            "Qty Ordered": qty,
            "Qty Shipped": qty, # Asumiendo que es lo mismo por ahora, ajustar si hay campo separado
            "Description": desc,
            "Product Number": product_number,
            "Unit Price": unit_price,
            "Total Price": total_price
            

        })

    return items



# ============================
#   PROCESAR UN PDF COMPLETO
# ============================

def process_pdf(pdf_path: str) -> Dict:
    """
    Procesa un PDF extrayendo:
    - Encabezado (invoice, date, etc.)
    - Líneas de productos

    Args:
        pdf_path: ruta al PDF
    
    Returns:
        Dict estructurado
    """
    text = read_pdf_text(pdf_path)
    header = extract_header_fields(text)
    products = extract_product_lines(text)

    return {
        "pdf_path": pdf_path,
        "header": header,
        "products": products
    }



# ============================
#   PROCESAR MÚLTIPLES PDF
# ============================

def process_multiple_pdfs(pdf_paths: List[str]) -> List[Dict]:
    """
    Procesa una lista de PDFs y devuelve una lista con la información estructurada.

    Args:
        pdf_paths: lista de rutas
        
    Returns:
        List[Dict]
    """
    results = []
    for path in pdf_paths:
        try:
            # Procesar cada PDF
            print(f"Analizando: {os.path.basename(path)}")
            pdf_data = process_pdf(path)
            header = pdf_data["header"]
            products = pdf_data["products"]
            
            if not products:
                print(f"  WARNING: No se encontraron productos en {os.path.basename(path)}")
                # Imprimir un fragmento del texto para depurar
                text_snippet = read_pdf_text(path)
                # Buscar la sección donde suelen estar los productos
                print("  --- TEXTO DE MUESTRA (Primeros 1000 chars) ---")
                print(text_snippet[:1000])
                print("  ----------------------------------------------")

            # Aplanar la estructura: Header + Product Line
            for prod in products:
                # Unir diccionarios
                flat_item = {**header, **prod}
                results.append(flat_item)
                
        except Exception as e:
            print(f"Error procesando {path}: {e}")
            
    return results



# ============================
#   FUNCIÓN MAIN PARA STREAMLIT
# ============================

def main(pdf_paths: List[str]) -> List[Dict]:
    """
    Función principal para procesar facturas desde Streamlit.
    Toma una lista de rutas de PDF y devuelve la información estructurada.

    Args:
        pdf_paths: Lista de rutas a archivos PDF

    Returns:
        Lista de diccionarios con la información extraída
    """
    return process_multiple_pdfs(pdf_paths)


# ============================
#   EJEMPLO DE USO
# ============================

if __name__ == "__main__":
    # Detectar la carpeta de descargas del usuario actual
    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
    
    # Buscar archivos PDF que empiecen con 'gates' en la carpeta de descargas
    # Se puede cambiar "*.pdf" para buscar todos si se desea, pero el usuario busca facturas especificas
    pdf_files = glob.glob(os.path.join(downloads_folder, "gates*.pdf"))
    
    if not pdf_files:
        print(f"No se encontraron archivos PDF que comiencen con 'gates' en: {downloads_folder}")
        print("Archivos encontrados en la carpeta:")
        all_pdfs = glob.glob(os.path.join(downloads_folder, "*.pdf"))
        for p in all_pdfs:
            print(f" - {os.path.basename(p)}")
    else:
        print(f"Procesando {len(pdf_files)} archivos PDF encontrados en {downloads_folder}...")
        data = process_multiple_pdfs(pdf_files)
        
        # Convertir a DataFrame
        df = pd.DataFrame(data)
        
        # Guardar en Excel en la misma ruta
        output_file = os.path.join(downloads_folder, "resumen_facturas_gates.xlsx")
        try:
            df.to_excel(output_file, index=False)
            print(f"✅ Archivo Excel generado exitosamente: {output_file}")
            print("\nVista previa de los datos:")
            print(df.head())
        except Exception as e:
            print(f"❌ Error al guardar el archivo Excel: {e}")
            print(df)
