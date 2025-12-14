# Sistema de Comparación de Archivos Excel (Declaración vs Factura)

Un sistema para comparar archivos Excel de declaraciones de importación y facturas, identificando coincidencias parciales en referencias, comparando cantidades y generando reportes detallados con interfaz gráfica.

## Características Principales

- **Comparación Inteligente**: Busca coincidencias parciales entre referencias de productos
- **Interfaz Gráfica**: Selección visual de columnas equivalentes entre archivos
- **Manejo de Cantidades**: Comparación precisa de cantidades con diferencias calculadas
- **Soporte para Marcas**: Filtro opcional por marca para mayor precisión
- **Exportación Automática**: Resultados exportados a Excel con todos los campos originales
- **Barra de Progreso**: Indicador visual del progreso de comparación
- **Manejo de Errores**: Validación robusta de archivos y datos

## Estructura del Proyecto

```
├── archivo_principal.py     # Script principal con interfaz gráfica completa
├── comparacion.py          # Versión simplificada sin barra de progreso
├── archivo_principal.spec  # Configuración para cx_Freeze
├── setup.py               # Script de construcción del ejecutable
├── requirements.txt        # Dependencias del proyecto
├── README.md              # Documentación del proyecto
├── config/                # Módulo de configuración
├── models/                # Modelos de datos (dataclasses)
├── scraper/               # Módulo de scraping web
├── utils/                 # Utilidades y funciones auxiliares
├── writers/               # Módulos de escritura/exportación
└── output/                # Directorio de salida para resultados
```

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/ALERODAG/Declaracion_importacion.git
cd Declaracion_importacion
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso Básico

# Activar el entorno
# En Windows (PowerShell)
.\declaracion_importacion\Scripts\Activate.ps1

# O crear un nuevo entorno virtual si es necesario:
# python -m venv venv
# .\venv\Scripts\Activate.ps1

# EJECUTAR EL SCRIPT
streamlit run streamlit.py

### Comparación con Interfaz Gráfica (Recomendado)

Ejecuta el script principal para una experiencia completa:

```bash
streamlit run streamlit.py
```

O para la versión simplificada:

```bash
python comparacion.py
```

### Funcionalidades

- **Selección Automática de Archivos**: Detecta automáticamente archivos Excel en el directorio configurado
- **Interfaz de Selección de Columnas**: Permite mapear columnas equivalentes entre declaración y factura
- **Comparación Inteligente**: Busca coincidencias parciales en referencias
- **Filtros Opcionales**: Soporte para filtrar por marca cuando está disponible
- **Resultados Detallados**: Exporta todas las coincidencias, diferencias y registros únicos

### Configuración

El sistema busca archivos Excel en el directorio:
```
./PDF_A_LEER/EXCEL_PDF_LEIDOS
```

Los resultados se guardan automáticamente en `resultado_comparacion.xlsx` en el mismo directorio.

## Algoritmo de Comparación

El sistema implementa un algoritmo inteligente para comparar archivos Excel:

1. **Detección Automática**: Identifica archivos de declaración y factura por nombre
2. **Selección de Columnas**: Interfaz gráfica para mapear columnas equivalentes
3. **Limpieza de Datos**: Normalización de tipos de datos y manejo de valores nulos
4. **Comparación por Referencia**: Búsqueda de coincidencias parciales usando expresiones regulares
5. **Filtrado por Marca**: Filtro opcional adicional cuando las columnas de marca están disponibles
6. **Cálculo de Diferencias**: Comparación numérica de cantidades
7. **Clasificación de Resultados**:
   - **Coincide**: Referencia y cantidad exactas
   - **Cantidad diferente**: Referencia coincide pero cantidad varía
   - **Solo en Declaración**: Registro único en archivo de declaración
   - **Solo en Factura**: Registro único en archivo de factura

## Formato de Salida

El archivo de resultados `resultado_comparacion.xlsx` contiene:

- Todas las columnas originales de ambos archivos (sufijadas con _DECLARACION y _FACTURA)
- Columna `DIFERENCIA_CANTIDAD`: Diferencia numérica entre cantidades
- Columna `RESULTADO`: Clasificación del tipo de coincidencia

## Scripts Disponibles

### archivo_principal.py
Script principal con interfaz gráfica completa que incluye:
- Selección visual de columnas
- Barra de progreso durante la comparación
- Manejo completo de errores
- Exportación automática de resultados

### comparacion.py
Versión simplificada sin interfaz de progreso, ideal para:
- Ejecución por lotes
- Integración en otros sistemas
- Procesamiento automatizado

