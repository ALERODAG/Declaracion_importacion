#!/usr/bin/env python3
"""
Sistema simplificado de procesamiento de declaraciones de importación.
Extrae información de la primera página únicamente.
"""

import json
import re
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


def extract_text_from_first_page(pdf_file: str) -> str:
    """Extrae texto de la primera página del PDF usando PyMuPDF con OCR como mejora."""
    try:
        import fitz  # PyMuPDF

        # Abrir el PDF
        doc = fitz.open(pdf_file)

        # Verificar que tenga páginas
        if len(doc) > 0:
            # Extraer texto de la primera página
            first_page = doc.load_page(0)
            page_text = first_page.get_text()

            if page_text and len(page_text.strip()) > 100:  # Si hay texto suficiente
                return page_text.strip()
            else:
                # Si no hay texto suficiente, intentar OCR
                print("Texto insuficiente, aplicando OCR...")
                return extract_text_with_ocr(first_page)

        doc.close()
        return ""
    except ImportError:
        print("Error: PyMuPDF (fitz) no está instalado")
        return ""
    except Exception as e:
        print(f"Error extrayendo texto con PyMuPDF: {e}")
        return ""


def extract_text_with_ocr(page) -> str:
    """Extrae texto usando OCR con EasyOCR como método alternativo."""
    try:
        import fitz  # PyMuPDF

        # Convertir página a imagen
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Escalar 2x para mejor OCR

        # Convertir pixmap a bytes
        img_data = pix.tobytes("png")

        # Guardar imagen temporalmente para OCR
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_file.write(img_data)
            temp_file_path = temp_file.name

        try:
            # Aplicar OCR usando EasyOCR
            import easyocr

            # Crear reader para español e inglés
            reader = easyocr.Reader(['es', 'en'])

            # Aplicar OCR
            results = reader.readtext(temp_file_path)

            # Combinar resultados de OCR
            text_lines = []
            for result in results:
                if len(result) >= 3:  # Verificar que tenemos (bbox, text, confidence)
                    bbox, text, confidence = result
                    # Verificar que confidence es un número y mayor a 0.5
                    if isinstance(confidence, (int, float)) and confidence > 0.5:
                        text_lines.append(text)

            final_text = '\n'.join(text_lines)
            return final_text.strip() if final_text else ""

        except ImportError as e:
            print(f"Error: EasyOCR no disponible - {e}")
            return ""
        except Exception as e:
            print(f"Error aplicando OCR con EasyOCR: {e}")
            return ""
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except ImportError as e:
        print(f"Error: PyMuPDF no disponible - {e}")
        return ""
    except Exception as e:
        print(f"Error aplicando OCR: {e}")
        return ""

