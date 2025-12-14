# =================================
#   factura_universal.py
#   Parser universal inteligente para cualquier formato de factura
# =================================

import pdfplumber
import pandas as pd
import re
from typing import Dict, List, Optional

# -----------------------------
#   MAPEO DE COLUMNAS
# -----------------------------
COLUMN_MAPPINGS = {
    # Spanish
    "l/n": "Line_Number",
    "línea": "Line_Number",
    "ln": "Line_Number",
    "codigo": "Code",
    "código": "Code",
    "code": "Code",
    "codigo 2": "Code_2",
    "código 2": "Code_2",
    "codigo2": "Code_2",
    "descripcion": "Description",
    "descripción": "Description",
    "marca": "Brand",
    "cantidad": "Quantity",
    "precio": "Price",
    
    # French
    "lg": "Line_Number",
    "ligne": "Line_Number",
    "code article": "Code",
    "article": "Code_2",
    "libellé": "Description",
    "libelle": "Description",
    "qté": "Quantity",
    "qte": "Quantity",
    "quantité": "Quantity",
    "unité": "Unit",
    "unite": "Unit",
    "prix unit": "Unit_Price",
    "prix unit.": "Unit_Price",
    "prix unitaire": "Unit_Price",
    "c/m": "CM",
    "montant ht": "Amount_HT",
    "montant": "Amount",
    
    # English
    "item": "Line_Number",
    "parts no": "Code",
    "parts no.": "Code",
    "part no": "Code",
    "part no.": "Code",
    "supply code": "Code_2",
    "description": "Description",
    "qty": "Quantity",
    "quantity": "Quantity",
    "price": "Unit_Price",
    "unit price": "Unit_Price",
    "total": "Total",
    "brand": "Brand",
    "order no": "Order_Number"
}

# Palabras clave que indican que NO es una fila de producto
PALABRAS_INVALIDAS = [
    "total", "subtotal", "sub-total", "grand total",
    "tva", "iva", "tax", "vat",
    "page", "página", "pagina",
    "facture", "factura", "invoice",
    "conditions", "condiciones", "terms",
    "transporteur", "transporte", "shipping"
]


# -----------------------------
#   NORMALIZAR NOMBRE DE COLUMNA
# -----------------------------
def normalizar_columna(nombre: str) -> str:
    """
    Normaliza el nombre de una columna para mapeo.
    
    Args:
        nombre: Nombre de columna del PDF
        
    Returns:
        Nombre normalizado en minúsculas sin espacios extra
    """
    if not nombre or not isinstance(nombre, str):
        return ""
    
    # Convertir a minúsculas y limpiar
    nombre = nombre.lower().strip()
    # Eliminar puntos y espacios múltiples
    nombre = re.sub(r'\s+', ' ', nombre)
    nombre = nombre.replace('.', '')
    
    return nombre


# -----------------------------
#   DETECTAR COLUMNAS
# -----------------------------
def detectar_columnas(headers: List[str]) -> Dict[int, str]:
    """
    Detecta y mapea columnas de tabla a nombres estándar.
    
    Args:
        headers: Lista de nombres de columnas del PDF
        
    Returns:
        Dict mapeando índice de columna a nombre estándar
    """
    mapeo = {}
    
    for idx, header in enumerate(headers):
        if not header:
            continue
            
        header_norm = normalizar_columna(header)
        
        # Buscar en el diccionario de mapeos
        if header_norm in COLUMN_MAPPINGS:
            mapeo[idx] = COLUMN_MAPPINGS[header_norm]
        else:
            # Si no se encuentra mapeo exacto, usar el nombre original limpio
            mapeo[idx] = header.strip()
    
    return mapeo


# -----------------------------
#   VALIDAR FILA DE PRODUCTO
# -----------------------------
def es_fila_producto(fila: List) -> bool:
    """
    Determina si una fila representa un producto válido.
    
    Args:
        fila: Lista de valores de la fila
        
    Returns:
        True si es una fila de producto, False si es encabezado/total/etc
    """
    if not fila or len(fila) == 0:
        return False
    
    # Convertir fila a texto para análisis
    texto_fila = " ".join(str(cell).lower() if cell else "" for cell in fila)
    
    # Rechazar si contiene palabras inválidas
    for palabra in PALABRAS_INVALIDAS:
        if palabra in texto_fila:
            return False
    
    # Debe tener al menos un número (cantidad o precio)
    tiene_numero = any(
        str(cell).replace(",", "").replace(".", "").replace(" ", "").isdigit()
        for cell in fila if cell
    )
    
    return tiene_numero


# -----------------------------
#   CONVERTIR VALOR NUMÉRICO
# -----------------------------
def convertir_numero(valor) -> Optional[float]:
    """
    Convierte un valor a número, manejando diferentes formatos.
    
    Args:
        valor: Valor a convertir
        
    Returns:
        Número float o None si no se puede convertir
    """
    if valor is None or valor == "":
        return None
    
    try:
        # Si ya es número, retornar
        if isinstance(valor, (int, float)):
            return float(valor)
        
        # Convertir a string y limpiar
        str_valor = str(valor).strip().replace(" ", "")
        
        if not str_valor or str_valor.lower() == "none":
            return None
        
        # Manejar formatos europeos y americanos
        # Formato europeo: 1.234,56 -> 1234.56
        # Formato americano: 1,234.56 -> 1234.56
        
        if ',' in str_valor and '.' in str_valor:
            # Determinar cuál es el separador decimal
            pos_punto = str_valor.rfind('.')
            pos_coma = str_valor.rfind(',')
            
            if pos_punto > pos_coma:
                # Formato americano: coma=miles, punto=decimal
                str_valor = str_valor.replace(',', '')
            else:
                # Formato europeo: punto=miles, coma=decimal
                str_valor = str_valor.replace('.', '').replace(',', '.')
        elif ',' in str_valor:
            # Solo coma - asumir decimal europeo
            str_valor = str_valor.replace(',', '.')
        
        return float(str_valor)
    
    except (ValueError, TypeError):
        return None


