#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#SCRIPT PRODUCTOS

import os
import re
from typing import cast, List, Dict, Any, Optional
import pandas as pd

# =========================
# Dependencia: PyMuPDF
# =========================
try:
    import fitz  # PyMuPDF
except ImportError as e:
    raise RuntimeError(
        "No se encontró PyMuPDF. Instálalo con:\n\n    pip install pymupdf\n"
    ) from e

# =========================
# TextUtils (import o fallback) - DEBE ir antes de ProductExtractor
# =========================
try:
    # Si tienes tu utilitario propio, se usará este
    from utils.text_utils import TextUtils  # type: ignore[import-not-found]
except Exception:
    # Fallback mínimo para limpieza básica
    class TextUtils:
        def clean_text(self, t: str) -> str:
            t = t.replace("\r", "\n")
            t = re.sub(r"[ \t]+", " ", t)
            t = re.sub(r"\n+", "\n", t)
            return t.strip()

# =========================
# Utilidades de extracción sueltas
# =========================

def extraer_texto_pdf(ruta_pdf: str) -> str:
    texto = ""
    try:
        with fitz.open(ruta_pdf) as doc:
            for p in doc:
                page = cast("fitz.Page", p)
                texto += page.get_text("text")  # type: ignore[attr-defined]
                
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
# Búsqueda robusta del template
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
# Extractor de productos
# =========================

