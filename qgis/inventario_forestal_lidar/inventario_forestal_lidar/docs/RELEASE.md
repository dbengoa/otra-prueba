Versión 0.2.0 experimental: **ya no se necesita el índice CSV CNIG**.

Seleccione los originales LAZ/LAS con «Archivos…» o «Carpeta…». El complemento lee
metadatos y CRS automáticamente, deduplica copias, conserva los originales y comprueba
apoyo de puntos y suelo antes del MDT y las métricas. Rechaza CRS incompatibles y
archivos solapados; permite asumir el CRS de parcelas sólo si falta y el usuario lo
confirma explícitamente mediante la casilla correspondiente.

La descarga/autorización continúa en el portal oficial CNIG. Su catálogo devolvió
HTTP 503 en desarrollo; no se afirma búsqueda automática en línea. El control local
es muestreado y no certifica huellas oficiales ni ausencia de huecos a cualquier escala.

Requiere Windows, QGIS 3.34+ y FUSION 4.61 en C:\FUSION. Instale el ZIP sin descomprimir
con el gestor QGIS y reinicie QGIS para recargar el código de la versión anterior.

Pruebas ejecutadas: 30 aprobadas en Linux/QGIS 3.40.6, incluidas 24 portables. El ensayo
del flujo completo utiliza un sustituto de FUSION; la exportación QGIS/GDAL es real.
Pendientes: FUSION real y prueba PNOA3 LAZ/Windows. La CI ejecuta las 24 portables.
Sin modelización estadística en esta fase. Consulte README y docs/VALIDACION.md.
