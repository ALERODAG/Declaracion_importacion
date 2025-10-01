#!/usr/bin/env python3
"""
Consolidador de información de PDFs de declaraciones de importación.

Este módulo procesa archivos PDF de declaraciones de importación y extrae
la información estructurada en un archivo Excel consolidado con hojas
Datos_Generales y Productos siguiendo las especificaciones del usuario.

Autor: Sistema de Consolidación
Versión: 1.0.0
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from datetime import datetime

# Importar módulos personalizados
from parsers.general_info_parser import GeneralInfoParser
from extractors.products_parser import ProductsParser
from utils.text_utils import TextUtils
from writers.excel_writer import ExcelWriter


class PDFConsolidator:
    """
    Clase principal para consolidar información de PDFs de declaraciones.
    """

    def __init__(self, output_file: str = "Consolidado.xlsx"):
        """
        Inicializa el consolidador.

        Args:
            output_file: Nombre del archivo Excel de salida
        """
        self.output_file = output_file
        self.text_utils = TextUtils()
        self.general_parser = GeneralInfoParser()
        self.products_parser = ProductsParser()
        self.excel_writer = ExcelWriter(output_file)

        # Configurar logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configura el sistema de logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('consolidacion.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def process_pdf(self, pdf_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Procesa un archivo PDF individual.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: DataFrames de datos generales y productos
        """
        self.logger.info(f"Iniciando procesamiento de: {pdf_path}")

        try:
            # Extraer texto del PDF
            text = self._extract_text_from_pdf(pdf_path)
            if not text:
                self.logger.error(f"No se pudo extraer texto de: {pdf_path}")
                return pd.DataFrame(), pd.DataFrame()

            # Procesar texto
            cleaned_text = self.text_utils.clean_text(text)

            # Extraer datos generales (primera página)
            general_data = self.general_parser.parse_general_info(cleaned_text, pdf_path)

            # Extraer productos
            products_data = self.products_parser.parse_products(cleaned_text, pdf_path)

            self.logger.info(f"Completado {pdf_path}: {len(general_data)} registros generales, {len(products_data)} productos")

            return general_data, products_data

        except Exception as e:
            self.logger.error(f"Error procesando {pdf_path}: {str(e)}")
            return pd.DataFrame(), pd.DataFrame()

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extrae texto de un archivo PDF.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            str: Texto extraído del PDF
        """
        try:
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text.strip()

        except ImportError:
            self.logger.error("pdfplumber no está instalado")
            return ""
        except Exception as e:
            self.logger.error(f"Error extrayendo texto: {e}")
            return ""

    def process_all_pdfs(self, pdf_directory: str = ".") -> None:
        """
        Procesa todos los archivos PDF en un directorio.

        Args:
            pdf_directory: Directorio que contiene los PDFs
        """
        self.logger.info(f"Procesando PDFs en: {pdf_directory}")

        # Encontrar todos los archivos PDF
        pdf_files = list(Path(pdf_directory).glob("*.pdf"))

        if not pdf_files:
            self.logger.warning(f"No se encontraron archivos PDF en: {pdf_directory}")
            return

        all_general_data = []
        all_products_data = []

        for pdf_file in pdf_files:
            self.logger.info(f"Procesando: {pdf_file.name}")

            # Procesar PDF individual
            general_data, products_data = self.process_pdf(str(pdf_file))

            # Agregar datos a las listas generales
            if not general_data.empty:
                all_general_data.append(general_data)

            if not products_data.empty:
                all_products_data.append(products_data)

        # Consolidar y guardar resultados
        if all_general_data or all_products_data:
            self._save_consolidated_data(all_general_data, all_products_data)
        else:
            self.logger.warning("No se encontraron datos para consolidar")

    def _save_consolidated_data(self, general_data_list: List[pd.DataFrame],
                               products_data_list: List[pd.DataFrame]) -> None:
        """
        Guarda los datos consolidados en Excel.

        Args:
            general_data_list: Lista de DataFrames de datos generales
            products_data_list: Lista de DataFrames de productos
        """
        try:
            # Consolidar datos generales
            if general_data_list:
                combined_general = pd.concat(general_data_list, ignore_index=True)
                self.logger.info(f"Datos generales consolidados: {len(combined_general)} registros")
            else:
                combined_general = pd.DataFrame()

            # Consolidar productos
            if products_data_list:
                combined_products = pd.concat(products_data_list, ignore_index=True)
                self.logger.info(f"Productos consolidados: {len(combined_products)} registros")
            else:
                combined_products = pd.DataFrame()

            # Guardar en Excel
            self.excel_writer.write_to_excel(combined_general, combined_products)

            self.logger.info(f"Datos consolidados guardados en: {self.output_file}")

        except Exception as e:
            self.logger.error(f"Error guardando datos consolidados: {str(e)}")
            raise


def main():
    """Función principal de ejecución."""
    consolidator = PDFConsolidator()
    consolidator.process_all_pdfs()


if __name__ == "__main__":
    main()