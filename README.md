# poesia-api-es

Proyecto base para construir una API estática de poemas en español a partir de archivos JSON.

La idea del proyecto es recolectar poemas de dominio público mediante web scraping, normalizarlos en una estructura simple y guardarlos en [api/poemas.json](api/poemas.json) para que luego puedan ser consumidos por un frontend, un generador de sitios estáticos o una API muy ligera.

## Estructura

```text
poesia-api-es/
├── api/
│   └── poemas.json
├── scripts/
│   ├── generar_db.py
│   └── requirements.txt
└── .gitignore
```

## Qué hace el script

El archivo [scripts/generar_db.py](scripts/generar_db.py) ahora:

- importa las librerías necesarias para scraping y serialización JSON;
- hace scraping real de poemas de dominio público en español desde Wikisource;
- usa un catálogo curado de fuentes para priorizar legalidad, estabilidad y limpieza del texto;
- genera una colección ampliada con obras de Gustavo Adolfo Bécquer y José Martí;
- guarda el resultado en [api/poemas.json](api/poemas.json) con codificación UTF-8;
- usa `ensure_ascii=False` para preservar correctamente caracteres como tildes y eñes.

La fuente elegida es Wikisource en español, que publica textos de dominio público y expone HTML estático suficientemente estable para una extracción simple. El enfoque actual no intenta recorrer todo el sitio de forma indiscriminada: mantiene una lista curada de poemas y reglas de limpieza para evitar introducir ruido editorial en la base de datos.

## Requisitos

- Python 3.10 o superior
- pip

Dependencias definidas en [scripts/requirements.txt](scripts/requirements.txt):

- requests
- beautifulsoup4

## Instalación

### Windows

```bash
python -m venv venv
venv\Scripts\activate
pip install -r scripts/requirements.txt
```

### macOS y Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r scripts/requirements.txt
```

## Uso

Ejecuta el script desde la raíz del proyecto:

### Windows

```bash
python scripts/generar_db.py
```

### macOS y Linux

```bash
python3 scripts/generar_db.py
```

Al ejecutarlo, se generarán o sobrescribirán [api/poemas.json](api/poemas.json) y [api/poetas.json](api/poetas.json) con una estructura como esta:

```json
[
	{
		"title": "Rima XXI",
		"author": "Gustavo Adolfo Bécquer",
		"lines": [
			"¿Qué es poesía?, dices mientras clavas",
			"en mi pupila tu pupila azul.",
			"¿Qué es poesía? ¿Y tú me lo preguntas?",
			"Poesía... eres tú."
		],
		"language": "SPANISH"
	}
]
```

## Formato del JSON

Cada poema se guarda como un objeto con esta forma:

```json
{
	"title": "Nombre del poema",
	"author": "Nombre del autor",
	"lines": ["Verso 1", "Verso 2", "Verso 3"],
	"language": "SPANISH"
}
```

Y cada poeta se guarda con esta forma:

```json
{
	"name": "Nombre del autor",
	"language": "SPANISH",
	"poemCount": 1
}
```

Esto facilita consumir el contenido desde la app Android sin transformaciones adicionales respecto a sus modelos.

## Estado actual de la colección

La base generada incluye actualmente poemas públicos de:

- Gustavo Adolfo Bécquer
- José Martí

El catálogo inicial ya contiene poemas breves y poemas largos, y está preparado para crecer añadiendo nuevas URLs públicas verificadas dentro del arreglo `POEMAS_FUENTE`.

## Próximos pasos

1. Añadir más autores de dominio público con páginas verificadas en Wikisource.
2. Incorporar validación del esquema JSON antes de escribir archivos.
3. Añadir una fuente secundaria legal para ampliar cobertura si la estructura HTML es estable.
4. Exponer [api/poemas.json](api/poemas.json) y [api/poetas.json](api/poetas.json) mediante un hosting estático.
