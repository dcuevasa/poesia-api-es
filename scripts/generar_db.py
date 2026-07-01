import json
import os
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests import RequestException


HEADERS = {
    "User-Agent": "poesia-api-es/1.0 (+static-json-generator educational project)"
}

BASE_URL = "https://es.wikisource.org"

CATEGORIA_POESIAS_POR_AUTOR_URL = "https://es.wikisource.org/wiki/Categor%C3%ADa:Poes%C3%ADas_por_autor"
MAX_PAGINAS_CATEGORIA = int(os.getenv("POESIA_MAX_PAGINAS_CATEGORIA", "2"))
MAX_AUTORES = int(os.getenv("POESIA_MAX_AUTORES", "80"))
MAX_OBRAS_POR_AUTOR = int(os.getenv("POESIA_MAX_OBRAS_POR_AUTOR", "8"))
MAX_POEMAS_POR_OBRA = int(os.getenv("POESIA_MAX_POEMAS_POR_OBRA", "80"))

PALABRAS_CLAVE_POESIA = (
    "poema",
    "poemas",
    "poesía",
    "poetica",
    "poética",
    "poesias",
    "poesías",
    "rima",
    "rimas",
    "verso",
    "versos",
    "canción",
    "canciones",
    "romance",
    "romances",
    "oda",
    "odas",
    "soneto",
    "sonetos",
    "copla",
    "coplas",
)

FRASES_DESCARTADAS = {
    "metadatos",
    ".",
    "obras",
    "versos sencillos",
    "la edad de oro",
    "jose marti",
    "josé martí",
    "gustavo adolfo becquer",
    "gustavo adolfo bécquer",
    "1885",
    "1889",
    "españa",
    "artículo enciclopédico",
    "descargar como pdf",
    "descargar como epub",
    "descargar como mobi",
    "100 p.m.a. o menos",
}

PATRONES_DESCARTADOS = (
    "nota:",
    "librería de",
    "imprenta de",
    "descargar como",
    "subir un archivo",
    "añadir texto",
    "añadir imagen",
    "versión para imprimir",
)

PATRON_ROMANO = re.compile(r"^[IVXLCDM]+$")
PATRON_TITULO_RIMA = re.compile(r"^Rima [IVXLCDM]+$")
PATRON_POEMA_SECCIONAL = re.compile(r".+/[IVXLCDM]+$")
PATRON_CATEGORIA_POESIAS_AUTOR = re.compile(r"^Poesías de (.+)$")


def obtener_soup(url):
    respuesta = requests.get(url, headers=HEADERS, timeout=20)
    respuesta.raise_for_status()
    return BeautifulSoup(respuesta.text, "html.parser")


def normalizar_url(href):
    return urljoin(BASE_URL, href)


def extraer_nombre_autor_desde_url(author_url):
    nombre = author_url.rsplit("Autor:", 1)[-1].replace("_", " ")
    return requests.utils.unquote(nombre)


def limpiar_nombre_autor(nombre):
    nombre_limpio = nombre.replace("Autor:", "").strip()
    return " ".join(nombre_limpio.split())


def limpiar_titulo_poema(titulo):
    titulo_limpio = " ".join(titulo.split())
    if not titulo_limpio:
        return None
    if titulo_limpio.lower() in FRASES_DESCARTADAS:
        return None
    if titulo_limpio.lower() == "rimas":
        return None
    return titulo_limpio


def descubrir_autores():
    autores = []
    vistos = set()
    siguiente_url = CATEGORIA_POESIAS_POR_AUTOR_URL
    paginas_visitadas = 0

    while siguiente_url and paginas_visitadas < MAX_PAGINAS_CATEGORIA and len(autores) < MAX_AUTORES:
        try:
            soup = obtener_soup(siguiente_url)
        except RequestException:
            break
        paginas_visitadas += 1

        contenedor_subcategorias = soup.select_one("div#mw-subcategories") or soup.select_one("div.mw-category")
        if contenedor_subcategorias is None:
            break

        for enlace in contenedor_subcategorias.select("a[href]"):
            texto = enlace.get_text(" ", strip=True)
            href = enlace.get("href", "")
            coincidencia = PATRON_CATEGORIA_POESIAS_AUTOR.match(texto)
            if coincidencia is None:
                continue
            nombre_autor = limpiar_nombre_autor(coincidencia.group(1))
            url_autor = normalizar_url(f"/wiki/Autor:{nombre_autor.replace(' ', '_')}")
            if url_autor in vistos:
                continue
            vistos.add(url_autor)
            autores.append(
                {
                    "author": nombre_autor,
                    "author_url": url_autor,
                }
            )
            if len(autores) >= MAX_AUTORES:
                break

        siguiente = contenedor_subcategorias.select_one('a[href*="pagefrom="]')
        siguiente_url = normalizar_url(siguiente.get("href")) if siguiente else None

    return autores


