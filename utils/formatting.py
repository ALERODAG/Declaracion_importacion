import pandas as pd
import re

def convertir_numero(valor):
    """Función para convertir correctamente los números (Lógica robusta)."""
    if pd.isna(valor) or valor == "" or valor is None:
        return None
    
    s = str(valor).strip()
    # Dejar solo dígitos, puntos, comas y signo menos
    s = re.sub(r'[^\d.,-]', '', s)
    if not s: return None

    last_comma = s.rfind(',')
    last_point = s.rfind('.')

    try:
        # Caso A: No hay separadores -> Entero
        if last_comma == -1 and last_point == -1:
            return float(s)

        # Caso B: Punto está después de coma (o no hay coma) -> Formato 1,234.56
        # El punto es el decimal.
        if last_point > last_comma:
            # Eliminar todas las comas (separadores de miles)
            clean_s = s.replace(',', '')
            # Asegurar que solo hay un punto (el último)
            parts = clean_s.split('.')
            if len(parts) > 2:
                # Unir todo menos el último decimal
                integer_part = "".join(parts[:-1])
                decimal_part = parts[-1]
                clean_s = f"{integer_part}.{decimal_part}"
            
            return float(clean_s)
        
        # Caso C: Coma está después de punto (o no hay punto) -> Formato 1.234,56
        # La coma es el decimal.
        else: 
             # Eliminar todos los puntos (separadores de miles)
            clean_s = s.replace('.', '')
            # Reemplazar la coma decimal por punto para Python
            parts = clean_s.split(',')
            if len(parts) > 2:
                integer_part = "".join(parts[:-1])
                decimal_part = parts[-1]
                # Reemplazar ultima coma por punto
                clean_s = f"{integer_part}.{decimal_part}"
            else:
                clean_s = clean_s.replace(',', '.')
            
            return float(clean_s)

    except (ValueError, TypeError):
        return None

def formatear_numero(valor):
    """Función para formatear números para visualización (1,234.56)."""
    if pd.isna(valor) or valor is None:
        return ""
    try:
        num = float(valor)
        return f"{num:,.2f}" # 1,234.56
    except (ValueError, TypeError):
        return str(valor) if valor else ""