class ProductExtractor:
    """Extractor de productos de PDFs de declaraciones de importación (autopartes).
    NO extrae: Moneda, Valor_FOB, Incoterm, Peso_Neto, Peso_Bruto, API, ACEA.
    """

    # ======== Configuración ========
    SUMAR_CANTIDADES_EN_BLOQUE = False

    # ======== columnas base ========
    BASE_COLUMNS = [
        'Producto', 'Subpartida', 'Marca', 'Modelo', 'Referencia', 'Serial',
        'Compatibilidad', 'Cantidad', 'Unidad', 'Pais_Origen', 'Codigo_Pais_Origen',
        'Archivo', 'Declaracion'
    ]

    # ======== columnas opcionales ========
    OPTIONAL_COLUMNS = [
        'Categoria', 'Material', 'Composicion', 'Presentacion_Comercial',
        'Estado_Producto', 'Norma_Tecnica',
        'Viscosidad', 'Tipo_Aceite', 'Capacidad_L',
        'Tipo_Filtro', 'Micraje', 'Medidas',
        'Tipo_Bujia', 'Rosca', 'Numero_Calor',
        'Tipo_Terminal', 'Longitud', 'Ancho', 'Paso',
        'Tipo_Sensor', 'Voltaje',
        'Tipo_Soporte',
        'Incluye_Accesorios',
    ]

    STD_COLUMNS = BASE_COLUMNS + OPTIONAL_COLUMNS

    def __init__(self):
        self.text_utils = TextUtils()

        # ==== Patrones (strings) ====
        self.patrones_uso = [
            r"USO\s*:\s*([^,\n]+)",
            r"USO\s*O\s*DESTINO\s*:\s*([^,\n]+)",
            r"APLICACI[ÓO]N\s*:\s*([^,\n]+)",
            r"COMPATIBILIDAD\s*:\s*([^,\n]+)",
            r"DESTINO\s*:\s*([^,\n]+)",
        ]
        self.patrones_categoria = [r"CATEGOR[ÍI]A\s*:\s*([^\n,]+)", r"TIPO\s*DE\s*REPUESTO\s*:\s*([^\n,]+)"]
        self.patrones_material = [r"MATERIAL\s*:\s*([^\n,]+)"]
        self.patrones_presentacion = [r"EMPAQUE\s*:\s*([^\n,]+)", r"PRESENTACI[ÓO]N\s*:\s*([^\n,]+)"]
        self.patrones_estado = [r"ESTADO\s*:\s*(NUEVO|USADO|REMANUFACTURADO|RECONSTRUIDO)", r"NUEVO|USADO|REMANUFACTURADO|RECONSTRUIDO"]
        self.patrones_norma = [r"NORMA\s*:\s*([^\n,]+)", r"CERTIFICACI[ÓO]N\s*:\s*([^\n,]+)"]
        self.patrones_oem = [r"(?:N[ÚU]MERO\s*OEM|OEM|P\/N|PN|P\.N\.)\s*[:\-]?\s*([A-Z0-9\-\._\/ ]+)"]
        self.patrones_after = [r"(?:AFTERMARKET|EQUIV\.?|EQUIVALENTE)\s*[:\-]?\s*([A-Z0-9\-\._\/ ]+)"]
        self.patrones_unidad = [r"\bUNIDAD(?:ES)?\b|\bUND\b|\bUNID\b"]
        self.patrones_procedencia = [r"PA[IÍ]S\s*PROCEDENCIA\s*:\s*([A-ZÁÉÍÓÚÜÑ ]+)"]
        self.patrones_subpartida = [r"SUBPARTIDA\s*[:\-]?\s*([\d\.]{8,10})"]

        # Aceites (sin API/ACEA)
        self.patrones_viscosidad = [r"\b(\d{1,2}W-\d{1,2})\b"]
        self.patrones_tipo_aceite = [r"\b(SINT[EÉ]TICO|MINERAL|SEMISINT[EÉ]TICO)\b"]
        self.patrones_capacidad_l = [r"\b(\d+(?:[\.,]\d+)?)\s*(L|LTS|LITROS)\b"]

        # Filtros
        self.patrones_tipo_filtro = [r"\bFILTRO\s*(DE\s*[A-ZÁÉÍÓÚÜÑ]+)?\b"]
        self.patrones_micraje = [r"\b(\d{1,3})\s*MICRAS?\b"]
        self.patrones_medidas_generic = [r"\b(\d+(?:[\.,]\d+)?\s*x\s*\d+(?:[\.,]\d+)?\s*x\s*\d+(?:[\.,]\d+)?)\b"]

        # Bujías
        self.patrones_tipo_bujia = [r"\bBUJ[IÍ]A\s*(IRIDIO|N[IÍ]QUEL|PLATINO)\b"]
        self.patrones_rosca = [r"\bM\d{6}\b|\bM\d{1,2}\s*x\s*\d(?:[\.,]\d+)?\b"]
        self.patrones_numero_calor = [r"\bN[ÚU]MERO\s*DE\s*CALOR\s*[:\-]?\s*([A-Z0-9\-]+)\b"]

        # Cables / Correas
        self.patrones_tipo_terminal = [r"\bTERMINAL\s*[:\-]?\s*([A-Z0-9\/\-\s]+)\b"]
        self.patrones_longitud = [r"\bLONGITUD\s*[:\-]?\s*([\d\.,]+)\s*(MM|CM|M)\b"]
        self.patrones_ancho = [r"\bANCHO\s*[:\-]?\s*([\d\.,]+)\s*(MM|CM|M)\b"]
        self.patrones_paso = [r"\bPASO\s*[:\-]?\s*([\d\.,]+)\s*(MM|IN)\b"]

        # Sensores
        self.patrones_tipo_sensor = [r"\bSENSOR\s*(MAP|O2|ABS|TPS|MAF|CKP|CMP)\b"]
        self.patrones_voltaje = [r"\b(\d{1,2}(?:[\.,]\d+)?)\s*V\b"]

        # Soportes / Depósitos
        self.patrones_tipo_soporte = [r"\bSOPORTE\s*(HIDR[ÁA]ULICO|DE\s*CAUCHO|RIGIDO)\b"]
        self.patrones_incluye = [r"\b(CON\s*TAPA|SIN\s*TAPA|CON\s*SENSOR|SIN\s*SENSOR)\b"]

        # ===== Cantidades (no sumar) =====
        units_alt = r'UND|UNID|UNIDADES|PCS|PIEZAS|PZA|PZ'
        self.re_qty_with_unit = re.compile(
            r'\bCANT(?:IDAD)?[^\n]{0,80}(\d{1,9})\s*(?:' + units_alt + r')\b',
            re.IGNORECASE
        )
        self.re_qty_paren_opt_unit = re.compile(
            r'\bCANT(?:IDAD)?[^\n]{0,80}\((\d{1,9})\)\s*(?:' + units_alt + r')?',
            re.IGNORECASE
        )
        self.re_qty_simple_no_unit = re.compile(
            r'\bCANT(?:IDAD)?[^\n]{0,80}(\d{1,9})(?!\s*(?:' + units_alt + r'))',
            re.IGNORECASE
        )

    # ==========================
    # Extracción de texto
    # ==========================
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        texto = ""
        with fitz.open(pdf_path) as doc:
            for p in doc:
                page = cast("fitz.Page", p)
                texto += page.get_text("text", sort=True) + "\n"  # type: ignore[attr-defined]
        return texto
          

    # ==========================
    # Limpiezas internas
    # ==========================
    def _strip_no_diligenciable_blocks(self, t: str) -> str:
        src = t
        low = src.lower()
        while True:
            i1 = low.find('<!-- continua')
            i2 = low.find('<-- continua')
            start = i1 if (i1 != -1 and (i2 == -1 or i1 < i2)) else i2
            if start == -1:
                break
            candidates = [low.find('<< do', start), low.find('<<do', start)]
            candidates = [c for c in candidates if c != -1]
            end = min(candidates) if candidates else -1
            if end == -1:
                break
            src = src[:start] + src[end:]
            low = src.lower()
        return src

    def _strip_inline_do_markers(self, t: str) -> str:
        src = t
        low = src.lower()
        pos = 0
        out: List[str] = []
        L = len(src)
        while pos < L:
            i = low.find('<<', pos)
            if i == -1:
                out.append(src[pos:])
                break
            out.append(src[pos:i])
            j = low.find('>>', i + 2)
            if j == -1:
                out.append(src[i:])
                break
            inner = low[i+2:j].strip()
            if ('do' in inner) or ('declar' in inner):
                out.append(' ')
            else:
                out.append(src[i:j+2])
            pos = j + 2
        cleaned = ''.join(out)
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned


