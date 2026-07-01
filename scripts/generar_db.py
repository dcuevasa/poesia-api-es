import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "poesia-api-es/1.0 (+static-json-generator educational project)"
}

POEMAS_FUENTE = [
    {
        "title": "Rima XXI",
        "author": "Gustavo Adolfo Bécquer",
        "url": "https://es.wikisource.org/wiki/Rimas_(B%C3%A9cquer,_1885)/Rima_XXI",
    },
    {
        "title": "Cultivo una rosa blanca",
        "author": "José Martí",
        "url": "https://es.wikisource.org/wiki/Cultivo_una_rosa_blanca",
    },
]


def extraer_lineas_poema(url):
    respuesta = requests.get(url, headers=HEADERS, timeout=30)
    respuesta.raise_for_status()

    soup = BeautifulSoup(respuesta.text, "html.parser")
    contenido = soup.select_one("div.prp-pages-output") or soup.select_one("div.mw-parser-output")

    if contenido is None:
        raise ValueError(f"No se encontro el contenido principal para: {url}")

    for selector in [
        "table",
        ".mw-editsection",
        ".rellink",
        ".noprint",
        ".sister-wikipedia",
        ".metadata",
    ]:
        for nodo in contenido.select(selector):
            nodo.decompose()

    lineas_descartadas = {
        "metadatos",
        ".",
        "obras",
        "versos sencillos",
        "jose marti",
        "josé martí",
        "gustavo adolfo becquer",
        "gustavo adolfo bécquer",
        "1885",
        "españa",
        "100 p.m.a. o menos",
    }

    lineas = []
    for bloque in contenido.find_all(["div", "p"], recursive=False):
        texto = bloque.get_text("\n", strip=True)
        if not texto:
            continue

        for linea in texto.splitlines():
            linea_limpia = " ".join(linea.split())
            if not linea_limpia:
                continue
            if linea_limpia.startswith("←") or linea_limpia.endswith("→"):
                continue
            if linea_limpia.lower() in lineas_descartadas:
                continue
            if linea_limpia.lower().startswith("nota:"):
                continue
            if linea_limpia.lower().startswith("librería de"):
                continue
            if linea_limpia.lower().startswith("imprenta de"):
                continue
            if linea_limpia.lower().startswith("de " ) and len(linea_limpia.split()) <= 4:
                continue
            if len(linea_limpia) < 3:
                continue
            lineas.append(linea_limpia)

    if not lineas:
        raise ValueError(f"No se pudieron extraer versos desde: {url}")

    return lineas


def hacer_scraping_poemas():
    """Extrae poemas de dominio publico en espanol desde Wikisource."""
    poemas = []

    for fuente in POEMAS_FUENTE:
        poemas.append(
            {
                "title": fuente["title"],
                "author": fuente["author"],
                "lines": extraer_lineas_poema(fuente["url"]),
                "language": "SPANISH",
            }
        )

    return poemas


def procesar_poetas(poemas):
    conteo_por_autor = {}

    for poema in poemas:
        autor = poema["author"]
        conteo_por_autor[autor] = conteo_por_autor.get(autor, 0) + 1

    return [
        {
            "name": autor,
            "language": "SPANISH",
            "poemCount": cantidad
        }
        for autor, cantidad in conteo_por_autor.items()
    ]


def guardar_json(datos, ruta):
    ruta_salida = Path(ruta)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)


def main():
    poemas = hacer_scraping_poemas()
    poetas = procesar_poetas(poemas)
    base_dir = Path(__file__).resolve().parent

    guardar_json(poemas, base_dir / "../api/poemas.json")
    guardar_json(poetas, base_dir / "../api/poetas.json")


if __name__ == '__main__':
    main()