def es_enlace_poetico(texto, href):
    texto_normalizado = texto.lower()
    href_normalizado = href.lower()

    if any(palabra in texto_normalizado for palabra in PALABRAS_CLAVE_POESIA):
        return True
    if PATRON_TITULO_RIMA.match(texto):
        return True
    if PATRON_ROMANO.match(texto):
        return True
    if "/rimas_" in href_normalizado or "/versos_" in href_normalizado:
        return True

    return False


def descubrir_obras_poeticas(autor):
    try:
        soup = obtener_soup(autor["author_url"])
    except RequestException:
        return []
    contenedor = soup.select_one("div.mw-parser-output") or soup.select_one("div#mw-content-text")
    if contenedor is None:
        return []

    obras = []
    vistos = set()

    for encabezado in contenedor.find_all(["h2", "h3", "h4"]):
        titulo_encabezado = encabezado.get_text(" ", strip=True).lower()
        if not any(clave in titulo_encabezado for clave in ["poes", "poema", "verso", "rima", "soneto", "romance", "oda", "canci"]):
            continue

        for sibling in encabezado.find_next_siblings():
            if getattr(sibling, "name", None) in {"h2", "h3", "h4"}:
                break
            for enlace in sibling.select("a[href]"):
                texto = limpiar_titulo_poema(enlace.get_text(" ", strip=True))
                href = enlace.get("href", "")
                if not texto or not href.startswith("/wiki/"):
                    continue
                if "/wiki/Autor:" in href or "/wiki/Portal:" in href or "redlink=1" in href or "action=edit" in href:
                    continue
                url_obra = normalizar_url(href)
                if url_obra in vistos:
                    continue
                vistos.add(url_obra)
                obras.append(
                    {
                        "author": autor["author"],
                        "title": texto,
                        "url": url_obra,
                    }
                )
                if len(obras) >= MAX_OBRAS_POR_AUTOR:
                    return obras

    for enlace in contenedor.select("a[href]"):
        texto = limpiar_titulo_poema(enlace.get_text(" ", strip=True))
        href = enlace.get("href", "")
        if not texto or not href.startswith("/wiki/"):
            continue
        if "/wiki/Autor:" in href or "/wiki/Portal:" in href or "redlink=1" in href or "action=edit" in href:
            continue
        if not es_enlace_poetico(texto, href):
            continue

        url_obra = normalizar_url(href)
        if url_obra in vistos:
            continue
        vistos.add(url_obra)
        obras.append(
            {
                "author": autor["author"],
                "title": texto,
                "url": url_obra,
            }
        )
        if len(obras) >= MAX_OBRAS_POR_AUTOR:
            break

    return obras


def es_enlace_de_poema(texto, href, obra):
    if not href.startswith("/wiki/"):
        return False
    if PATRON_TITULO_RIMA.match(texto):
        return True
    if PATRON_ROMANO.match(texto):
        return True
    if PATRON_POEMA_SECCIONAL.match(href.split("/wiki/")[-1].replace("_", " ")):
        return True
    if href.startswith(obra["url"].replace(BASE_URL, "/wiki/" ) + "/"):
        return True

    return False

def descubrir_poemas_de_obra(obra):
    try:
        soup = obtener_soup(obra["url"])
    except RequestException:
        return []
    contenedor = soup.select_one("div.mw-parser-output") or soup.select_one("div#mw-content-text")

    if contenedor is None:
        return []

    poemas = []
    vistos = set()

    for enlace in contenedor.select("a[href]"):
        titulo = limpiar_titulo_poema(enlace.get_text(" ", strip=True))
        href = enlace.get("href", "")
        if not titulo or not href.startswith("/wiki/"):
            continue
        if not es_enlace_de_poema(titulo, href, obra):
            continue

        url_poema = normalizar_url(href)
        clave = (obra["author"], titulo, url_poema)
        if clave in vistos:
            continue
        vistos.add(clave)
        poemas.append(
            {
                "title": titulo,
                "author": obra["author"],
                "url": url_poema,
            }
        )
        if len(poemas) >= MAX_POEMAS_POR_OBRA:
            break

    if poemas:
        return poemas

    return [
        {
            "title": obra["title"],
            "author": obra["author"],
            "url": obra["url"],
        }
    ]


def descubrir_poemas():
    poemas_descubiertos = []

    for autor in descubrir_autores():
        for obra in descubrir_obras_poeticas(autor):
            poemas_descubiertos.extend(descubrir_poemas_de_obra(obra))

    return poemas_descubiertos