# -----------------------------
#   EXTRAER TABLA INTELIGENTE
# -----------------------------
def extraer_tabla_inteligente(pdf_path: str) -> Optional[pd.DataFrame]:
    """
    Extrae tablas de productos usando detección inteligente de columnas.
    
    Args:
        pdf_path: Ruta al archivo PDF
        
    Returns:
        DataFrame con productos o None si no se encontraron
    """
    todas_filas = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extraer todas las tablas de la página
            tablas = page.extract_tables()
            
            if not tablas:
                continue
            
            for tabla in tablas:
                if not tabla or len(tabla) < 1:
                    continue
                
                # Primera fila como encabezados
                headers = tabla[0]
                
                # Detectar mapeo de columnas
                mapeo_columnas = detectar_columnas(headers)
                
                if not mapeo_columnas:
                    continue
                
                # Verificar si es una tabla de productos (debe tener columnas clave)
                nombres_std = set(mapeo_columnas.values())
                tiene_columnas_producto = any(
                    col in nombres_std 
                    for col in ["Code", "Description", "Quantity", "Price", "Unit_Price"]
                )
                
                if not tiene_columnas_producto:
                    continue
                
                # Procesar filas de datos
                for fila in tabla[1:]:
                    # CASO 1: Fila normal con celdas separadas
                    if len([c for c in fila if c]) > 1:
                        if not es_fila_producto(fila):
                            continue
                        
                        # Crear diccionario de producto
                        producto = {}
                        
                        for idx, nombre_columna in mapeo_columnas.items():
                            if idx < len(fila):
                                valor = fila[idx]
                                
                                # Intentar convertir a número si el nombre sugiere valor numérico
                                if nombre_columna in ["Quantity", "Unit_Price", "Price", "Total", "Amount_HT", "Amount"]:
                                    valor = convertir_numero(valor)
                                
                                producto[nombre_columna] = valor
                        
                        if producto:
                            todas_filas.append(producto)
                    
                    # CASO 2: Todas las filas están en una sola celda (texto fusionado)
                    elif len(fila) > 0 and fila[0] and '\n' in str(fila[0]):
                        texto_fusionado = str(fila[0])
                        lineas = texto_fusionado.split('\n')
                        
                        # Intentar parsear cada línea como un producto
                        for linea in lineas:
                            linea = linea.strip()
                            if not linea:
                                continue
                            
                            # Limpiar caracteres especiales de PDF (cid:160 = espacio no rompible)
                            linea = re.sub(r'\(cid:\d+\)', ' ', linea)
                            linea = re.sub(r'\s+', ' ', linea)  # Normalizar espacios
                            
                            # Patron para líneas de productos franceses
                            # Formato: 001 N300501 /N3005 POMPE N3005-BOITE SOFABEX EMBALLE 360,00 O 9,54 3 434,40
                            patron_fr = re.compile(
                                r'^(\d{3})\s+'  # Lg (001, 002, etc.)
                                r'([A-Z0-9]+)\s+'  # Code (N300501)
                                r'/([A-Z0-9]+)\s+'  # Article (/N3005)
                                r'(.+?)\s+'  # Libellé (descripción)
                                r'([\d\s,\.]+?)\s+'  # Qté (cantidad con posibles espacios)
                                r'([A-Z])\s+'  # Unité (O, EA, etc.)
                                r'([\d,\.]+)\s+'  # Prix Unit
                                r'([\d\s,\.]+)$'  # Montant HT
                            )
                            
                            match = patron_fr.match(linea)
                            if match:
                                try:
                                    producto = {
                                        "Line_Number": match.group(1),
                                        "Code": match.group(2),
                                        "Code_2": match.group(3),
                                        "Description": match.group(4).strip(),
                                        "Quantity": convertir_numero(match.group(5)),
                                        "Unit": match.group(6),
                                        "Unit_Price": convertir_numero(match.group(7)),
                                        "Amount_HT": convertir_numero(match.group(8))
                                    }
                                    
                                    # Calcular Total si no existe
                                    if "Total" not in producto and producto.get("Quantity") and producto.get("Unit_Price"):
                                        producto["Total"] = producto["Quantity"] * producto["Unit_Price"]
                                    
                                    todas_filas.append(producto)
                                except Exception as e:
                                    print(f"Error parseando linea: {linea} - {e}")
                                    continue
    
    if not todas_filas:
        return None
    
    df = pd.DataFrame(todas_filas)
    
    # Calcular Total si no existe pero tenemos Quantity y Unit_Price
    if "Total" not in df.columns:
        if "Quantity" in df.columns and "Unit_Price" in df.columns:
            df["Total"] = df["Quantity"] * df["Unit_Price"]
        elif "Quantity" in df.columns and "Amount_HT" in df.columns:
            df["Total"] = df["Amount_HT"]
    
    return df


# -----------------------------
#   FUNCIÓN PRINCIPAL
# -----------------------------
def procesar_factura_universal(pdf_path: str) -> Optional[pd.DataFrame]:
    """
    Procesa cualquier factura usando detección inteligente de tablas.
    
    Args:
        pdf_path: Ruta al archivo PDF
        
    Returns:
        DataFrame con productos extraídos o None si falla
    """
    try:
        df = extraer_tabla_inteligente(pdf_path)
        
        if df is not None and not df.empty:
            return df
        
        return None
    
    except Exception as e:
        print(f"Error procesando factura universal: {e}")
        return None
