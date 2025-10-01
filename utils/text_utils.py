"""
Utilidades para procesamiento de texto.

Este módulo proporciona funciones para limpiar, normalizar y procesar
texto extraído de PDFs de declaraciones de importación.
"""

import re
from typing import List, Optional


class TextUtils:
    """Utilidades para procesamiento de texto."""

    def __init__(self):
        """Inicializa las utilidades de texto."""
        pass

    def clean_text(self, text: str) -> str:
        """
        Limpia y normaliza el texto.

        Args:
            text: Texto a limpiar

        Returns:
            str: Texto limpio y normalizado
        """
        if not text:
            return ""

        # Unir palabras separadas por guion al final de línea
        text = self._join_hyphenated_words(text)

        # Normalizar espacios múltiples
        text = re.sub(r'\s+', ' ', text)

        # Eliminar caracteres especiales problemáticos
        text = text.replace('\x00', '')  # Caracteres nulos

        return text.strip()

    def _join_hyphenated_words(self, text: str) -> str:
        """
        Une palabras que están separadas por guion al final de línea.

        Args:
            text: Texto con posibles separaciones

        Returns:
            str: Texto con palabras unidas
        """
        # Patrón para encontrar guion seguido de salto de línea
        pattern = r'-\s*\n\s*'
        return re.sub(pattern, '', text, flags=re.MULTILINE)

    def extract_between_markers(self, text: str, start_marker: str, end_marker: str) -> str:
        """
        Extrae texto entre dos marcadores.

        Args:
            text: Texto completo
            start_marker: Marcador de inicio
            end_marker: Marcador de fin

        Returns:
            str: Texto entre los marcadores
        """
        start_idx = text.find(start_marker)
        if start_idx == -1:
            return ""

        end_idx = text.find(end_marker, start_idx + len(start_marker))
        if end_idx == -1:
            return ""

        return text[start_idx + len(start_marker):end_idx]

    def find_first_occurrence(self, text: str, marker: str) -> int:
        """
        Encuentra la primera ocurrencia de un marcador.

        Args:
            text: Texto a buscar
            marker: Marcador a encontrar

        Returns:
            int: Posición de la primera ocurrencia, -1 si no se encuentra
        """
        return text.find(marker)

    def split_into_lines(self, text: str) -> List[str]:
        """
        Divide texto en líneas.

        Args:
            text: Texto a dividir

        Returns:
            List[str]: Lista de líneas
        """
        return text.split('\n')

    def is_line_only_zeros(self, line: str) -> bool:
        """
        Verifica si una línea contiene solo ceros.

        Args:
            line: Línea a verificar

        Returns:
            bool: True si la línea contiene solo ceros
        """
        return line.strip() == '0' * len(line.strip())

    def is_line_only_x(self, line: str) -> bool:
        """
        Verifica si una línea contiene solo letras X/x.

        Args:
            line: Línea a verificar

        Returns:
            bool: True si la línea contiene solo X/x
        """
        stripped = line.strip()
        return stripped == 'X' * len(stripped) or stripped == 'x' * len(stripped)

    def normalize_date(self, date_str: str) -> str:
        """
        Normaliza una fecha al formato ISO (YYYY-MM-DD).

        Args:
            date_str: Fecha en formato original

        Returns:
            str: Fecha en formato ISO o cadena original si no se puede convertir
        """
        if not date_str:
            return ""

        # Si ya está en formato ISO, devolver tal cual
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str

        # Intentar convertir formato DD-MM-YYYY
        if re.match(r'^\d{2}-\d{2}-\d{4}$', date_str):
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # Intentar convertir formato YYYY-MM-DD (con puntos o barras)
        if re.match(r'^\d{4}[./]\d{2}[./]\d{2}$', date_str):
            try:
                from datetime import datetime
                # Primero intentar YYYY.MM.DD
                try:
                    date_obj = datetime.strptime(date_str, "%Y.%m.%d")
                    return date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    # Luego intentar YYYY/MM/DD
                    date_obj = datetime.strptime(date_str, "%Y/%m/%d")
                    return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                pass

        return date_str

    def normalize_number(self, number_str: str) -> str:
        """
        Normaliza un número eliminando separadores de miles.

        Args:
            number_str: Número con posibles separadores

        Returns:
            str: Número sin separadores de miles
        """
        if not number_str:
            return ""

        # Eliminar puntos y comas que no sean decimales
        # Primero eliminar puntos que sean separadores de miles
        normalized = re.sub(r'\.(?=\d{3})', '', number_str)

        # Luego eliminar comas que sean separadores de miles
        normalized = re.sub(r',(?=\d{3})', '', normalized)

        return normalized

    def extract_key_value_pairs(self, text: str, separator: str = ',') -> List[tuple]:
        """
        Extrae pares clave:valor de un texto.

        Args:
            text: Texto con pares clave:valor
            separator: Separador entre pares

        Returns:
            List[tuple]: Lista de tuplas (clave, valor)
        """
        pairs = []
        parts = [part.strip() for part in text.split(separator)]

        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                pairs.append((key.strip(), value.strip()))

        return pairs

    def find_continuation_markers(self, text: str) -> List[int]:
        """
        Encuentra posiciones de marcadores de continuación.

        Args:
            text: Texto a buscar

        Returns:
            List[int]: Lista de posiciones de marcadores
        """
        markers = [
            "<-- CONTINUA .....-->",
            "<< DO/IMP",
            ">>"
        ]

        positions = []
        for marker in markers:
            pos = 0
            while True:
                idx = text.find(marker, pos)
                if idx == -1:
                    break
                positions.append(idx)
                pos = idx + 1

        return sorted(positions)

    def extract_products_section(self, text: str) -> str:
        """
        Extrae la sección de productos del texto.

        Args:
            text: Texto completo

        Returns:
            str: Sección de productos
        """
        # Encontrar primera ocurrencia de PRODUCTO
        producto_start = text.find("PRODUCTO")
        if producto_start == -1:
            producto_start = text.find("NOMBRE TECNICO DEL PRODUCTO")

        if producto_start == -1:
            return ""

        # Encontrar primera ocurrencia de <-- CONTINUA
        continua_pos = text.find("<-- CONTINUA .....-->", producto_start)

        if continua_pos == -1:
            # Si no hay marcador de continuación, tomar todo desde PRODUCTO
            return text[producto_start:]
        else:
            # Tomar desde PRODUCTO hasta antes del marcador de continuación
            return text[producto_start:continua_pos]

    def extract_continuation_products(self, text: str) -> List[str]:
        """
        Extrae productos de las secciones de continuación.

        Args:
            text: Texto completo

        Returns:
            List[str]: Lista de bloques de productos de continuación
        """
        products = []

        # Encontrar todas las ocurrencias de << DO/IMP
        pattern = r'<< DO/IMP[^>]+>>'
        matches = re.finditer(pattern, text)

        for match in matches:
            start_pos = match.end()
            # Buscar siguiente línea que contenga solo X's
            remaining_text = text[start_pos:]

            lines = remaining_text.split('\n')
            block_lines = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Si encontramos línea con solo X's, terminar bloque
                if re.match(r'^X+$', line) or re.match(r'^x+$', line):
                    break

                # Si es línea con solo ceros, ignorar
                if self.is_line_only_zeros(line):
                    continue

                block_lines.append(line)

            if block_lines:
                products.append('\n'.join(block_lines))

        return products