def limpiar_linea(linea):
    linea_limpia = " ".join(linea.split())
    if not linea_limpia:
        return None

    linea_normalizada = linea_limpia.lower()

    if linea_limpia.startswith("←") or linea_limpia.endswith("→"):
        return None
    if linea_normalizada in FRASES_DESCARTADAS:
        return None
    if any(linea_normalizada.startswith(prefijo) for prefijo in PATRONES_DESCARTADOS):
        return None
    if linea_normalizada.startswith("de ") and len(linea_limpia.split()) <= 4:
        return None
    if linea_limpia in {"i: i", "i: i.", "i", "xxix", "xxxix"}:
        return None
    if len(linea_limpia) < 3:
        return None

    return linea_limpia


def puntuar_bloque(lineas):
    if len(lineas) < 3:
        return -1

    puntaje = 0
    for linea in lineas:
        if any(caracter in linea for caracter in [",", ";", "¿", "?", "!", "¡"]):
            puntaje += 2
        if len(linea.split()) >= 3:
            puntaje += 1
        if linea[:1].isupper():
            puntaje += 1

    return puntaje


def extraer_lineas_de_bloque(bloque):
    texto = bloque.get_text("\n", strip=True)
    if not texto:
        return []

    lineas = []
    for linea in texto.splitlines():
        linea_limpia = limpiar_linea(linea)
        if linea_limpia:
            lineas.append(linea_limpia)

    return lineas


def seleccionar_bloque_poetico(contenido):
    bloques_candidatos = []

    for bloque in contenido.find_all(["div", "p"], recursive=False):
        lineas = extraer_lineas_de_bloque(bloque)
        if not lineas:
            continue
        bloques_candidatos.append((puntuar_bloque(lineas), lineas))

    if not bloques_candidatos:
        lineas_totales = []
        for bloque in contenido.find_all(["div", "p"]):
            lineas_totales.extend(extraer_lineas_de_bloque(bloque))
        return lineas_totales

    mejor_puntaje, mejores_lineas = max(bloques_candidatos, key=lambda item: (item[0], len(item[1])))

    if mejor_puntaje < 0:
        raise ValueError("No se encontro un bloque poetico util")

    return mejores_lineas


def deduplicar_lineas_consecutivas(lineas):
    resultado = []
    anterior = None

    for linea in lineas:
        if linea == anterior:
            continue
        resultado.append(linea)
        anterior = linea

    return resultado


def extraer_lineas_poema(url):
    soup = obtener_soup(url)
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

    lineas = deduplicar_lineas_consecutivas(seleccionar_bloque_poetico(contenido))

    if not lineas:
        raise ValueError(f"No se pudieron extraer versos desde: {url}")

    return lineas


def hacer_scraping_poemas():
    """Extrae poemas de dominio publico en espanol desde Wikisource."""
    poemas = []

    for fuente in descubrir_poemas():
        try:
            lineas = extraer_lineas_poema(fuente["url"])
        except RequestException:
            continue
        except ValueError:
            continue
        if len(lineas) < 3:
            continue

        titulo = fuente["title"]
        if PATRON_ROMANO.match(titulo):
            titulo = lineas[0]

        poemas.append(
            {
                "title": titulo,
                "author": fuente["author"],
                "lines": lineas,
                "language": "SPANISH",
            }
        )

    return sorted(poemas, key=lambda poema: (poema["author"], poema["title"]))


def procesar_poetas(poemas):
    conteo_por_autor = {}

    for poema in poemas:
        autor = poema["author"]
        conteo_por_autor[autor] = conteo_por_autor.get(autor, 0) + 1

    return sorted([
        {
            "name": autor,
            "language": "SPANISH",
            "poemCount": cantidad
        }
        for autor, cantidad in conteo_por_autor.items()
    ], key=lambda poeta: poeta["name"])


def guardar_json(datos, ruta):
    ruta_salida = Path(ruta)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)


def cargar_json_existente(ruta):
    ruta_entrada = Path(ruta)
    if not ruta_entrada.exists():
        return []
    contenido = ruta_entrada.read_text(encoding="utf-8").strip()
    if not contenido:
        return []
    return json.loads(contenido)


def main():
    poemas = hacer_scraping_poemas()
    base_dir = Path(__file__).resolve().parent
    ruta_poemas = base_dir / "../api/poemas.json"
    ruta_poetas = base_dir / "../api/poetas.json"

    if not poemas:
        poemas = cargar_json_existente(ruta_poemas)

    poetas = procesar_poetas(poemas)

    guardar_json(poemas, ruta_poemas)
    guardar_json(poetas, ruta_poetas)


if __name__ == '__main__':
    main()
