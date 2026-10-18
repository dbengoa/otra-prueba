0.3.0 experimental: **descarga automática CNIG desde la capa de parcelas**.

La interfaz ya no pide CSV ni archivos LAZ/LAS. Consulta espacialmente LIDA3, pagina y
deduplica resultados, obtiene huellas oficiales y comprueba cobertura. Descarga mediante
el botón real del portal en una ventana independiente de Edge/Chrome, respetando su
reCAPTCHA, preautorización y licencia. El usuario sólo interviene si CNIG lo requiere.
El plugin recoge los originales y continúa con conversión LAS, MDT clase 2, ClipData,
CloudMetrics y CSV/GeoPackage por ID. Conserva y reutiliza archivos verificados.

Instale el ZIP sin descomprimir y reinicie QGIS. Requiere QGIS 3.34+, Windows,
FUSION 4.61 en C:\FUSION y Edge o Chrome. Sin modelización estadística.

**Verificado:** consulta CNIG real HTTP 200 y huellas de cuatro teselas en una esquina;
44 pruebas Linux/QGIS/Chromium aprobadas. El navegador se probó contra un servidor
local con aprobación simulada, y la integración del motor sustituye FUSION por fixtures.
**Pendiente:** autorización/descarga CNIG real y FUSION de extremo a extremo en Windows.
No se presenta la prueba local como validación del reCAPTCHA o LAZ real.

La descarga depende de autorización CNIG y de un protocolo web sin contrato estable.
El plugin no elude ese control ni cambia el flujo por carga manual. Detalles en README,
docs/FUENTES.md y docs/VALIDACION.md.
