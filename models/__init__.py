"""
Modelos de datos para el sistema de procesamiento de declaraciones de importación.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class DeclaracionData:
    """Modelo para datos generales de una declaración."""

    # Información básica
    numero_declaracion: str = ""
    tipo_declaracion: str = ""
    codigo_declaracion: str = ""
    ano_declaracion: str = ""

    # Importador
    nit_importador: str = ""
    dv_importador: str = ""
    nombre_importador: str = ""
    direccion_importador: str = ""
    telefono_importador: str = ""
    codigo_direccion_importador: str = ""

    # Agencia aduanera
    nit_agencia: str = ""
    dv_agencia: str = ""
    nombre_agencia: str = ""
    nivel_agencia: str = ""
    codigo_agencia: str = ""

    # Declarante
    cedula_declarante: str = ""
    nombre_declarante: str = ""

    # Tipo de declaración
    codigo_tipo_declaracion: str = ""
    descripcion_tipo_declaracion: str = ""
    numero_tipo_declaracion: str = ""
    datos_adicionales_tipo: str = ""

    # Información de transporte
    codigo_aeropuerto: str = ""
    numero_aeropuerto: str = ""
    numero_guia_aerea: str = ""
    fecha_guia_aerea: str = ""
    numero_manifiesto: str = ""
    fecha_manifiesto: str = ""

    # Proveedor
    nombre_proveedor: str = ""
    ubicacion_proveedor: str = ""
    direccion_proveedor: str = ""
    email_proveedor: str = ""

    # Factura
    numero_factura: str = ""
    codigo_factura: str = ""

    # Transporte
    fecha_transporte: str = ""
    codigo_transporte_1: str = ""
    codigo_transporte_2: str = ""
    codigo_transporte_3: str = ""
    codigo_transporte_4: str = ""
    nombre_carrier: str = ""
    monto_transporte: str = ""

    # Producto
    codigo_arancelario: str = ""
    descripcion_producto: str = ""
    detalles_producto: str = ""

    # Datos financieros
    valor_cif: str = ""
    valor_arancel: str = ""
    sobretasa_valor: str = ""
    base_imponible: str = ""
    campo_fin_1_3: str = ""
    campo_fin_1_4: str = ""
    campo_fin_1_5: str = ""

    # Tasas e impuestos
    tasa_arancel: str = ""
    valor_arancel_calculado: str = ""
    tasa_sobretasa: str = ""
    valor_sobretasa: str = ""
    base_imponible_2: str = ""
    fob: str = ""
    iva: str = ""

    # Campos financieros adicionales
    campo_fin_3_1: str = ""
    campo_fin_3_2: str = ""
    campo_fin_3_3: str = ""
    campo_fin_3_4: str = ""
    campo_fin_3_5: str = ""

    # Totales
    total_arancel: str = ""
    total_sobretasa: str = ""
    campo_fin_5_1: str = ""
    campo_fin_5_2: str = ""
    campo_fin_5_3: str = ""
    campo_fin_5_4: str = ""
    campo_fin_5_5: str = ""

    # Campos financieros 6
    campo_fin_6_1: str = ""
    campo_fin_6_2: str = ""
    campo_fin_6_3: str = ""
    campo_fin_6_4: str = ""
    campo_fin_6_5: str = ""

    # Total liquidación
    total_liquidacion: str = ""
    campo_fin_7_2: str = ""
    campo_fin_7_3: str = ""

    # Campos financieros 8
    campo_fin_8_1: str = ""
    campo_fin_8_2: str = ""
    campo_fin_8_3: str = ""
    campo_fin_8_4: str = ""

    # Campos financieros 9
    campo_fin_9_1: str = ""
    campo_fin_9_2: str = ""
    campo_fin_9_3: str = ""
    campo_fin_9_4: str = ""

    # Metadatos
    declaracion_numero: str = ""
    fecha_procesamiento: Optional[datetime] = None

    def __post_init__(self):
        """Inicialización posterior para mapear campos del parser."""
        # Este método permite manejar la conversión de campos del parser
        # a los nombres de atributos del modelo
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto a diccionario."""
        return {
            'numero_declaracion': self.numero_declaracion,
            'tipo_declaracion': self.tipo_declaracion,
            'codigo_declaracion': self.codigo_declaracion,
            'ano_declaracion': self.ano_declaracion,
            'nit_importador': self.nit_importador,
            'dv_importador': self.dv_importador,
            'nombre_importador': self.nombre_importador,
            'direccion_importador': self.direccion_importador,
            'telefono_importador': self.telefono_importador,
            'codigo_direccion_importador': self.codigo_direccion_importador,
            'nit_agencia': self.nit_agencia,
            'dv_agencia': self.dv_agencia,
            'nombre_agencia': self.nombre_agencia,
            'nivel_agencia': self.nivel_agencia,
            'codigo_agencia': self.codigo_agencia,
            'cedula_declarante': self.cedula_declarante,
            'nombre_declarante': self.nombre_declarante,
            'codigo_tipo_declaracion': self.codigo_tipo_declaracion,
            'descripcion_tipo_declaracion': self.descripcion_tipo_declaracion,
            'numero_tipo_declaracion': self.numero_tipo_declaracion,
            'datos_adicionales_tipo': self.datos_adicionales_tipo,
            'codigo_aeropuerto': self.codigo_aeropuerto,
            'numero_aeropuerto': self.numero_aeropuerto,
            'numero_guia_aerea': self.numero_guia_aerea,
            'fecha_guia_aerea': self.fecha_guia_aerea,
            'numero_manifiesto': self.numero_manifiesto,
            'fecha_manifiesto': self.fecha_manifiesto,
            'nombre_proveedor': self.nombre_proveedor,
            'ubicacion_proveedor': self.ubicacion_proveedor,
            'direccion_proveedor': self.direccion_proveedor,
            'email_proveedor': self.email_proveedor,
            'numero_factura': self.numero_factura,
            'codigo_factura': self.codigo_factura,
            'fecha_transporte': self.fecha_transporte,
            'codigo_transporte_1': self.codigo_transporte_1,
            'codigo_transporte_2': self.codigo_transporte_2,
            'codigo_transporte_3': self.codigo_transporte_3,
            'codigo_transporte_4': self.codigo_transporte_4,
            'nombre_carrier': self.nombre_carrier,
            'monto_transporte': self.monto_transporte,
            'codigo_arancelario': self.codigo_arancelario,
            'descripcion_producto': self.descripcion_producto,
            'detalles_producto': self.detalles_producto,
            'valor_cif': self.valor_cif,
            'valor_arancel': self.valor_arancel,
            'sobretasa_valor': self.sobretasa_valor,
            'base_imponible': self.base_imponible,
            'campo_fin_1_3': self.campo_fin_1_3,
            'campo_fin_1_4': self.campo_fin_1_4,
            'campo_fin_1_5': self.campo_fin_1_5,
            'tasa_arancel': self.tasa_arancel,
            'valor_arancel_calculado': self.valor_arancel_calculado,
            'tasa_sobretasa': self.tasa_sobretasa,
            'valor_sobretasa': self.valor_sobretasa,
            'base_imponible_2': self.base_imponible_2,
            'fob': self.fob,
            'iva': self.iva,
            'campo_fin_3_1': self.campo_fin_3_1,
            'campo_fin_3_2': self.campo_fin_3_2,
            'campo_fin_3_3': self.campo_fin_3_3,
            'campo_fin_3_4': self.campo_fin_3_4,
            'campo_fin_3_5': self.campo_fin_3_5,
            'total_arancel': self.total_arancel,
            'total_sobretasa': self.total_sobretasa,
            'campo_fin_5_1': self.campo_fin_5_1,
            'campo_fin_5_2': self.campo_fin_5_2,
            'campo_fin_5_3': self.campo_fin_5_3,
            'campo_fin_5_4': self.campo_fin_5_4,
            'campo_fin_5_5': self.campo_fin_5_5,
            'campo_fin_6_1': self.campo_fin_6_1,
            'campo_fin_6_2': self.campo_fin_6_2,
            'campo_fin_6_3': self.campo_fin_6_3,
            'campo_fin_6_4': self.campo_fin_6_4,
            'campo_fin_6_5': self.campo_fin_6_5,
            'total_liquidacion': self.total_liquidacion,
            'campo_fin_7_2': self.campo_fin_7_2,
            'campo_fin_7_3': self.campo_fin_7_3,
            'campo_fin_8_1': self.campo_fin_8_1,
            'campo_fin_8_2': self.campo_fin_8_2,
            'campo_fin_8_3': self.campo_fin_8_3,
            'campo_fin_8_4': self.campo_fin_8_4,
            'campo_fin_9_1': self.campo_fin_9_1,
            'campo_fin_9_2': self.campo_fin_9_2,
            'campo_fin_9_3': self.campo_fin_9_3,
            'campo_fin_9_4': self.campo_fin_9_4,
            'declaracion_numero': self.declaracion_numero,
            'fecha_procesamiento': self.fecha_procesamiento.isoformat() if self.fecha_procesamiento else None
        }