def extract_text_from_all_pages(pdf_file: str) -> str:
    """Extrae texto de todas las páginas del PDF usando PyMuPDF, con OCR de respaldo cuando el texto es insuficiente en una página."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_file)
        texts = []

        for page_index in range(len(doc)):
            try:
                page = doc.load_page(page_index)
                page_text = page.get_text()

                # Si la página tiene texto suficiente, úsalo; si no, aplica OCR de respaldo
                if page_text and len(page_text.strip()) > 50:
                    texts.append(page_text.strip())
                else:
                    ocr_text = extract_text_with_ocr(page)
                    if ocr_text:
                        texts.append(ocr_text)
            except Exception:
                # Respaldo adicional: intentar OCR si falló la extracción directa
                try:
                    page = doc.load_page(page_index)
                    ocr_text = extract_text_with_ocr(page)
                    if ocr_text:
                        texts.append(ocr_text)
                except Exception:
                    # Si falla también el OCR, continuar con la siguiente página
                    pass

        doc.close()
        return "\n".join(texts).strip()
    except ImportError:
        print("Error: PyMuPDF (fitz) no está instalado")
        return ""
    except Exception as e:
        print(f"Error extrayendo texto de todas las páginas: {e}")
        return ""
def export_to_excel(data: dict, output_file: str) -> None:
    """Exporta los datos a Excel en hoja 'Informacion_General'."""
    try:
        # Crear DataFrame con los datos
        df = pd.DataFrame([data])

        # Crear archivo Excel
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name='Informacion_General', index=False)

        print(f"Datos exportados a Excel: {output_file} (hoja: Informacion_General)")

    except Exception as e:
        print(f"Error exportando a Excel: {e}")


def extract_first_page_data(text: str, pdf_filename: str) -> dict:
    """Extrae información de la primera página según especificaciones."""
    data = {}

    # Buscar componentes de la empresa (PyMuPDF puede fragmentar el texto)
    lines = text.split('\n')

    # Buscar NIT, DV y empresa en líneas separadas
    nit_line = ""
    dv_line = ""
    empresa_line = ""

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if line_stripped == "900428482":
            nit_line = line_stripped
        elif line_stripped == "1" and i > 0 and lines[i-1].strip() == "900428482":
            dv_line = line_stripped
        elif "YADAS WT IMPORTACIONES S.A.S." in line:
            empresa_line = line_stripped

    # Si encontramos la empresa, continuar
    if empresa_line:
        # Buscar "PRODUCTO" y cortar el texto ahí para eliminar todo lo que sigue
        producto_idx = text.find("PRODUCTO")
        if producto_idx != -1:
            # Cortar el texto en "PRODUCTO" para eliminar todo lo que sigue
            text = text[:producto_idx]

        # Procesar líneas
        lines = text.split('\n')
        current_field_51_value = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Saltar líneas con solo ceros o X
            if re.match(r'^[0\s\.]+\.?\s*$', line) or re.match(r'^[Xx\s]+$', line):
                continue

            # Procesar información básica
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                data[key] = value
            else:
                # Líneas sin formato clave:valor
                if '@' in line and 'GMAIL.COM' in line:
                    data['EMAIL_PROVEEDOR'] = line
                # MODIFICADO: Mejorar detección de numero de factura para diferentes formatos
                # Buscar patrones comunes de numero de factura: FC-, HMM, y otros códigos alfanuméricos
                elif 'FC-' in line or 'HMM' in line or re.search(r'^[A-Z]{3}\d+', line):
                    data['NUMERO_FACTURA'] = line.strip()
                elif re.search(r'^\d{10}', line):
                    data['CODIGO_ARANCELARIO'] = line
                elif re.search(r'\d{4}\s+\d{2}\s+\d{2}', line):
                    data['FECHA_FACTURA'] = line
                elif 'YADAS WT IMPORTACIONES S.A.S.' in line:
                    data['NOMBRE_IMPORTADOR'] = line.strip()
                elif 'BENITOMO WORLD S.A' in line or 'NSK LATIN AMERICA INC' in line:
                    data['NOMBRE_PROVEEDOR_EXTERIOR'] = line.strip()
                elif line.strip() == '51':
                    # CAMBIO: Mejorar lógica para campo 51 - buscar numero de factura después del campo 51
                    current_field_51_value = '51'
                elif current_field_51_value == '51' and line.strip().isdigit():
                    # Si venimos del campo 51 y encontramos un número, podría ser el numero de factura
                    data['NUMERO_FACTURA_CAMPO_51'] = line.strip()
                    current_field_51_value = None

        return data

    return data


def process_pdf_file(pdf_file: str) -> dict:
    """Procesa un archivo PDF individual."""
    try:
        print(f"Iniciando procesamiento de: {pdf_file}")

        # Validar archivo
        if not Path(pdf_file).exists():
            return {"error": f"Archivo no encontrado: {pdf_file}"}

        # Extraer texto: primera página para datos generales y TODAS las páginas para productos
        text_first = extract_text_from_first_page(pdf_file)
        if not text_first:
            return {"error": f"No se pudo extraer texto de: {pdf_file}"}
        text_all = extract_text_from_all_pages(pdf_file) or text_first

        # Guardar textos extraídos (para depuración)
        text_file_first = pdf_file.replace('.pdf', '_first_page_text.txt')
        with open(text_file_first, 'w', encoding='utf-8') as f:
            f.write(text_first)
        text_file_all = pdf_file.replace('.pdf', '_all_pages_text.txt')
        with open(text_file_all, 'w', encoding='utf-8') as f:
            f.write(text_all)

        # Extraer datos generales de la PRIMERA página
        data = extract_first_page_data(text_first, pdf_file)

        if data:
            # Crear JSON output
            json_output = {
                'datos_generales': [data],
                'productos': [],
                'metadata': {
                    'fecha_procesamiento': datetime.now().isoformat(),
                    'archivo_procesado': pdf_file,
                    'total_declaraciones': 1,
                    'total_productos': 0
                }
            }

            # Guardar JSON
            json_file = pdf_file.replace('.pdf', '.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_output, f, indent=2, ensure_ascii=False)

            # Exportar a Excel (datos generales)
            excel_file = pdf_file.replace('.pdf', '.xlsx')
            export_to_excel(data, excel_file)

            # Extraer y guardar productos usando TODAS las páginas
            products_list = extract_and_save_products(text_all, pdf_file, excel_file)

            # Actualizar metadata con el número real de productos
            json_output['metadata']['total_productos'] = len(products_list)
            json_output['productos'] = products_list

            print("JSON output:")
            print(json.dumps(json_output, indent=2, ensure_ascii=False))

            return json_output
        else:
            return {"error": "No se encontraron datos para procesar"}

    except Exception as e:
        error_msg = f"Error procesando {pdf_file}: {str(e)}"
        print(error_msg)
        return {"error": error_msg}


def extract_and_save_products(text: str, pdf_file: str, excel_file: str) -> List[Dict[str, Any]]:
    """
    Extrae productos del texto y los guarda en la hoja "Productos" del Excel.

    Args:
        text: Texto extraído del PDF
        pdf_file: Nombre del archivo PDF
        excel_file: Archivo Excel de salida

    Returns:
        List[Dict[str, Any]]: Lista de productos extraídos
    """
    try:
        from productos import ProductExtractor

        # Crear extractor de productos
        extractor = ProductExtractor()

        # Extraer productos
        products_df = extractor.extract_products_from_text(text, pdf_file)

        if not products_df.empty:
            # Guardar productos en Excel
            extractor.save_products_to_excel(products_df, excel_file)
            print(f"Productos extraídos y guardados: {len(products_df)} productos")

            # Convertir DataFrame a lista de diccionarios
            products_list = products_df.to_dict('records')
            return products_list
        else:
            print("No se encontraron productos para extraer")
            return []

    except ImportError as e:
        print(f"Error importando ProductExtractor: {e}")
        return []
    except Exception as e:
        print(f"Error extrayendo productos: {e}")
        return []


def main():
    """Función principal de ejecución."""
    import glob
    import os

    # Cambiar al directorio del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Encontrar archivos PDF
    pdf_files = glob.glob("*.pdf")
    if not pdf_files:
        print("No se encontraron archivos PDF en el directorio")
        return

    print(f"Iniciando procesamiento... Encontrados {len(pdf_files)} archivos PDF")

    for pdf_file in pdf_files:
        result = process_pdf_file(pdf_file)

        if "error" not in result:
            print(f"Procesamiento completado exitosamente: {pdf_file}")
        else:
            print(f"Error en {pdf_file}: {result['error']}")


if __name__ == "__main__":
    main()