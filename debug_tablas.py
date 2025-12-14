#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de depuracion para ver que tablas detecta pdfplumber
"""

import pdfplumber

pdf_path = r"c:\Users\asus\Documents\Declaracion-de-importacion_V_290\PDF_A_LEER\FA001108.PDF"

print("="*60)
print("DEPURACION: Tablas detectadas por pdfplumber")
print("="*60)

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"\n--- PAGINA {i+1} ---")
        
        tablas = page.extract_tables()
        print(f"Tablas encontradas: {len(tablas)}")
        
        for j, tabla in enumerate(tablas):
            print(f"\n  TABLA {j+1}:")
            print(f"  Filas: {len(tabla)}")
            print(f"  Columnas: {len(tabla[0]) if tabla else 0}")
            
            if tabla:
                print(f"\n  Encabezados (fila 1):")
                for idx, header in enumerate(tabla[0]):
                    print(f"    Col {idx}: '{header}'")
                
                print(f"\n  Primeras 3 filas de datos:")
                for row_idx, fila in enumerate(tabla[1:4], 1):
                    print(f"    Fila {row_idx}: {fila}")
