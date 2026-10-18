Versión experimental para QGIS en Windows con FUSION 4.61 en C:\FUSION.

Incluye interfaz, conservación de originales, conversión LAZ/LAS con caché SHA-256,
cobertura entre teselas, MDT de clase 2, ClipData circular y normalizado, CloudMetrics,
CSV y GeoPackage por ID, progreso y cancelación. La modelización queda fuera de esta fase.

**Limitaciones:** requiere índice CSV explícito de huellas y fichas oficiales CNIG;
no implementa descubrimiento espacial automático desde sólo los centros. CNIG devolvió
HTTP 503 en las comprobaciones de desarrollo. La autorización se completa en su portal
oficial y admite reutilizar los originales descargados allí.

Pruebas ejecutadas: 18 aprobadas en Linux con QGIS 3.40.6, incluidas 15 portables.
La CI ejecuta las portables; no ejecuta FUSION ni QGIS. Pendiente: instalación del ZIP,
smoke test FUSION y descarga PNOA3 real en Windows. Consulte README y docs/VALIDACION.md.

Instale el ZIP desde el gestor de complementos QGIS. FUSION no está incluido.
