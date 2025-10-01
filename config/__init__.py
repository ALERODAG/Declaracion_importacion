"""
Módulo de configuración para el sistema de procesamiento de declaraciones de importación.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Config:
    """Clase de configuración principal."""

    # Configuración de archivos
    working_directory: str = None
    pdf_file: str = None
    output_excel: str = None

    # Configuración de logging
    log_level: str = "INFO"
    log_format: str = '%(asctime)s - %(levelname)s - %(message)s'

    # Configuración de procesamiento
    max_financial_lines: int = 10
    text_extraction_method: str = "pdfplumber"

    # Configuración de exportación
    export_formats: list = None

    def __post_init__(self):
        """Inicialización posterior para valores por defecto."""
        if self.working_directory is None:
            self.working_directory = os.getcwd()

        if self.export_formats is None:
            self.export_formats = ['excel', 'json']


class ConfigManager:
    """Gestor de configuración."""

    def __init__(self):
        """Inicializa el gestor de configuración."""
        self.config = Config()

    def load_from_env(self) -> 'ConfigManager':
        """Carga configuración desde variables de entorno."""
        # Aquí se pueden cargar configuraciones desde .env o variables de entorno
        return self

    def load_from_file(self, config_file: str) -> 'ConfigManager':
        """Carga configuración desde archivo."""
        if os.path.exists(config_file):
            # Aquí se puede implementar carga desde YAML, JSON, etc.
            pass
        return self

    def get_config(self) -> Config:
        """Obtiene la configuración actual."""
        return self.config


# Instancia global de configuración
config_manager = ConfigManager()