# Borrar especio no diligenciable entre enl formato de la declaracion y la informacino de los productos
    def clean_text(self, text: str) -> str:
        t = self.text_utils.clean_text(text)
        t = self._strip_no_diligenciable_blocks(t)
        t = self._strip_inline_do_markers(t)
        t = re.sub(r'NO\s+DILIGENCIABLE', ' ', t, flags=re.IGNORECASE)
        t = re.sub(r'[ \t]+', ' ', t)
        t = re.sub(r'\n+', '\n', t)
        return t.strip()

    # ==========================
    # Helpers / extracción de campos
    # ==========================
    def _first_label_pos(self, text: str) -> int:
        label = re.search(
            r'\b(?:REFERENCIA|REF\.?|SER(?:IAL)?\.?|USO|DESTINO|APLICACI[ÓO]N|COMPATIBILIDAD|PA[IÍ]S\s*ORIGEN|PA[IÍ]S\s*PROCEDENCIA|MARCA|MODELO|COMPOSICION|MATERIAL|CATEGOR[ÍI]A|PRESENTACI[ÓO]N|SUBPARTIDA)\s*:',
            text, flags=re.IGNORECASE,
        )
        return label.start() if label else -1

    def _trim_numeric_tail(self, s: str) -> str:
        if not s:
            return s
        m = re.search(r',\s*(?:[\d\s\.,]{6,})$', s)
        return s[:m.start()] if m else s

    def _dedupe_ref(self, ref: str) -> str:
        ref = ref.strip()
        if '-' in ref:
            left, right = ref.split('-', 1)
            if left.strip().upper() == right.strip().upper():
                return left.strip()
        return ref

    def _extract_with_patterns(self, text: str, patterns: list):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return (m.group(1) if m.groups() else m.group(0)).strip()
        return ""

    def _extract_pais_origen(self, text: str, fields: dict):
        m = re.search(
            r'PA[IÍ]S\s*ORIGEN\s*:\s*([A-ZÁÉÍÓÚÜÑ ]+?)\s*[-–—]\s*(\d{2,3})\.?',
            text, flags=re.IGNORECASE,
        )
        if m:
            fields['Pais_Origen'] = m.group(1).strip()
            fields['Codigo_Pais_Origen'] = m.group(2).strip()
        else:
            m2 = re.search(r'PA[IÍ]S\s*ORIGEN\s*:\s*([A-ZÁÉÍÓÚÜÑ ]+)', text, flags=re.IGNORECASE)
            if m2:
                fields['Pais_Origen'] = m2.group(1).strip()

    # ==========================
    # Núcleo de extracción de un producto
    # ==========================
    def _extract_product_fields(self, product_block: str) -> dict:
        """
        Extrae campos de un bloque de producto de forma GENÉRICA y ROBUSTA.
        Soporta tanto formato separado por comas como por espacios/newlines.
        """
        fields: Dict[str, str] = {}
        block = product_block.strip()

        # ===== PASO 1: Identificar el producto =====
        # El producto es todo lo anterior al primer campo con ":"
        # Buscar "ETIQUETA:"
        first_field_match = re.search(r'\b[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s/\.]{2,40}?\s*:', block, re.IGNORECASE)
        
        if first_field_match:
            producto_text = block[:first_field_match.start()].strip(' ,.;:-')
            producto_text = self._trim_numeric_tail(producto_text)
            if producto_text and len(producto_text) >= 3:
                fields['Producto'] = producto_text
            
            # El resto es texto de campos
            fields_text = block[first_field_match.start():]
        else:
            # Todo es producto si no hay etiquetas
            fields['Producto'] = self._trim_numeric_tail(block.strip(' ,.;:-'))
            return fields

        # ===== PASO 2: Extracción con REGEX (Más robusto que split) =====
        # Busca pares "ETIQUETA: Valor"
        # El valor termina cuando encuentra la siguiente etiqueta o el fin.
        # Soporta separadores: comas, puntos, espacios, newlines antes de la siguiente etiqueta.
        
        generic_pattern = re.compile(
            r'\b([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s/\.]{2,60}?)\s*:\s*'  # Grupo 1: Etiqueta
            r'(.*?)'  # Grupo 2: Valor (non-greedy)
            # Lookahead: Para en la siguiente etiqueta (precedida opcionalmente por comas/puntos) o fin de string
            r'(?=\s*(?:[,;.]\s*)?[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s/\.]{2,60}?\s*:|$)', 
            re.IGNORECASE | re.DOTALL
        )
        
        for match in generic_pattern.finditer(fields_text):
            label = match.group(1).strip()
            value = match.group(2).strip()
            
            if not value or len(value) > 1000: # Safety check
                continue
            
            # Limpiar valor de comas finales
            value = value.strip(' ,.;:\n\r\t')
            
            # Normalizar nombre del campo
            field_name = self._normalize_field_name(label)
            
            if field_name and value:
                fields[field_name] = value

        # ===== PASO 3: Post-procesamiento de campos específicos =====
        
        # Limpiar TODOS los valores de marcadores de zona no tramitable
        for field_name in list(fields.keys()):
            if field_name == 'Producto':
                continue
            
            value = fields[field_name]
            
            # Eliminar marcadores de zona no tramitable: // XXXXX... números
            # Patrón: // seguido de X's y números
            value = re.sub(r'//\s*X+.*$', '', value, flags=re.IGNORECASE)
            value = re.sub(r'//.*$', '', value)  # Eliminar cualquier cosa después de //
            
            # Limpiar espacios extra
            value = value.strip()
            
            if value:
                fields[field_name] = value
            else:
                # Si el valor queda vacío después de limpiar, eliminar el campo
                del fields[field_name]
        
        # Detectar si CANTIDAD está "escondida" dentro de PAÍS ORIGEN
        # Formato: "REINO UNIDO - 628. CANT (31) UND" o similar
        if 'Pais_Origen' in fields and 'Cantidad' not in fields:
            pais_value = fields['Pais_Origen']
            
            # Estrategia más agresiva: Buscar cualquier patrón de cantidad dentro del valor de país
            # 1. Buscar "CANT (31)" o "CANT: 31"
            m_qty = re.search(r'CANT(?:IDAD|\.)?\s*(?:\()?\s*(\d+(?:[.,]\d+)?)\s*(?:\))?', pais_value, re.IGNORECASE)
            
            # 2. Si no, buscar patrón "(31) UND" o "31 UND" al final
            if not m_qty:
                 m_qty = re.search(r'[\(\s](\d+(?:[.,]\d+)?)\)?\s*(?:UND|UNID|UNIDADES|PCS)', pais_value, re.IGNORECASE)

            if m_qty:
                fields['Cantidad'] = m_qty.group(1)
                fields['Unidad'] = 'UND' # Asumir unidad si se encuentra este patrón
                
                # Opcional: Limpiar la cantidad del campo país para que quede solo el país
                # (Esto es estético, pero ayuda)
                # re.sub(...)
        
        # Si aún no hay cantidad, buscar en TODOS los campos (incluyendo Producto)
        if 'Cantidad' not in fields:
            for field_name, field_value in list(fields.items()):
                # Ya no saltamos 'Producto' - a veces la cantidad está ahí
                # if field_name == 'Producto':
                #    continue
                
                # Patrones variados para encontrar cantidad:
                # 1. CANT(31) o CANTIDAD(31)
                # 2. CANT: 31 o CANT. 31
                # 3. 31 UND o 31 UNID (sin etiqueta CANT)
                
                # Regex 1: Explicit labels with parens or colons
                # Matches: CANT(10), CANTIDAD(10), CANT:10, CANT. 10
                match = re.search(r'(?:CANT(?:IDAD|\.)?)\s*(?:[:\.]|\s+)?\s*(?:\()?\s*(\d+(?:[.,]\d+)?)\s*(?:\))?', field_value, re.IGNORECASE)
                
                # Regex 2: Number followed by Unit (implicit quantity)
                # Matches: 10 UND, 10 PCS, 10 UNIDADES
                if not match:
                    match = re.search(r'\b(\d+(?:[.,]\d+)?)\s*(?:UND|UNID|UNIDADES|PCS|PZA|PIEZA)\b', field_value, re.IGNORECASE)

                if match:
                    qty_found = match.group(1)
                    fields['Cantidad'] = qty_found
                    
                    # Intentar limpiar el valor del campo original
                    # Si fue por etiqueta
                    cleaned_value = re.sub(r'(?:CANT(?:IDAD|\.)?)\s*(?:[:\.]|\s+)?\s*(?:\()?\s*\d+(?:[.,]\d+)?\s*(?:\))?', '', field_value, flags=re.IGNORECASE)
                    # Si fue por unidad
                    cleaned_value = re.sub(r'\b\d+(?:[.,]\d+)?\s*(?:UND|UNID|UNIDADES|PCS|PZA|PIEZA)\b', '', cleaned_value, flags=re.IGNORECASE)
                    
                    # Limpiar basura residual
                    cleaned_value = cleaned_value.strip(' ,.;:-')
                    if cleaned_value:
                        fields[field_name] = cleaned_value
                    
                    # Si encontramos unidad implicita, setearla también
                    if 'Unidad' not in fields:
                         # Verificar si hay unidad en el texto original cerca del numero
                         m_unit = re.search(r'\b(UND|UNID|UNIDADES|PCS|PZA|PIEZA)\b', field_value, re.IGNORECASE)
                         if m_unit:
                             fields['Unidad'] = 'UND' 
                    break
        
        # Normalizar REFERENCIA (eliminar duplicados como "ABC-ABC")
        if 'Referencia' in fields:
            fields['Referencia'] = self._dedupe_ref(fields['Referencia'])
        
        # Extraer código de país si está en formato "PAÍS - CÓDIGO" (y no se procesó arriba)
        if 'Pais_Origen' in fields and 'Codigo_Pais_Origen' not in fields:
            m = re.search(r'^(.+?)\s*[-–—]\s*(\d{2,3})\.?$', fields['Pais_Origen'])
            if m:
                fields['Pais_Origen'] = m.group(1).strip()
                fields['Codigo_Pais_Origen'] = m.group(2).strip()
        
        # Normalizar CANTIDAD - extraer solo el número
        if 'Cantidad' in fields:
            m = re.search(r'(\d+(?:[,\.]\d+)?)', fields['Cantidad'])
            if m:
                qty_str = m.group(1).replace(',', '.')
                try:
                    fields['Cantidad'] = str(int(float(qty_str)))
                except:
                    pass
        
        # Normalizar UNIDAD
        if 'Unidad' in fields:
            unidad_upper = fields['Unidad'].upper()
            if any(u in unidad_upper for u in ['UND', 'UNID', 'PCS', 'PZA', 'PIEZA']):
                fields['Unidad'] = 'UND'
        elif 'Cantidad' in fields:
            # Si hay cantidad pero no unidad, asumir UND
            fields['Unidad'] = 'UND'
        
        # Normalizar campos de estado
        if 'Estado_Producto' in fields:
            estado = fields['Estado_Producto'].upper()
            if 'NUEVO' in estado:
                fields['Estado_Producto'] = 'NUEVO'
            elif 'USADO' in estado:
                fields['Estado_Producto'] = 'USADO'
            elif 'REMANUFACTURADO' in estado or 'RECONSTRUIDO' in estado:
                fields['Estado_Producto'] = 'REMANUFACTURADO'

        return fields
    
    def _normalize_field_name(self, label: str) -> str:
        """
        Normaliza el nombre de un campo para consistencia.
        
        Ejemplos:
        - "PAÍS ORIGEN" -> "Pais_Origen"
        - "REF." -> "Referencia"
        - "DIMENSIONES" -> "Dimensiones"
        """
        # Diccionario de mapeos conocidos
        mappings = {
            # Variaciones de campos comunes
            'referencia': 'Referencia',
            'ref': 'Referencia',
            'ref.': 'Referencia',
            'serial': 'Serial',
            'ser': 'Serial',
            'ser.': 'Serial',
            'marca': 'Marca',
            'modelo': 'Modelo',
            'cantidad': 'Cantidad',
            'cant': 'Cantidad',
            'cant.': 'Cantidad',
            'unidad': 'Unidad',
            'und': 'Unidad',
            'uso': 'Compatibilidad',
            'uso o destino': 'Compatibilidad',
            'aplicación': 'Compatibilidad',
            'aplicacion': 'Compatibilidad',
            'compatibilidad': 'Compatibilidad',
            'destino': 'Compatibilidad',
            'país origen': 'Pais_Origen',
            'pais origen': 'Pais_Origen',
            'país de origen': 'Pais_Origen',
            'pais de origen': 'Pais_Origen',
            'país procedencia': 'Pais_Procedencia',
            'pais procedencia': 'Pais_Procedencia',
            'categoría': 'Categoria',
            'categoria': 'Categoria',
            'tipo de repuesto': 'Categoria',
            'material': 'Material',
            'composición': 'Composicion',
            'composicion': 'Composicion',
            'empaque': 'Presentacion_Comercial',
            'presentación': 'Presentacion_Comercial',
            'presentacion': 'Presentacion_Comercial',
            'estado': 'Estado_Producto',
            'norma': 'Norma_Tecnica',
            'certificación': 'Norma_Tecnica',
            'certificacion': 'Norma_Tecnica',
            'subpartida': 'Subpartida',
            'número oem': 'Numero_OEM',
            'numero oem': 'Numero_OEM',
            'oem': 'Numero_OEM',
            'p/n': 'Numero_OEM',
            'pn': 'Numero_OEM',
            'p.n.': 'Numero_OEM',
            'aftermarket': 'Numero_Aftermarket',
            'equiv.': 'Numero_Aftermarket',
            'equivalente': 'Numero_Aftermarket',
            
            # Campos específicos por tipo de producto
            'viscosidad': 'Viscosidad',
            'tipo aceite': 'Tipo_Aceite',
            'capacidad': 'Capacidad_L',
            'tipo filtro': 'Tipo_Filtro',
            'micraje': 'Micraje',
            'medidas': 'Medidas',
            'dimensiones': 'Dimensiones',
            'tipo bujía': 'Tipo_Bujia',
            'tipo bujia': 'Tipo_Bujia',
            'rosca': 'Rosca',
            'número de calor': 'Numero_Calor',
            'numero de calor': 'Numero_Calor',
            'terminal': 'Tipo_Terminal',
            'longitud': 'Longitud',
            'ancho': 'Ancho',
            'paso': 'Paso',
            'tipo sensor': 'Tipo_Sensor',
            'voltaje': 'Voltaje',
            'tipo soporte': 'Tipo_Soporte',
            'incluye': 'Incluye_Accesorios',
        }
        
        # Normalizar a minúsculas para comparación
        label_lower = label.lower().strip()
        
        # Buscar en mapeos conocidos
        if label_lower in mappings:
            return mappings[label_lower]
        
        # Si no está en mapeos, crear nombre estándar
        # Convertir a Title_Case_With_Underscores
        # "PAÍS ORIGEN" -> "Pais_Origen"
        # "DIMENSIONES" -> "Dimensiones"
        
        # Remover acentos para nombres de campos
        import unicodedata
        label_normalized = ''.join(
            c for c in unicodedata.normalize('NFD', label)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Reemplazar espacios y caracteres especiales con guión bajo
        label_normalized = re.sub(r'[^\w\s]', '', label_normalized)
        label_normalized = re.sub(r'\s+', '_', label_normalized)
        
        # Capitalizar primera letra de cada palabra
        parts = label_normalized.split('_')
        field_name = '_'.join(part.capitalize() for part in parts if part)
        
        return field_name

    # ==========================
    # Utilidades de DataFrame
    # ==========================
    def _drop_empty_optional_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Elimina columnas completamente vacías del DataFrame.
        Preserva las columnas 'Archivo', 'Declaracion' y columnas CORE aunque estén vacías.
        """
        cols_to_drop = []
        # Columnas que SIEMPRE deben aparecer, incluso si están vacías
        preserve_cols = [
            'Archivo', 'Declaracion', 'Producto', 
            'Cantidad', 'Unidad', 
            'Referencia', 'Marca', 'Modelo', 'Serial',
            'Pais_Origen'
        ]
        
        for col in df.columns:
            # No eliminar columnas prioritarias
            if col in preserve_cols:
                continue
                
            # Verificar si la columna está completamente vacía
            serie = df[col].astype(str).str.strip()
            if serie.eq("").all() or serie.isna().all():
                cols_to_drop.append(col)
        
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
            
        return df

    def extract_products_from_text(self, text: str, pdf_filename: str) -> pd.DataFrame:
        """
        Extrae productos del texto de forma DINÁMICA.
        Las columnas del DataFrame se crean basándose en los campos encontrados,
        sin usar plantillas predefinidas.
        """
        cleaned_text = self.clean_text(text)

        # Delimitación por declaraciones
        declaration_pattern = r'(DECLARACI[ÓO]N\s+(\d+)\s+DE\s+\d+)'
        declaration_matches = list(re.finditer(declaration_pattern, cleaned_text, flags=re.IGNORECASE))

        all_products = []

        for idx, match in enumerate(declaration_matches):
            declaration_num = match.group(2)
            start = match.end()
            end = declaration_matches[idx + 1].start() if idx + 1 < len(declaration_matches) else len(cleaned_text)
            declaration_text = cleaned_text[start:end].strip()

            product_pattern = (
                r'(?:PRODUCTO|NOMBRE\s+TECNICO\s+DEL\s+PRODUCTO)\s*:\s*'
                r'(.*?)(?://\s*(?=(?:PRODUCTO|NOMBRE\s+TECNICO\s+DEL\s+PRODUCTO)\s*:|$)|\Z)'
            )
            products = re.finditer(product_pattern, declaration_text, re.IGNORECASE | re.DOTALL)

            for product_match in products:
                product_text = product_match.group(1).strip()
                if not product_text:
                    continue

                # Extraer campos dinámicamente
                product_data = self._extract_product_fields(product_text)
                if product_data:
                    # Agregar metadatos al inicio
                    product_data['Archivo'] = pdf_filename
                    product_data['Declaracion'] = declaration_num
                    all_products.append(product_data)

        # Columnas CORE que siempre queremos ver
        core_cols = [
            'Archivo', 'Declaracion', 'Producto', 
            'Cantidad', 'Unidad', 
            'Referencia', 'Marca', 'Modelo', 'Serial',
            'Pais_Origen'
        ]

        if all_products:
            # Crear DataFrame con TODAS las columnas encontradas
            df = pd.DataFrame(all_products)
            
            # Asegurar que existan las columnas CORE (rellenar con vacío si faltan)
            for col in core_cols:
                if col not in df.columns:
                    df[col] = ""
            
            # Reordenar: Primero CORE, luego el resto alfabéticamente
            cols = df.columns.tolist()
            other_cols = [c for c in cols if c not in core_cols]
            other_cols.sort()
            
            final_cols = [c for c in core_cols if c in cols] + other_cols
            df = df[final_cols]
            
            # Eliminar columnas irrelevantes vacías (pero preservando las CORE)
            df = self._drop_empty_optional_columns(df)
        else:
            # DataFrame vacío con columnas CORE
            df = pd.DataFrame(columns=core_cols)

        return df

    def save_products_to_excel(self, df: pd.DataFrame, excel_file: str):
        if not df.empty:
            os.makedirs(os.path.dirname(excel_file), exist_ok=True)
            try:
                with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
                    df.to_excel(writer, sheet_name='Productos', index=False)
            except ImportError as e:
                raise RuntimeError(
                    "Para escribir .xlsx necesitas 'openpyxl'. Instala con: pip install openpyxl"
                ) from e
            print(f"Productos guardados en {excel_file}: {len(df)} productos")
        else:
            print("No se encontraron productos para guardar")

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
            "Para leer archivos .xlsx necesitas 'openpyxl'.\nInstala con: pip install openpyxl"
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

    # Si más adelante activas productos:
    # extractor = ProductExtractor()

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
            data = []
            for i in range(len(headers)):
                data.append(lines[i] if i < len(lines) else None)
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

        # ---- Productos: (aún desactivado en este main)
        df_products = pd.DataFrame()

        # ---- Guardado: UN EXCEL POR PDF con el MISMO NOMBRE
        excel_name = ("D:\DESARROLLO DE SOFTWARE\PDF_A_LEER\EXCEL_PDF_LEIDOS\prueba.xlsx")
        excel_path = os.path.join(output_dir, excel_name)

        if (df_decl is None or df_decl.empty) and (df_products is None or df_products.empty):
            print(f"   -> No hay datos para guardar en {excel_name}.")
            continue

        try:
            with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
                if df_decl is not None and not df_decl.empty:
                    df_decl.to_excel(writer, sheet_name="Declaraciones", index=False)
                # if df_products is not None and not df_products.empty:
                #     df_products.to_excel(writer, sheet_name="Productos", index=False)
        except ImportError as e:
            raise RuntimeError(
                "Para escribir .xlsx necesitas 'openpyxl'.\nInstala con: pip install openpyxl"
            ) from e

        print(f"   -> Archivo Excel generado: {excel_path}")
        print(f"      Declaraciones: {0 if df_decl is None else len(df_decl)}")

    print("\nProceso completado (un Excel por PDF).")
