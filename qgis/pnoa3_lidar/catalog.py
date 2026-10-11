"""Consulta pública que usa el formulario oficial de la serie LIDA3."""
import json
import re
from http.cookiejar import CookieJar
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPCookieProcessor

BASE = "https://centrodedescargas.cnig.es/CentroDescargas/"


def parse_tiles(html):
    if not re.search(r'id=[\"\']totalArchivos[\"\']', html):
        raise RuntimeError("La respuesta no tiene el formato del catálogo CNIG esperado.")
    found = {}
    for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", html, re.S | re.I):
        filename = re.search(r"\b(PNOA[\w.-]*\.(?:LAS|LAZ))\b", row, re.I)
        sec = re.search(r"(?:linkDescDir_|verArchivo_)(\d+)", row)
        if filename and sec:
            found[sec.group(1)] = {
                "coverage": 3, "filename": filename.group(1), "id": sec.group(1),
                "page_url": BASE + "detalleArchivo?sec=" + sec.group(1),
            }
    total = re.search(r'id=[\"\']totalArchivos[\"\'][^>]*value=[\"\'](\d+)', html)
    if total and int(total.group(1)) > 0 and not found:
        raise RuntimeError("CNIG anuncia resultados, pero no se pudieron identificar los LAS/LAZ.")
    return list(found.values())


def search_tiles(lon, lat):
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        raise ValueError("Coordenadas geográficas inválidas.")
    headers = {"User-Agent": "Mozilla/5.0 (compatible; PNOA3-QGIS/0.1.0)",
               "Accept": "text/html", "Referer": BASE + "lidar-tercera-cobertura"}
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    with opener.open(Request(BASE + "lidar-tercera-cobertura", headers=headers), timeout=40) as response:
        response.read(2_000_000)
    geometry = {"type": "FeatureCollection", "features": [{"type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]}}]}
    fields = {"codAgr": "MOMDT", "codSerie": "LIDA3", "numPagina": "1",
              "coordenadas": json.dumps(geometry)}
    headers["X-Requested-With"] = "XMLHttpRequest"
    request = Request(BASE + "archivosSerie", data=urlencode(fields).encode(), headers=headers)
    with opener.open(request, timeout=40) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise RuntimeError("La respuesta del catálogo supera el tamaño esperado.")
    return parse_tiles(data.decode("utf-8"))
