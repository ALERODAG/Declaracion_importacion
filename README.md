# Sistema de Procesamiento de Declaraciones de Importación

Un sistema modular y orientado a objetos para procesar declaraciones de importación desde archivos PDF, extrayendo datos generales y productos de manera estructurada.

## Características Principales

- **Arquitectura Modular**: Código organizado en módulos separados por responsabilidades
- **Orientado a Objetos**: Diseño basado en clases y principios SOLID
- **Extracción Robusta**: Múltiples métodos para extraer productos de diferentes formatos
- **Configurable**: Sistema de configuración flexible
- **Testeable**: Suite de tests unitarios incluida
- **Manejo de Errores**: Logging y manejo de errores robusto
- **Exportación Múltiple**: Soporte para Excel y JSON

## Estructura del Proyecto

```
├── config/                 # Módulo de configuración
├── models/                 # Modelos de datos (dataclasses)
├── parsers/                # Lógica de parsing de declaraciones
├── extractors/             # Lógica de extracción de productos
├── utils/                  # Utilidades y funciones auxiliares
├── tests/                  # Tests unitarios
├── main.py                 # Punto de entrada principal
└── requirements.txt        # Dependencias del proyecto
```

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd declaracion-de-importacion
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso Básico

### Procesamiento Simple

```python
from main import DeclaracionProcessor

# Crear procesador
processor = DeclaracionProcessor()

# Procesar archivo PDF
result = processor.process_pdf_file("archivo.pdf", "salida.xlsx")

print(f"Declaraciones procesadas: {result.declaraciones_encontradas}")
print(f"Productos extraídos: {result.productos_extraidos}")
```

### Procesamiento Múltiple

```python
# Procesar múltiples archivos
results = processor.process_multiple_pdfs("*.pdf", "salida.xlsx")

for result in results:
    print(f"Archivo: {result.archivo_procesado}")
    print(f"  Declaraciones: {result.declaraciones_encontradas}")
    print(f"  Productos: {result.productos_extraidos}")
```

## Configuración

El sistema utiliza un sistema de configuración flexible:

```python
from config import Config, ConfigManager

# Crear configuración personalizada
config = Config(
    log_level="DEBUG",
    max_financial_lines=15,
    export_formats=['excel', 'json']
)

# Crear procesador con configuración
processor = DeclaracionProcessor(config)
```

### Variables de Entorno

También se puede configurar mediante variables de entorno:

```bash
export LOG_LEVEL=DEBUG
export WORKING_DIRECTORY=/ruta/al/directorio
```

## Modelos de Datos

### DeclaracionData

Representa los datos generales de una declaración de importación:

```python
from models import DeclaracionData

declaracion = DeclaracionData(
    numero_declaracion="1 DE 4",
    tipo_declaracion="DO /IMP",
    nit_importador="900428482",
    nombre_importador="YADAS WT IMPORTACIONES S.A.S."
)
```

### ProductoData

Representa los datos de un producto:

```python
from models import ProductoData

producto = ProductoData(
    declaracion_numero="1",
    producto="RODAMIENTOS DE BOLA",
    marca="NSK",
    modelo="NO TIENE",
    referencia="BD25-9T12C3",
    cantidad="10"
)
```

## Arquitectura

### Módulos

#### 1. Config (`config/`)
- Gestión de configuración del sistema
- Variables de entorno y archivos de configuración
- Parámetros de procesamiento

#### 2. Models (`models/`)
- Definiciones de datos usando dataclasses
- Estructuras para declaraciones y productos
- Métodos de serialización

#### 3. Parsers (`parsers/`)
- Parsing de datos generales de declaraciones
- Análisis línea por línea
- Extracción estructurada de información

#### 4. Extractors (`extractors/`)
- Extracción de productos usando múltiples métodos
- 21 métodos diferentes para diferentes formatos
- Eliminación de duplicados automática

#### 5. Utils (`utils/`)
- Utilidades para procesamiento de texto
- Validaciones de datos
- Gestión de archivos
- Patrones regex reutilizables

#### 6. Tests (`tests/`)
- Tests unitarios para todos los módulos
- Tests de integración
- Mocks para dependencias externas

## Métodos de Extracción de Productos

El sistema implementa 21 métodos diferentes para extraer productos:

1. **Método 1**: Formato completo estándar
2. **Método 2**: Formato simplificado
3. **Método 3**: Patrón flexible para continuación
4. **Método 4**: Formato para productos que cruzan páginas
5. **Método 5**: Formato de continuación
6. **Método 6**: Continuación simplificada
7. **Método 7**: Productos en la misma línea
8. **Método 8**: Descripciones adicionales
9. **Método 9**: Formato país y cantidad
10. **Método 10**: Continuación flexible
11. **Método 11**: Detalles de continuación
12. **Método 12**: Búsqueda comprehensiva
13. **Método 13**: Sección de descripción
14. **Método 14**: Descripción flexible
15. **Método 15**: Patrón CANT // PRODUCTO
16. **Método 16**: Segunda declaración
17. **Método 17**: Marcador de continuación
18. **Método 18**: Continuación avanzada
19. **Método 19**: Continuación simplificada
20. **Método 20**: Lista larga avanzada
21. **Método 21**: Lista larga flexible

## Manejo de Errores

El sistema incluye manejo robusto de errores:

- Logging detallado de todas las operaciones
- Captura y reporte de errores específicos
- Validación de archivos de entrada
- Recuperación de errores en procesamiento individual

## Tests

Ejecutar la suite de tests:

```bash
python -m pytest tests/ -v
```

### Cobertura de Tests

- ✅ Modelos de datos
- ✅ Utilidades de texto y archivos
- ✅ Validaciones
- ✅ Parsers de declaraciones
- ✅ Extractores de productos
- ✅ Integración completa

## Mejores Prácticas Implementadas

### Principios SOLID

1. **Single Responsibility**: Cada clase tiene una responsabilidad única
2. **Open/Closed**: Extensible sin modificar código existente
3. **Liskov Substitution**: Interfaces consistentes
4. **Interface Segregation**: Interfaces específicas y enfocadas
5. **Dependency Inversion**: Dependencias inyectadas

### Patrones de Diseño

- **Factory Pattern**: Fábricas para crear parsers y extractores
- **Strategy Pattern**: Múltiples estrategias de extracción
- **Template Method**: Estructura común para procesamiento
- **Observer Pattern**: Logging y monitoreo de operaciones

### Clean Code

- Nombres descriptivos y significativos
- Funciones pequeñas y enfocadas
- Comentarios y documentación
- Eliminación de código duplicado
- Consistencia en el estilo

## Contribución

1. Fork el proyecto
2. Crear rama para nueva funcionalidad
3. Agregar tests para nueva funcionalidad
4. Implementar la funcionalidad
5. Ejecutar tests completos
6. Crear Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo LICENSE para más detalles.

## Soporte

Para soporte técnico o preguntas:

- Crear un issue en GitHub
- Revisar la documentación
- Ejecutar tests para diagnosticar problemas

## Roadmap

### Versión 2.1
- [ ] Soporte para más formatos de PDF
- [ ] Interfaz web para carga de archivos
- [ ] API REST para integración
- [ ] Configuración avanzada por archivo

### Versión 2.2
- [ ] Machine Learning para extracción automática
- [ ] Soporte para múltiples idiomas
- [ ] Integración con bases de datos
- [ ] Dashboard de análisis

### Versión 3.0
- [ ] Microservicios
- [ ] Procesamiento distribuido
- [ ] Integración con sistemas aduaneros
- [ ] IA para validación automática
