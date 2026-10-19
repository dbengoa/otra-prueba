# Validación 0.3.2 — 19 de octubre de 2026

48 pruebas aprobadas en Linux con QGIS 3.40.6 y Chromium headless contra servidor local.
Dos regresiones nuevas comprueban que se buscan todas las instalaciones de Chrome sin
intercalar Edge, y que Chrome del usuario se elige aunque exista Edge en Program Files.
Si sólo existe Edge se informa de que falta Chrome; no se abre Edge como alternativa.

Se repitieron los tres ensayos CDP con Chromium real: aprobación simulada antes de
la transferencia, rechazo de nombre inesperado y cancelación/cierre. Son ensayos
contra un servidor local con LAS sintético, no autorización ni descarga CNIG real.
Se mantienen las pruebas de originales planos (guiones/guiones bajos), caché, CRS,
PNR sin Hxx, cobertura y métricas/exportación con FUSION sustituido por fixtures.

La CI ejecuta 35 pruebas portables y omite 13 de integración. Registro: tests-linux.txt.
La consulta CNIG real de la tesela PNR se ejecutó en 0.3.1; evidencias en FUENTES.md.

Pendiente: verificar Google Chrome de Windows con CNIG y sus autorizaciones, y FUSION
real de extremo a extremo. No se asegura que cambiar de navegador baste para que CNIG
conceda la autorización. Se conservan los originales al cancelar o encontrar errores.
