#!/usr/bin/env python3
"""
Módulo independiente para extracción de información de productos.

Este módulo procesa la información de productos desde texto extraído de PDFs,
siguiendo las especificaciones detalladas para una extracción precisa y estructurada.
"""

import re
import pandas as pd
import logging
from typing import List, Dict, Any, Tuple, Optional


class ProductExtractor:
    """
    Extractor especializado para información de productos según especificaciones detalladas.
    """

    def __init__(self):
        """Inicializa el extractor de productos."""
        self.logger = logging.getLogger(__name__)

    def extract_products_from_text(self, text: str, pdf_filename: str) -> pd.DataFrame:
        """
        Extrae información de productos desde el texto del PDF.

        Args:
            text: Texto completo extraído del PDF
            pdf_filename: Nombre del archivo PDF para trazabilidad

        Returns:
            pd.DataFrame: DataFrame con los productos extraídos
        """
        products_data = []

        try:
            # 1. INICIO DE EXTRACCIÓN: Encontrar primera coincidencia de "PRODUCTO"
            first_product_idx = text.find("PRODUCTO:")
            if first_product_idx == -1:
                first_product_idx = text.find("NOMBRE TECNICO DEL PRODUCTO:")
                if first_product_idx == -1:
                    self.logger.warning(f"No se encontró información de productos en {pdf_filename}")
                    return pd.DataFrame()

            # Extraer texto desde el primer PRODUCTO hasta el final
            products_section = text[first_product_idx:]

            # 2. MANEJO DE MÚLTIPLES DECLARACIONES
            declarations_products = self._split_into_declarations(products_section)

            for decl_num, decl_text in declarations_products:
                # 3. EXTRAER PRODUCTOS DE CADA DECLARACIÓN
                declaration_products = self._extract_products_from_declaration(decl_text, decl_num, pdf_filename)
                products_data.extend(declaration_products)

            # 4. CREAR DATAFRAME
            if products_data:
                df = pd.DataFrame(products_data)
                self.logger.info(f"Extraídos {len(products_data)} productos de {pdf_filename}")
                return df
            else:
                self.logger.warning(f"No se encontraron productos válidos en {pdf_filename}")
                return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Error extrayendo productos de {pdf_filename}: {e}")
            return pd.DataFrame()

    def _split_into_declarations(self, products_section: str) -> List[Tuple[str, str]]:
        """
        Divide el texto en declaraciones individuales.

        Cada declaración termina con "//" seguido de caracteres "x".

        Args:
            products_section: Sección de texto con productos

        Returns:
            List[Tuple[str, str]]: Lista de (número_declaración, texto_declaración)
        """
        declarations = []

        # Patrón para encontrar declaraciones: DECLARACION(X-Y)
        decl_pattern = r'DECLARACION\((\d+)-(\d+)\)'

        # Buscar todas las declaraciones
        declaration_matches = list(re.finditer(decl_pattern, products_section))

        if not declaration_matches:
            # Si no hay declaraciones marcadas, tratar todo como una sola declaración
            return [("1", products_section)]

        # Procesar cada declaración encontrada
        for i, match in enumerate(declaration_matches):
            decl_start = match.start()
            current_decl_num = match.group(1)

            # Determinar fin de la declaración
            if i + 1 < len(declaration_matches):
                # Hasta el inicio de la siguiente declaración
                decl_end = declaration_matches[i + 1].start()
            else:
                # Hasta el final del texto
                decl_end = len(products_section)

            # Extraer texto de la declaración
            decl_text = products_section[decl_start:decl_end]
            # Recortar cualquier línea de relleno compuesta solo por X/x al final de la declaración
            x_line_match = re.search(r'^(?:X+|x+)\s*$', decl_text, flags=re.MULTILINE)
            if x_line_match:
                decl_text = decl_text[:x_line_match.start()].rstrip()
            declarations.append((current_decl_num, decl_text))

        return declarations

    def _extract_products_from_declaration(self, decl_text: str, decl_num: str, pdf_filename: str) -> List[Dict[str, Any]]:
        """
        Extrae productos individuales de una declaración.

        Args:
            decl_text: Texto de la declaración
            decl_num: Número de declaración
            pdf_filename: Nombre del archivo PDF

        Returns:
            List[Dict[str, Any]]: Lista de productos extraídos
        """
        products = []

        # 3. DELIMITACIÓN DE PRODUCTOS INDIVIDUALES
        # Cada producto termina con "//"
        product_blocks = decl_text.split("//")

        for block in product_blocks:
            block = block.strip()
            if not block:
                continue

            # Extraer información del producto
            product_info = self._parse_product_block(block, decl_num, pdf_filename)

            if product_info:
                products.append(product_info)

        return products

    def _parse_product_block(self, block: str, decl_num: str, pdf_filename: str) -> Optional[Dict[str, Any]]:
        """
        Parsea un bloque individual de producto.

        Args:
            block: Bloque de texto del producto
            decl_num: Número de declaración
            pdf_filename: Nombre del archivo PDF

        Returns:
            Dict[str, Any]: Información del producto parseada
        """
        product = {
            'archivo_origen': pdf_filename,
            'declaracion_numero': decl_num,
            'PRODUCTO': '',
            'MARCA': '',
            'MODELO': '',
            'REFERENCIA': '',
            'SERIAL': '',
            'USO_O_DESTINO': '',
            'TIPO_DE_MOTOR': '',
            'PAIS_ORIGEN': '',
            'CANT': ''
        }

        # 2. ESTRUCTURA DE CAMPOS: Extraer cada campo específico
        # Buscar cada etiqueta y extraer su valor

        # PRODUCTO
        producto_match = re.search(r'PRODUCTO:\s*(.*?)(?=,\s*MARCA:|$)', block)
        if producto_match:
            product['PRODUCTO'] = producto_match.group(1).strip()

        # MARCA
        marca_match = re.search(r'MARCA:\s*([^,]+)', block)
        if marca_match:
            product['MARCA'] = marca_match.group(1).strip()

        # MODELO
        modelo_match = re.search(r'MODELO:\s*([^,]+)', block)
        if modelo_match:
            product['MODELO'] = modelo_match.group(1).strip()

        # REFERENCIA (campo único y obligatorio)
        referencia_match = re.search(r'REFERENCIA:\s*([^,]+)', block)
        if referencia_match:
            product['REFERENCIA'] = referencia_match.group(1).strip()

        # SERIAL
        serial_match = re.search(r'SERIAL:\s*([^,]+)', block)
        if serial_match:
            product['SERIAL'] = serial_match.group(1).strip()

        # USO O DESTINO
        uso_match = re.search(r'USO O DESTINO:\s*([^,]+)', block)
        if uso_match:
            product['USO_O_DESTINO'] = uso_match.group(1).strip()

        # TIPO DE MOTOR AL QUE ESTA DESTINADO
        motor_match = re.search(r'TIPO DE MOTOR AL QUE ESTA DESTINADO:\s*([^,]+)', block)
        if motor_match:
            product['TIPO_DE_MOTOR'] = motor_match.group(1).strip()

        # PAIS ORIGEN Y CANT - MEJORADO: Parsear correctamente campos separados por " - " y ". CANT"
        # Buscar patrón: PAIS ORIGEN: [COUNTRY] - [NUMBER]. CANT ([QUANTITY]) UND
        pais_cant_match = re.search(r'PAIS ORIGEN:\s*([^,-]+)\s*-\s*(\d+)\.\s*CANT\s*\(\s*(\d+)\s*\)', block)
        if pais_cant_match:
            product['PAIS_ORIGEN'] = pais_cant_match.group(1).strip()
            product['CANT'] = pais_cant_match.group(3).strip()
        else:
            # MEJORADO: Buscar patrones más flexibles para PAIS ORIGEN
            # Patrón 1: PAIS ORIGEN: [COUNTRY] - [NUMBER]. CANT
            pais_match1 = re.search(r'PAIS ORIGEN:\s*([A-Z]+)\s*-\s*\d+\.?\s*CANT', block)
            if pais_match1:
                product['PAIS_ORIGEN'] = pais_match1.group(1).strip()

            # Patrón 2: PAIS ORIGEN: [COUNTRY] (sin número)
            pais_match2 = re.search(r'PAIS ORIGEN:\s*([A-Z]+(?:\s+[A-Z]+)*)', block)
            if pais_match2 and not product['PAIS_ORIGEN']:
                pais_value = pais_match2.group(1).strip()
                # Limpiar si contiene números o caracteres especiales
                if not re.search(r'\d', pais_value):
                    product['PAIS_ORIGEN'] = pais_value

            # Patrón 3: Buscar país en referencias técnicas
            if not product['PAIS_ORIGEN']:
                # Buscar países comunes en el texto
                countries = ['CHINA', 'JAPON', 'TAILANDIA', 'COREA', 'BRASIL', 'USA', 'ALEMANIA']
                for country in countries:
                    if country in block.upper():
                        product['PAIS_ORIGEN'] = country
                        break

            # Fallback: buscar CANT por separado
            if not product['CANT']:
                cant_match = re.search(r'CANT\s*\(\s*(\d+)\s*\)', block)
                if cant_match:
                    product['CANT'] = cant_match.group(1).strip()

        # Validación: debe tener al menos PRODUCTO
        if product['PRODUCTO']:
            return product
        else:
            return None

    def save_products_to_excel(self, products_df: pd.DataFrame, output_file: str) -> None:
        """
        Guarda los productos en una hoja Excel llamada "Productos".
        Si el archivo no existe, lo crea. Si existe, agrega la hoja.

        Args:
            products_df: DataFrame con productos
            output_file: Archivo Excel de salida
        """
        try:
            import os

            # VERIFICACIÓN Y CREACIÓN: Validar si el archivo Excel existe
            if not os.path.exists(output_file):
                # Si no existe, crear nuevo archivo Excel
                with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
                    products_df.to_excel(writer, sheet_name='Productos', index=False)
                self.logger.info(f"✅ Archivo Excel CREADO: {output_file} (hoja: Productos)")
            else:
                # Si existe, agregar hoja "Productos"
                try:
                    with pd.ExcelWriter(output_file, engine="openpyxl", mode='a') as writer:
                        products_df.to_excel(writer, sheet_name='Productos', index=False)
                    self.logger.info(f"✅ Productos AGREGADOS a: {output_file} (hoja: Productos)")
                except Exception as e:
                    # Si hay error al agregar hoja (ej. hoja ya existe), intentar sobreescribir
                    self.logger.warning(f"Error al agregar hoja, intentando sobreescribir: {e}")
                    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
                        products_df.to_excel(writer, sheet_name='Productos', index=False)
                    self.logger.info(f"✅ Productos SOBREESCRITOS en: {output_file} (hoja: Productos)")

        except Exception as e:
            self.logger.error(f"Error guardando productos en Excel: {e}")
            raise

    def process_pdf_products(self, pdf_file: str) -> pd.DataFrame:
        """
        Procesa productos de un PDF individual.

        Args:
            pdf_file: Ruta al archivo PDF

        Returns:
            pd.DataFrame: DataFrame con productos extraídos
        """
        # Extraer texto de TODAS las páginas usando la función de main_simple
        from main_simple import extract_text_from_all_pages

        text = extract_text_from_all_pages(pdf_file)
        if not text:
            return pd.DataFrame()

        # Extraer productos
        products_df = self.extract_products_from_text(text, pdf_file)

        return products_df


def main():
    """Función principal para pruebas independientes."""
    import glob
    import os

    # Configurar logging
    logging.basicConfig(level=logging.INFO)

    # Crear extractor
    extractor = ProductExtractor()

    # Cambiar al directorio del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Encontrar archivos PDF
    pdf_files = glob.glob("*.pdf")
    if not pdf_files:
        print("No se encontraron archivos PDF en el directorio")
        return

    print(f"Iniciando extracción de productos... Encontrados {len(pdf_files)} archivos PDF")

    for pdf_file in pdf_files:
        print(f"\nProcesando productos de: {pdf_file}")

        # Procesar productos
        products_df = extractor.process_pdf_products(pdf_file)

        if not products_df.empty:
            print(f"Productos encontrados: {len(products_df)}")

            # Guardar en Excel
            excel_file = pdf_file.replace('.pdf', '.xlsx')
            extractor.save_products_to_excel(products_df, excel_file)

            print(f"Productos guardados en: {excel_file}")
        else:
            print("No se encontraron productos")


if __name__ == "__main__":
    main()