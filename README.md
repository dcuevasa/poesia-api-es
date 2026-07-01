# poesia-api-es

API estática de poemas en español de dominio público, generada a partir de un scraper de Wikisource y publicada como JSON estático para que cualquier app o sitio la consuma vía raw file (por ejemplo, GitHub raw).

## Estructura

```text
poesia-api-es/
├── api/
│   ├── poemas.json
│   └── poetas.json
├── scripts/
│   ├── generar_db.py
│   └── requirements.txt
└── .gitignore
```

## Qué hace el script

[scripts/generar_db.py](scripts/generar_db.py):

1. Descubre automáticamente todos los autores catalogados en la categoría [Poesías por autor](https://es.wikisource.org/wiki/Categor%C3%ADa:Poes%C3%ADas_por_autor) de Wikisource — no depende de una lista de URLs escrita a mano.
2. Para cada autor, **verifica la categoría de dominio público que Wikisource ya le asignó** (`DP-Autores-NN` cuando el autor es libre, `DP-NO` cuando no lo es) y descarta por completo a cualquier autor marcado como no libre, sin importar que tenga poemas catalogados.
3. Descubre las obras/colecciones de cada autor y, dentro de ellas, cada poema individual.
4. Extrae el texto real del poema, limpiando tablas, notas editoriales, plantillas de licencia de Wikimedia y widgets de "Public domain / Más información..." que aparecen en páginas basadas en un archivo escaneado.
5. Guarda el resultado en [api/poemas.json](api/poemas.json) y [api/poetas.json](api/poetas.json), con codificación UTF-8 (`ensure_ascii=False`) para preservar tildes y eñes.
6. **Nunca sobrescribe por completo**: combina lo recién scrapeado con lo ya guardado (por autor + título), así que una corrida que falla a mitad de camino no hace perder lo ya capturado. Además guarda un checkpoint cada 10 autores procesados.

### Por qué Wikisource

Wikisource ya hace su propio trabajo de verificación de dominio público por autor (categorías `DP-Autores-NN`), lo cual es mucho más confiable que intentar derivar la regla de "vida + N años" nosotros mismos para cada país. El scraper respeta esa curación: si Wikisource dice que un autor no es libre, no se toca.

### Limitaciones conocidas (honestas)

- Algunas páginas de "obras completas" o antologías (p. ej. *Rimas sacras* de Lope de Vega) se guardan como un solo poema muy largo en vez de dividirse en poemas individuales. No es un problema legal, pero sí de granularidad.
- Los poemas de autores no hispanohablantes (traducidos al español) dependen de que Wikisource aloje esa traducción específica de forma segura. Se removieron manualmente los casos donde la traducción tenía un crédito de traductor moderno con licencia incierta (ver historial de commits).
- No hay una lista curada de "todos los poetas famosos en español" — la cobertura depende de qué tan bien esté organizada la categoría de cada autor en Wikisource.

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

Variables de entorno opcionales (todas tienen un valor por defecto razonable):

| Variable | Default | Qué controla |
|---|---|---|
| `POESIA_MAX_PAGINAS_CATEGORIA` | `5` | Páginas de paginación de la categoría de autores a recorrer |
| `POESIA_MAX_AUTORES` | `250` | Tope de autores a procesar por corrida |
| `POESIA_MAX_OBRAS_POR_AUTOR` | `20` | Tope de obras/colecciones a revisar por autor |
| `POESIA_MAX_POEMAS_POR_OBRA` | `120` | Tope de poemas a extraer por obra |
| `POESIA_RATE_LIMIT_SEGUNDOS` | `0.25` | Pausa entre requests a Wikisource (buena práctica ante un servicio compartido) |

## Formato del JSON

Cada poema se guarda como un objeto con esta forma:

```json
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
```

Y cada poeta se guarda con esta forma:

```json
{
	"name": "Gustavo Adolfo Bécquer",
	"language": "SPANISH",
	"poemCount": 1
}
```

Esto facilita consumir el contenido desde una app sin transformaciones adicionales respecto a sus modelos de datos.

## Estado actual de la colección

**138 poemas de 58 poetas** de dominio público en español, entre ellos Gustavo Adolfo Bécquer, José Martí, Rubén Darío, Federico García Lorca, Antonio Machado, Jorge Manrique, Andrés Eloy Blanco, San Juan de la Cruz, Lope de Vega, Luis de Góngora, Calderón de la Barca y Miguel Hernández.

## Próximos pasos

1. Dividir las páginas de "obras completas"/antologías en poemas individuales en vez de guardarlas como un solo bloque largo.
2. Incorporar validación de esquema JSON antes de escribir archivos.
3. Evaluar una fuente secundaria (además de Wikisource) para ampliar cobertura, con el mismo criterio de verificar dominio público antes de incluir nada.
4. Publicar `api/poemas.json` y `api/poetas.json` en GitHub (raw) para que apps externas los consuman directamente.
