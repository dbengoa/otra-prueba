# Verificación documental — 18 de octubre de 2026

## FUSION

Fuente primaria: [manual FUSION 4.61, septiembre de 2024](https://forsys.sefs.washington.edu/software/fusion/FUSION_manual.pdf).
Se revisaron las secciones LDA2LAS (p. 111), GridSurfaceCreate (p. 92), ClipData (p. 43)
CloudMetrics (p. 49) y DTM2ASCII (p. 66); son páginas impresas, no el índice del lector PDF.

Plantillas implementadas:

```text
C:\FUSION\LDA2LAS.exe entrada.laz salida.las
C:\FUSION\GridSurfaceCreate.exe /class:2 mdt.dtm 1 M M 1 <huso> 0 0 teselas.txt
C:\FUSION\DTM2ASCII.exe /raster mdt.dtm mdt.asc
C:\FUSION\ClipData.exe /shape:1 teselas.txt original.las xmin ymin xmax ymax
C:\FUSION\ClipData.exe /shape:1 /dtm:mdt.dtm /height teselas.txt normalizada.las xmin ymin xmax ymax
C:\FUSION\CloudMetrics.exe /new normalizada.las cloudmetrics.csv
```

Se usa una caja de diámetro `2 × radio` centrada en el punto para el círculo. Los
archivos de lista `.txt` evitan límites de longitud al trabajar entre teselas.
Los códigos de datum `0 0` no atribuyen a ETRS89 un código NAD83 ni a las alturas
ortométricas españolas un datum norteamericano. El CRS correcto se conserva en las
salidas GeoPackage y en el manifiesto. Las opciones se verificaron documentalmente;
su compatibilidad con la instalación local debe confirmarse con el smoke test.

## CNIG

- [Catálogo oficial LIDA3](https://centrodedescargas.cnig.es/CentroDescargas/catalogo.do?Serie=LIDA3).
- [Ficha oficial de ejemplo](https://centrodedescargas.cnig.es/CentroDescargas/detalleArchivo?sec=12504242).
- [Novedad CNIG sobre descarga masiva](https://centrodedescargas.cnig.es/CentroDescargas/https%3A/centrodedescargas.cnig.es/CentroDescargas/novedades?codSerie=MAPLI).

El catálogo describe unidades de 1 km, LAZ, UTM y alturas ortométricas. También
identifica varios niveles NPC; mezclarlos sin selección puede duplicar datos.
La ficha de ejemplo sólo acredita la nomenclatura del producto; no se usa como índice
espacial ni se afirma que cubra las parcelas del usuario.

Intentos HTTP directos al catálogo y a `/lidar-tercera-cobertura`: HTTP 503 desde el
entorno de desarrollo. Se contrastó el contenido oficial mediante consulta web.
No se ha validado búsqueda espacial programática, descarga binaria, autorización
real, ni un contrato de API de CNIG. La versión utiliza consulta oficial en navegador,
índice explícito y enlaces autorizados o descargas oficiales manuales.

## Cambio 0.2.0: metadatos locales

Se contrastó la representación CRS con la especificación ASPRS LAS: GeoTIFF en
`LASF_Projection`/34735 y WKT en 2112, incluidos registros extendidos. Referencias
primarias: [documentos ASPRS](https://community.asprs.org/leadership-restricted/leadership-content/public-documents/standards)
y [representación WKT en LAS](https://asprslas.org/latest/03_crs.html).
El lector de esta versión admite LAS 1.0–1.4; no anuncia soporte LAS 1.5.

El catálogo CNIG volvió a responder HTTP 503. La nueva interfaz usa exclusivamente
archivos locales; ya no necesita un índice ni identificadores `sec`.
