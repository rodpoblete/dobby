<div align="center">
  <img src="dobby-logo-v3.png" alt="Dobby Logo" width="300"/>

  # Dobby - Transformador de Datos de Matrícula Estudiantil

  *"Dobby está aquí para ayudar con los datos, señor"*

  Herramienta CLI para transformar datos CSV de matrícula estudiantil desde formato fuente al formato de carga del sistema SN.
</div>

---

## Características

- Transforma datos de estudiantes desde formato de 74 columnas al formato SN de 29 columnas
- Valida formato de RUT chileno y dígitos verificadores con soporte para IPE (rango 100/200 millones)
- Limpia y formatea direcciones
- Convierte fechas al formato ISO (YYYY-MM-DD)
- Divide nombres en primer y segundo nombre
- Mapea códigos de comuna a nombres
- Valida direcciones de email
- Formatea números telefónicos
- Indicadores de progreso y salida colorida (interfaz en español)
- Reportes de errores completos

## Instalación

### Usando uv (recomendado)

```bash
git clone <repository-url>
cd dobby
uv sync
```

### Usando pip

```bash
git clone <repository-url>
cd dobby
pip install -e .
```

## Inicio Rápido

Transformar un archivo CSV:

```bash
uv run dobby transform data/alumnos_ser.csv
```

O si está instalado globalmente:

```bash
dobby transform data/alumnos_ser.csv
```

## Uso

### Menú Interactivo

Dobby ahora incluye un menú interactivo que te guía paso a paso a través de las operaciones. Para acceder al menú interactivo, simplemente ejecuta:

```bash
uv run dobby
```

O si está instalado globalmente:

```bash
dobby
```

El menú interactivo te permite:
- 🔄 **Transformar archivo CSV** - Te guía a través de todas las opciones de transformación
- ✅ **Validar archivo CSV** - Valida tu archivo sin procesarlo
- ℹ️ **Ver información y ayuda** - Muestra información detallada sobre la herramienta
- 🚪 **Salir** - Sale del programa

### Comando Transform (Línea de comandos)

Transforma un CSV de matrícula estudiantil desde formato fuente al formato del sistema SN.

```bash
dobby transform ARCHIVO_ENTRADA [OPCIONES]
```

**Opciones:**

- `-o, --output RUTA`: Ruta del archivo CSV de salida (por defecto: data/YYYY-MM-DD-HHMM-alumnos-upload-sn.csv)
- `--rbd INTEGER`: Identificador RBD del colegio (por defecto: 574)
- `--year INTEGER`: Año académico (por defecto: 2025)
- `--local TEXT`: Ubicación del colegio (por defecto: Principal)
- `--dry-run`: Vista previa de la transformación sin escribir el archivo
- `--skip-validation`: Omitir validación de RUT y email
- `-v, --verbose`: Habilitar registro detallado
- `--version`: Mostrar versión y salir

**Ejemplos:**

```bash
# Transformación básica
dobby transform data/alumnos_ser.csv

# Archivo de salida personalizado y parámetros del colegio
dobby transform input.csv -o output.csv --rbd 123 --year 2026

# Vista previa sin escribir archivo
dobby transform input.csv --dry-run

# Modo verboso para ver todas las advertencias de validación
dobby transform input.csv -v

# Omitir validación para procesamiento más rápido
dobby transform input.csv --skip-validation
```

### Comando Validate (Línea de comandos)

Valida el CSV de entrada sin realizar la transformación.

```bash
dobby validate ARCHIVO_ENTRADA [OPCIONES]
```

**Ejemplos:**

```bash
# Validar archivo de entrada
dobby validate data/alumnos_ser.csv

# Validación detallada con errores específicos
dobby validate data/alumnos_ser.csv -v
```

## Formato de Entrada

La herramienta espera un archivo CSV con las siguientes columnas:

- Información del estudiante: Rut, Digito verificador, Nombres, etc.
- Información de dirección: Direccion, Comuna, etc.
- Información académica: Grado, Letra, Fecha de Matricula, etc.
- Información del apoderado: Nombre Apoderado, Email Apoderado, etc.

Requisitos del formato CSV:
- Separador: punto y coma (;)
- Codificación: UTF-8 con BOM (utf-8-sig)

## Formato de Salida

La herramienta genera un archivo CSV con 29 columnas requeridas por el sistema SN.

El archivo se guarda por defecto en la carpeta `data/` con el formato:
```
YYYY-MM-DD-HHMM-alumnos-upload-sn.csv
```

Ejemplo: `data/2025-10-14-1700-alumnos-upload-sn.csv`

## Validación de Datos

### Validación de RUT

La herramienta soporta dos tipos de identificadores:

**RUT Regular:**
- Formato: XXXXXXXX-Y donde Y es el dígito verificador (0-9 o K)
- Valida el dígito verificador usando el algoritmo estándar chileno

**IPE (Identificador Provisorio del Estudiante):**
- Para estudiantes extranjeros sin cédula de identidad definitiva
- Rangos: 100,000,000-199,999,999 o 200,000,000-299,999,999
- El dígito verificador NO se valida (se acepta tal cual)
- Ejemplos: 100123456-0, 200987654-K

### Validación de Teléfonos

La herramienta valida números telefónicos chilenos en ambos formatos:

**Teléfonos Móviles:**
- 9 dígitos empezando con 9
- Rango: 900,000,000 - 999,999,999
- Ejemplo: 987654321

**Teléfonos Fijos:**
- 9 dígitos empezando con código de área (2-7)
- Santiago (2): 223456789
- Regiones (3-7): 512345678, 322345678, etc.
- Rango: 200,000,000 - 799,999,999

**Valores especiales:**
- `0` indica teléfono vacío o no disponible
- Números inválidos se convierten a `0` con advertencia en el log

## Desarrollo

### Configurar Entorno de Desarrollo

```bash
# Clonar repositorio
git clone <repository-url>
cd dobby

# Instalar dependencias incluyendo herramientas de desarrollo
uv sync --all-extras
```

### Ejecutar Tests

```bash
# Ejecutar todos los tests
uv run pytest

# Ejecutar con reporte de cobertura
uv run pytest --cov

# Ejecutar archivo de test específico
uv run pytest tests/test_validators.py
```

### Calidad de Código

```bash
# Formatear código
uv run ruff format .

# Revisar linting
uv run ruff check .

# Corregir problemas de linting
uv run ruff check --fix .
```

## Estructura del Proyecto

```
dobby/
├── src/dobby/           # Código fuente
├── tests/               # Tests unitarios
├── data/                # Archivos de datos
├── logs/                # Archivos de log
├── pyproject.toml       # Configuración del proyecto
└── README.md            # Este archivo
```

## Licencia

MIT License
