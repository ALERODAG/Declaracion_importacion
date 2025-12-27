from factura_universal import procesar_factura_universal
from facturas_gate import procesar_factura_gate
from factura_sofabex import procesar_factura_sofabex
from factuta_adk import procesar_factura_adk

def procesar_factura(pdf_path):
    """
    Procesa una factura intentando diferentes parsers en orden.
    
    1. Parser universal (inteligente) - funciona con cualquier formato
    2. Parsers específicos por proveedor (fallback)
    
    Args:
        pdf_path: Ruta al archivo PDF
        
    Returns:
        DataFrame con productos o None si ningún parser funciona
    """
    for parser in [
        procesar_factura_gate,       # ESPECÍFICO
        procesar_factura_sofabex,    # ESPECÍFICO
        procesar_factura_adk,        # ESPECÍFICO
        procesar_factura_universal,  # GENÉRICO (Fallback)
    ]:
        try:
            df = parser(pdf_path)
            if df is not None and not df.empty:
                return df
        except Exception as e:
            # Continuar con el siguiente parser si este falla
            print(f"Parser {parser.__name__} falló: {e}")
            continue

    return None  # Ningún parser aplicó
