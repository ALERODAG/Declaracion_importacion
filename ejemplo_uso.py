#!/usr/bin/env python3
"""
Ejemplo de uso del sistema refactorizado de procesamiento de declaraciones.

Este archivo muestra cómo usar la nueva arquitectura modular comparada
con el código original monolítico.
"""

import logging
from main import DeclaracionProcessor
from config import Config


def ejemplo_uso_basico():
    """Ejemplo de uso básico del sistema."""
    print("=== EJEMPLO DE USO BÁSICO ===")

    # Crear procesador con configuración por defecto
    processor = DeclaracionProcessor()

    # Procesar archivo PDF
    pdf_file = "DIM YADAS NSK PARA OK[1].pdf"
    output_file = "declaracion_procesada.xlsx"

    print(f"Procesando archivo: {pdf_file}")
    print(f"Archivo de salida: {output_file}")

    # Procesar el archivo
    result = processor.process_pdf_file(pdf_file, output_file)

    # Mostrar resultados
    print("\nResultados:")
    print(f"  - Declaraciones encontradas: {result.declaraciones_encontradas}")
    print(f"  - Productos extraídos: {result.productos_extraidos}")
    print(f"  - Errores: {len(result.errores)}")

    if result.errores:
        print("  Errores encontrados:")
        for error in result.errores:
            print(f"    - {error}")


def ejemplo_configuracion_personalizada():
    """Ejemplo con configuración personalizada."""
    print("\n=== EJEMPLO CON CONFIGURACIÓN PERSONALIZADA ===")

    # Crear configuración personalizada
    config = Config(
        log_level="DEBUG",
        max_financial_lines=15,
        export_formats=['excel', 'json']
    )

    # Crear procesador con configuración
    processor = DeclaracionProcessor(config)

    print("Configuración personalizada:")
    print(f"  - Nivel de log: {config.log_level}")
    print(f"  - Líneas financieras máximas: {config.max_financial_lines}")
    print(f"  - Formatos de exportación: {config.export_formats}")

    # Procesar con configuración personalizada
    result = processor.process_pdf_file(
        "DIM YADAS NSK PARA OK[1].pdf",
        "declaracion_configurada.xlsx"
    )

    print(f"Procesamiento completado: {result.declaraciones_encontradas} declaraciones")


def ejemplo_uso_modular():
    """Ejemplo mostrando el uso modular de componentes."""
    print("\n=== EJEMPLO DE USO MODULAR ===")

    from parsers import DeclaracionParserFactory
    from extractors import ProductExtractorFactory
    from models import DeclaracionData, ProductoData

    # Crear componentes individuales
    parser = DeclaracionParserFactory.create_parser()
    extractor = ProductExtractorFactory.create_extractor()

    # Texto de ejemplo
    texto_ejemplo = """
DECLARACION 1 DE 4 DO /IMP LAC-1331-25
2 0 2 5
900428482 1 YADAS WT IMPORTACIONES S.A.S.
PRODUCTO: RODAMIENTOS DE BOLA, MARCA: NSK, MODELO: NO TIENE, REFERENCIA: BD25-9T12C3, SERIAL: NO TIENE, USO O DESTINO: PARA VEHICULOS, PAIS ORIGEN: JAPON - 399. CANT (6) UND
"""

    print("Usando componentes modulares:")

    # Parsear declaración
    fields = parser.parse_text(texto_ejemplo)
    print(f"  - NIT Importador: {fields.get('4_nit_importador', 'No encontrado')}")
    print(f"  - Nombre Importador: {fields.get('5_nombre_importador', 'No encontrado')}")

    # Extraer productos
    productos = extractor.extract_products(texto_ejemplo, "1")
    print(f"  - Productos encontrados: {len(productos)}")

    if productos:
        producto = productos[0]
        print(f"  - Primer producto: {producto.producto}")
        print(f"  - Marca: {producto.marca}")
        print(f"  - Cantidad: {producto.cantidad}")


def ejemplo_validaciones():
    """Ejemplo de validaciones de datos."""
    print("\n=== EJEMPLO DE VALIDACIONES ===")

    from utils import DataValidator

    # Validar NIT
    nits = ["900428482", "830049499", "123", "abc"]
    print("Validación de NITs:")
    for nit in nits:
        es_valido = DataValidator.is_valid_nit(nit)
        print(f"  - {nit}: {'Válido' if es_valido else 'Inválido'}")

    # Validar emails
    emails = ["test@empresa.com", "invalid-email", "test@"]
    print("\nValidación de emails:")
    for email in emails:
        es_valido = DataValidator.is_valid_email(email)
        print(f"  - {email}: {'Válido' if es_valido else 'Inválido'}")


def comparar_con_codigo_original():
    """Comparación con el código original."""
    print("\n=== COMPARACIÓN CON CÓDIGO ORIGINAL ===")

    print("CÓDIGO ORIGINAL:")
    print("  ❌ Un solo archivo de 1000+ líneas")
    print("  ❌ Función extract_products_from_declaration de 800+ líneas")
    print("  ❌ Código duplicado en múltiples lugares")
    print("  ❌ Configuración hardcodeada")
    print("  ❌ Sin separación de responsabilidades")
    print("  ❌ Sin tests unitarios")
    print("  ❌ Manejo de errores limitado")
    print("  ❌ Sin documentación estructurada")

    print("\nNUEVO SISTEMA REFACTORIZADO:")
    print("  ✅ Módulos separados por responsabilidades")
    print("  ✅ Función extract_products dividida en 21 métodos")
    print("  ✅ Código reutilizable y mantenible")
    print("  ✅ Configuración flexible")
    print("  ✅ Arquitectura orientada a objetos")
    print("  ✅ Tests unitarios completos")
    print("  ✅ Manejo robusto de errores")
    print("  ✅ Documentación completa")

    print("\nBENEFICIOS:")
    print("  📈 Mantenibilidad mejorada")
    print("  🧪 Testeabilidad completa")
    print("  🔧 Extensibilidad fácil")
    print("  📚 Legibilidad mejorada")
    print("  🐛 Debugging más sencillo")
    print("  🚀 Escalabilidad futura")


def main():
    """Función principal con todos los ejemplos."""
    # Configurar logging
    logging.basicConfig(level=logging.INFO)

    print("SISTEMA DE PROCESAMIENTO DE DECLARACIONES")
    print("=" * 50)

    # Ejecutar ejemplos
    ejemplo_uso_basico()
    ejemplo_configuracion_personalizada()
    ejemplo_uso_modular()
    ejemplo_validaciones()
    comparar_con_codigo_original()

    print("\n" + "=" * 50)
    print("¡Refactorización completada exitosamente!")
    print("El código ahora cumple con las mejores prácticas de desarrollo de software.")


if __name__ == "__main__":
    main()