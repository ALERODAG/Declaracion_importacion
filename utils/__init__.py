"""
Módulo de utilidades para el sistema de procesamiento de declaraciones.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path


class TextProcessor:
    """Utilidades para procesamiento de texto."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Limpia y normaliza el texto."""
        if not text:
            return ""

        # Eliminar caracteres especiales y normalizar
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)  # Normalizar espacios
        return text

    @staticmethod
    def split_preserving_quotes(text: str, delimiter: str = ',') -> List[str]:
        """Divide texto preservando comillas."""
        # Patrón simple para dividir por delimitador respetando comillas
        pattern = f'{delimiter}(?=(?:[^"]*"[^"]*")*[^"]*$)'
        return [part.strip().strip('"') for part in re.split(pattern, text)]

    @staticmethod
    def extract_email(text: str) -> Optional[str]:
        """Extrae email de un texto."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None

    @staticmethod
    def extract_phone(text: str) -> Optional[str]:
        """Extrae número de teléfono de un texto."""
        phone_pattern = r'\b\d{7,10}\b'
        match = re.search(phone_pattern, text)
        return match.group(0) if match else None


class FileManager:
    """Utilidades para manejo de archivos."""

    @staticmethod
    def ensure_directory(path: str) -> None:
        """Asegura que un directorio exista."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Obtiene la extensión de un archivo."""
        return Path(file_path).suffix.lower()

    @staticmethod
    def is_pdf_file(file_path: str) -> bool:
        """Verifica si es un archivo PDF."""
        return FileManager.get_file_extension(file_path) == '.pdf'

    @staticmethod
    def is_text_file(file_path: str) -> bool:
        """Verifica si es un archivo de texto."""
        return FileManager.get_file_extension(file_path) in ['.txt', '.text']


class DataValidator:
    """Utilidades para validación de datos."""

    @staticmethod
    def is_valid_nit(nit: str) -> bool:
        """Valida un NIT colombiano."""
        if not nit or not nit.isdigit():
            return False
        return len(nit) >= 8 and len(nit) <= 10

    @staticmethod
    def is_valid_date(date_str: str, date_format: str = "%Y-%m-%d") -> bool:
        """Valida formato de fecha."""
        try:
            from datetime import datetime
            datetime.strptime(date_str, date_format)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Valida formato de email."""
        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        return bool(re.match(email_pattern, email))

    @staticmethod
    def sanitize_string(text: str) -> str:
        """Sanitiza una cadena de texto."""
        if not text:
            return ""
        return text.strip().replace('\n', ' ').replace('\r', '')


class LoggerMixin:
    """Mixin para agregar logging a clases."""

    @property
    def logger(self):
        """Obtiene el logger para la clase."""
        return logging.getLogger(self.__class__.__name__)


class RegexPatterns:
    """Patrones regex reutilizables."""

    # Patrones para productos
    PRODUCTO_BASE = r'(?:NOMBRE TECNICO DEL )?PRODUCTO:\s*([^,]+),\s*MARCA:\s*([^,]+),\s*MODELO:\s*([^,]+),\s*REFERENCIA:\s*([^,]+)(?:[^,]*),\s*SERIAL:\s*([^,]+),\s*USO O DESTINO:\s*([^,]+),\s*PAIS ORIGEN:\s*([^-]+)\s*-\s*(\d+)\.\s*CANT\s*\((\d+)\)\s*UND'

    # Patrones para declaración
    DECLARACION_LINE = r'DECLARACION (\d+) DE \d+ DO /IMP LAC-\d+-\d+'

    # Patrones para NIT
    NIT_PATTERN = r'(\d{8,10})'

    # Patrones para fechas
    DATE_PATTERN = r'(\d{4})-(\d{2})-(\d{2})'

    # Patrón para email
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # Patrón para teléfono
    PHONE_PATTERN = r'\b\d{7,10}\b'


class DataFormatter:
    """Utilidades para formateo de datos."""

    @staticmethod
    def format_currency(value: str) -> str:
        """Formatea un valor como moneda."""
        if not value:
            return "0.00"
        try:
            # Eliminar puntos y comas, luego formatear
            cleaned = value.replace('.', '').replace(',', '.')
            return f"{float(cleaned):.2f}"
        except (ValueError, AttributeError):
            return value

    @staticmethod
    def format_date(date_str: str) -> str:
        """Formatea una fecha."""
        if not date_str:
            return ""

        # Si ya está en formato YYYY-MM-DD, devolver tal cual
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            return date_str

        # Si está en formato DD-MM-YYYY, convertir
        if re.match(r'\d{2}-\d{2}-\d{4}', date_str):
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                pass

        return date_str

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normaliza texto eliminando caracteres especiales."""
        if not text:
            return ""

        # Convertir a mayúsculas y eliminar caracteres especiales
        normalized = text.upper()
        normalized = re.sub(r'[^\w\s\-.,]', '', normalized)
        return normalized.strip()