#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para el parser universal de facturas
"""

import sys
sys.path.insert(0, r"c:\Users\asus\Documents\Declaracion-de-importacion_V_290")

from factura_universal import procesar_factura_universal
import pandas as pd

# Ruta al PDF de prueba
pdf_path = r"c:\Users\asus\Documents\Declaracion-de-importacion_V_290\PDF_A_LEER\FA001108.PDF"

print("="*60)
print("PRUEBA: Parser Universal de Facturas")
print("="*60)
print(f"\nProcesando: {pdf_path}")
print("-"*60)

# Procesar factura
df = procesar_factura_universal(pdf_path)

if df is not None and not df.empty:
    print("\n[OK] EXITO: Factura procesada correctamente")
    print(f"\nFilas extraidas: {len(df)}")
    print(f"\nColumnas detectadas: {list(df.columns)}")
    print("\n" + "="*60)
    print("DATOS EXTRAIDOS:")
    print("="*60)
    print(df.to_string())
    print("\n" + "="*60)
    
    # Guardar a Excel para verificar
    output_path = r"c:\Users\asus\Documents\Declaracion-de-importacion_V_290\test_universal_parser.xlsx"
    df.to_excel(output_path, index=False)
    print(f"\n[OK] Excel guardado en: {output_path}")
else:
    print("\n[ERROR] No se pudo extraer informacion de la factura")
