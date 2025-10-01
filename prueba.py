import os
import re
import pandas as pd
import pdfplumber

path = r'D:\Declaracion-de-importacion_V_29'
excel_file = 'import_data.xlsx'

# Cargar o crear DataFrame para Products
try:
    products_df = pd.read_excel(excel_file, sheet_name='Products')
except FileNotFoundError:
    products_df = pd.DataFrame(columns=['Archivo', 'Declaracion numero', 'Producto', 'Marca', 'Modelo', 'Referencia', 'Serial', 'Uso o Destino', 'Tipo De Motor', 'Pais Origen', 'Cant'])
except ValueError:
    products_df = pd.DataFrame(columns=['Archivo', 'Declaracion numero', 'Producto', 'Marca', 'Modelo', 'Referencia', 'Serial', 'Uso o Destino', 'Tipo De Motor', 'Pais Origen', 'Cant'])

for filename in os.listdir(path):
    if filename.lower().endswith('.pdf'):
        full_path = os.path.join(path, filename)
        with pdfplumber.open(full_path) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text() + '\n'
        
        # Dividir en bloques por declaración
        blocks = re.split(r'(?=DECLARACION \d+ DE \d+)', text)
        
        for block in blocks:
            if not block.strip():
                continue
            
            # Extraer número de declaración
            decl_match = re.search(r'DECLARACION (\d+) DE \d+', block)
            if not decl_match:
                continue
            decl_num = decl_match.group(1)
            
            # Encontrar sección de productos (después de "DO LAC-... DECLARACION")
            products_section_match = re.search(r'DO\s+LAC-\d+-\d+\s+DECLARACION\(\d+-\d+\)\s+(.*)', block, re.DOTALL)
            if products_section_match:
                products_text = products_section_match.group(1)
                
                # Extraer productos individuales separados por //
                product_entries = re.findall(r'(NOMBRE TECNICO DEL PRODUCTO|PRODUCTO):\s*(.*?),\s*MARCA:\s*(.*?),\s*(MODELO:\s*(.*?),\s*)?REFERENCIA:\s*(.*?),\s*SERIAL:\s*(.*?),\s*USO O DESTINO:\s*(.*?)(,\s*TIPO DE MOTOR\s*(AL QUE ESTA DESTINADO)?:\s*(.*?))?,?\s*PAIS ORIGEN:\s*(.*?)\s*-\s*\d+\.\s*CANT\s*\((\d+)\)\s*UND', products_text, re.DOTALL | re.IGNORECASE)
                
                for entry in product_entries:
                    producto = entry[1].strip()
                    marca = entry[2].strip()
                    modelo = entry[4].strip() if entry[4] else 'NO TIENE'
                    referencia = entry[5].strip()
                    serial = entry[6].strip() if entry[6] else 'NO TIENE'
                    uso = entry[7].strip()
                    tipo_motor = entry[10].strip() if entry[10] else ''
                    pais = entry[11].strip()
                    cant = int(entry[12])
                    
                    new_row = {
                        'Archivo': filename,
                        'Declaracion numero': decl_num,
                        'Producto': producto,
                        'Marca': marca,
                        'Modelo': modelo,
                        'Referencia': referencia,
                        'Serial': serial,
                        'Uso o Destino': uso,
                        'Tipo De Motor': tipo_motor,
                        'Pais Origen': pais,
                        'Cant': cant
                    }
                    products_df = pd.concat([products_df, pd.DataFrame([new_row])], ignore_index=True)

# Guardar en Excel (hoja Products)
with pd.ExcelWriter(excel_file, mode='a', if_sheet_exists='replace', engine='openpyxl') as writer:
    products_df.to_excel(writer, sheet_name='Products', index=False)

print("Productos extraídos y guardados en import_data.xlsx (hoja Products).")