### Otros Scripts
- `ejemplo_uso.py`: Ejemplos de uso básico
- `main_simple.py`: Versión minimalista
- Scripts específicos en subdirectorios para funcionalidades adicionales

## Requisitos del Sistema

- **Python**: 3.8 o superior
- **Dependencias**: Ver requirements.txt
- **Archivos de entrada**: Archivos Excel (.xlsx, .xls) en el directorio configurado
- **Espacio de salida**: Escritura en el directorio de entrada

## Construcción de Ejecutable

Este repositorio contiene instrucciones para crear un ejecutable independiente. Hay dos enfoques comunes:

- cx_Freeze: existe una configuración histórica en el repositorio (si prefieres `cx_Freeze` puedes usar el `setup.py` antiguo). Ejemplo:

```powershell
# Con cx_Freeze (si tienes setup.py preparado)
python setup.py build
```

- PyInstaller (recomendado para crear un único archivo ejecutable que puedas llevar a otras máquinas). He añadido un helper PowerShell `build_exe.ps1` en la raíz del proyecto para simplificar el proceso.

Ejemplo (PowerShell, desde la raíz del proyecto):

```powershell
# Construye un exe en modo "onefile" para main_simple.py
.\build_exe.ps1 -Script main_simple.py -OneFile

# Construye el lanzador GUI sin consola visible
.\build_exe.ps1 -Script ejecutar.py -OneFile -NoConsole
```

Después del build revisa la carpeta `dist/` para el ejecutable. El script intenta incluir carpetas comunes (`config`, `models`, `utils`, `writers`, `scraper`) y los archivos `README.md` y `requirements.txt` si están presentes.

Nota sobre la ubicación del lanzador:

Si el archivo `ejecutar.py` fue movido a la carpeta `ejecutable` (por ejemplo `ejecutable\ejecutar.py`), el repositorio incluye un helper dentro de esa carpeta. Puedes invocar directamente el helper con:

```powershell
.\ejecutable\build_exe.ps1 -Script ejecutar.py -OneFile -NoConsole
```

O bien, para mantener compatibilidad con el uso desde la raíz, hay un wrapper `build_exe.ps1` en la raíz que reenviará los argumentos al helper dentro de `ejecutable`.

Consejos:

- Si tu aplicación usa dependencias grandes (por ejemplo `torch`, `easyocr`, `opencv`), el ejecutable resultante será grande; valora excluirlas si no las necesitas en la máquina destino.
- Si encuentras errores por 'hidden imports', añade `--hidden-import nombre_modulo` a la llamada de PyInstaller o edita `build_exe.ps1` para añadirlos.
- Si prefieres una distribución en carpeta en vez de un solo archivo (menos propensa a detecciones de antivirus), no uses `-OneFile`.

## Manejo de Errores

El sistema incluye validaciones robustas:

- Verificación de existencia de archivos Excel
- Validación de selección de columnas requeridas
- Manejo de tipos de datos mixtos
- Recuperación de errores en conversión numérica
- Mensajes de error descriptivos en interfaz gráfica

## Contribución

1. Fork el proyecto
2. Crear rama para nueva funcionalidad
3. Probar cambios con archivos de ejemplo
4. Implementar la funcionalidad
5. Actualizar documentación si es necesario
6. Crear Pull Request

## Licencia


## Soporte

Para soporte técnico o preguntas:

- Crear un issue en GitHub
- Revisar la documentación
- Probar con archivos de ejemplo

## Roadmap

### Mejoras Planificadas
- [ ] Soporte para múltiples pares de archivos simultáneamente
- [ ] Configuración personalizable del directorio de trabajo
- [ ] Filtros adicionales (fecha, valor, etc.)
- [ ] Interfaz web para carga de archivos
- [ ] API para integración con otros sistemas
- [ ] Exportación a formatos adicionales (CSV, JSON)
- [ ] Análisis estadístico de resultados

## Módulo de Scraping Web

Este repositorio incluye un módulo de scraping web con paginación robusta incluido en el directorio `scraper/`. Este módulo es independiente del comparador de Excel y ofrece funcionalidades avanzadas de extracción web.

Características del scraper:
- Paginación automática por parámetros URL o enlaces "Siguiente"
- Deduplicación inteligente de productos
- Reintentos con backoff exponencial
- Exportación idempotente a Excel
- Logs detallados y resúmenes JSON

Para más información sobre el scraper, consulte la documentación específica en el directorio `scraper/`.