@dataclass
class ProductoData:
    """Modelo para datos de productos."""

    declaracion_numero: str = ""
    producto: str = ""
    marca: str = ""
    modelo: str = ""
    referencia: str = ""
    codigo_referencia: str = ""
    serial: str = ""
    uso_destino: str = ""
    pais_origen: str = ""
    codigo_pais: str = ""
    cantidad: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto a diccionario."""
        return {
            'declaracion_numero': self.declaracion_numero,
            'producto': self.producto,
            'marca': self.marca,
            'modelo': self.modelo,
            'referencia': self.referencia,
            'codigo_referencia': self.codigo_referencia,
            'serial': self.serial,
            'uso_destino': self.uso_destino,
            'pais_origen': self.pais_origen,
            'codigo_pais': self.codigo_pais,
            'cantidad': self.cantidad
        }


@dataclass
class ProcessingResult:
    """Resultado del procesamiento de un archivo."""

    archivo_procesado: str = ""
    declaraciones_encontradas: int = 0
    productos_extraidos: int = 0
    errores: List[str] = field(default_factory=list)
    fecha_procesamiento: Optional[datetime] = None

    def __post_init__(self):
        """Inicialización posterior."""
        if self.fecha_procesamiento is None:
            self.fecha_procesamiento = datetime.now()