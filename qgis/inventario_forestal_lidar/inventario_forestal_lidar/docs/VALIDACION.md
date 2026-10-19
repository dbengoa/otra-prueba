# Validación 0.3.1 — 19 de octubre de 2026

Corregido el error de Windows «Nomenclatura PNOA3 no reconocida» para
`PNOA-2024-PNR-523-4654-NPC01.laz`, causado por exigir Hxx en el nombre.

Ejecutado en Linux con QGIS 3.40.6: **43 pruebas aprobadas y 3 omitidas** (navegador).
Se añaden dos regresiones: variante exacta de la captura, y comparación de ediciones
con/sin huso conservando el rechazo de husos conocidos incompatibles. Siguen pasando
las pruebas de CRS de metadatos, geometría oficial, descarga simulada e integración.

La ausencia de Hxx nunca se convierte en una declaración de CRS. Tras la descarga se
sigue leyendo el CRS real y se rechazan discrepancias, incluso con la casilla de asumir
CRS activada cuando ya existe un CRS declarado. Sólo se usa el huso de la consulta para
agrupar candidatos sin Hxx; la huella oficial y los metadatos siguen siendo obligatorios.

Las tres pruebas Chromium contra servidor local pasaron en 0.3.0 y no se repitieron:
el código del navegador no ha cambiado. La CI de 0.3.1 ejecuta 33 pruebas portables y
omite 13 de integración. Registro actual: tests-linux.txt.

Pendiente: ejecución de este caso de usuario en Windows, autorización/descarga CNIG
real y FUSION real de extremo a extremo. La consulta de catálogo/huellas no acredita
una descarga ni los cálculos FUSION. Se mantienen los límites documentados del protocolo
web CNIG y los controles de cobertura y apoyo de puntos.

Comprobación CNIG real de sólo lectura: consulta de la tesela PNR reportada,
aceptación del nombre exacto y verificación de su huella/cobertura aprobadas.
Evidencia en live-cnig-pnr-plan.json y live-cnig-pnr-coverage.json.
