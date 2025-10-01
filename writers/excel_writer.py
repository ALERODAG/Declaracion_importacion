"""
Escritor de Excel para datos consolidados.

Este módulo maneja la creación y actualización del archivo Excel consolidado
con las hojas Datos_Generales y Productos.
"""

import os
import pandas as pd
from typing import Optional
from pathlib import Path


class ExcelWriter:
    """Escritor de archivos Excel."""

    def __init__(self, output_file: str):
        """
        Inicializa el escritor de Excel.

        Args:
            output_file: Nombre del archivo Excel de salida
        """
        self.output_file = output_file

    def write_to_excel(self, general_data: pd.DataFrame, products_data: pd.DataFrame) -> None:
        """
        Escribe datos en el archivo Excel.

        Args:
            general_data: DataFrame con datos generales
            products_data: DataFrame con productos
        """
        # Verificar si el archivo ya existe
        file_exists = os.path.exists(self.output_file)

        # Inicializar variables
        combined_general = general_data if not general_data.empty else pd.DataFrame()
        combined_products = products_data if not products_data.empty else pd.DataFrame()

        if file_exists:
            # Si existe, leer datos existentes
            existing_general = self._read_existing_sheet('Datos_Generales')
            existing_products = self._read_existing_sheet('Productos')

            # Combinar con nuevos datos
            if not general_data.empty:
                if existing_general.empty:
                    combined_general = general_data
                else:
                    combined_general = pd.concat([existing_general, general_data], ignore_index=True)

            if not products_data.empty:
                if existing_products.empty:
                    combined_products = products_data
                else:
                    combined_products = pd.concat([existing_products, products_data], ignore_index=True)

        # Crear Excel writer
        with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
            # Escribir hoja de datos generales
            if not combined_general.empty:
                combined_general.to_excel(writer, sheet_name='Datos_Generales', index=False)
            else:
                # Crear hoja vacía con encabezados básicos
                empty_df = pd.DataFrame(columns=['Origen_Archivo', 'Informacion'])
                empty_df.to_excel(writer, sheet_name='Datos_Generales', index=False)

            # Escribir hoja de productos
            if not combined_products.empty:
                combined_products.to_excel(writer, sheet_name='Productos', index=False)
            else:
                # Crear hoja vacía con encabezados básicos
                empty_df = pd.DataFrame(columns=[
                    'Id_Producto', 'Origen_Archivo', 'PRODUCTO', 'MARCA', 'MODELO',
                    'REFERENCIA', 'SERIAL', 'USO_O_DESTINO',
                    'TIPO_DE_MOTOR_AL_QUE_ESTA_DESTINADO', 'PAIS_ORIGEN', 'CANT'
                ])
                empty_df.to_excel(writer, sheet_name='Productos', index=False)

    def _read_existing_sheet(self, sheet_name: str) -> pd.DataFrame:
        """
        Lee una hoja existente del archivo Excel.

        Args:
            sheet_name: Nombre de la hoja

        Returns:
            pd.DataFrame: DataFrame con datos existentes
        """
        try:
            if not os.path.exists(self.output_file):
                return pd.DataFrame()

            # Leer solo la hoja especificada
            df = pd.read_excel(self.output_file, sheet_name=sheet_name)

            # Si la hoja tiene solo una fila con "info" o está vacía, devolver DataFrame vacío
            if df.empty or (len(df) == 1 and df.iloc[0].str.contains('info|No data', case=False, na=False).any()):
                return pd.DataFrame()

            return df

        except Exception:
            # Si hay error leyendo, devolver DataFrame vacío
            return pd.DataFrame()

    def ensure_excel_structure(self) -> None:
        """
        Asegura que el archivo Excel tenga la estructura básica.
        """
        if os.path.exists(self.output_file):
            return

        # Crear archivo Excel básico con estructura
        with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
            # Hoja de datos generales
            general_columns = [
                'Origen_Archivo', 'NIT', 'NOMBRE_EMPRESA', 'DIRECCION',
                'TELEFONO', 'CIUDAD', 'PAIS', 'AGENCIA_ADUANAS',
                'CODIGO_AGENCIA', 'NIVEL_AGENCIA', 'DECLARANTE',
                'CEDULA_DECLARANTE', 'TIPO_DECLARACION', 'NUMERO_DECLARACION',
                'AÑO_DECLARACION', 'AEROPUERTO', 'VUELO', 'GUIA_AEREA',
                'FECHA_LLEGADA', 'PROVEEDOR', 'EMAIL_PROVEEDOR',
                'NUMERO_FACTURA', 'TRANSPORTISTA', 'VALOR_DECLARADO'
            ]

            general_df = pd.DataFrame(columns=general_columns)
            general_df.to_excel(writer, sheet_name='Datos_Generales', index=False)

            # Hoja de productos
            products_columns = [
                'Id_Producto', 'Origen_Archivo', 'PRODUCTO', 'MARCA', 'MODELO',
                'REFERENCIA', 'SERIAL', 'USO_O_DESTINO',
                'TIPO_DE_MOTOR_AL_QUE_ESTA_DESTINADO', 'PAIS_ORIGEN', 'CANT'
            ]

            products_df = pd.DataFrame(columns=products_columns)
            products_df.to_excel(writer, sheet_name='Productos', index=False)

    def append_to_excel(self, general_data: pd.DataFrame, products_data: pd.DataFrame) -> None:
        """
        Agrega datos a un archivo Excel existente.

        Args:
            general_data: DataFrame con datos generales
            products_data: DataFrame con productos
        """
        # Leer datos existentes
        existing_general = self._read_existing_sheet('Datos_Generales')
        existing_products = self._read_existing_sheet('Productos')

        # Combinar datos
        if not general_data.empty:
            if existing_general.empty:
                combined_general = general_data
            else:
                combined_general = pd.concat([existing_general, general_data], ignore_index=True)
        else:
            combined_general = existing_general

        if not products_data.empty:
            if existing_products.empty:
                combined_products = products_data
            else:
                combined_products = pd.concat([existing_products, products_data], ignore_index=True)
        else:
            combined_products = existing_products

        # Escribir datos combinados
        with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
            if not combined_general.empty:
                combined_general.to_excel(writer, sheet_name='Datos_Generales', index=False)
            else:
                pd.DataFrame({"info": ["No general data found"]}).to_excel(
                    writer, sheet_name='Datos_Generales', index=False)

            if not combined_products.empty:
                combined_products.to_excel(writer, sheet_name='Productos', index=False)
            else:
                pd.DataFrame({"info": ["No products found"]}).to_excel(
                    writer, sheet_name='Productos', index=False)

    def get_excel_info(self) -> dict:
        """
        Obtiene información sobre el archivo Excel.

        Returns:
            dict: Información del archivo
        """
        info = {
            'file_exists': os.path.exists(self.output_file),
            'file_size': 0,
            'general_rows': 0,
            'products_rows': 0
        }

        if info['file_exists']:
            info['file_size'] = os.path.getsize(self.output_file)

            try:
                general_df = self._read_existing_sheet('Datos_Generales')
                products_df = self._read_existing_sheet('Productos')

                info['general_rows'] = len(general_df) if not general_df.empty else 0
                info['products_rows'] = len(products_df) if not products_df.empty else 0

            except Exception:
                pass

        return info