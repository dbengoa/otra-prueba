# Validación 0.4.0 — 19 de octubre de 2026

Ejecutado: 56 pruebas aprobadas en Linux con QGIS 3.40.6; ninguna omitida.
Python sin QGIS: 46 aprobadas y 10 de integración omitidas. Registros en tests-linux.txt
 y tests-portable.txt. Los avisos de Qt/GDAL no afectan al resultado.

Once pruebas de vigilancia verifican nombres (guiones/bajos/sufijos), copia conservando
fuente, temporales .crdownload, HTML, tesela incorrecta, enlaces simbólicos, estabilidad,
cambio de fuente durante copia, reutilización, cancelación y reapertura de ficha.
El lanzamiento se comprueba con Popen sustituido: sólo Chrome normal, --new-tab y URL
oficial. No se utiliza CDP, navegador headless, perfil temporal ni clic programado.

La integración QGIS/GDAL recorre cuatro teselas vecinas con una descarga humana
simulada que entrega archivos sintéticos en Descargas. La vigilancia real los incorpora;
FUSION está sustituido por fixtures. Se verifica exportación CSV/GeoPackage y caché.
Se mantienen pruebas de CRS, cobertura/MDT, parámetros FUSION, nombres PNR sin Hxx,
deduplicación, errores y cancelación. No son cálculos FUSION reales.

Consultas CNIG reales de catálogo y geometrías: ejecutadas en versiones anteriores,
evidencias conservadas en FUENTES.md. No se repitió descarga binaria CNIG en 0.4.0.

## Pendiente en Windows, con datos reales

1. Instalar ZIP y reiniciar QGIS; comprobar versión 0.4.0 y carpeta Descargas.
2. Centros con cobertura PNOA3; incluir parcela entre dos teselas y esquina de cuatro.
3. Ejecutar, comprobar Chrome habitual sin depuración. Pulsar Descargar, completar
   trámite oficial y guardar en carpeta indicada sin renombrar. No abrir descargaDir
   como enlace directo. Confirmar incorporación automática al terminar.
4. Verificar variantes Chrome «preguntar dónde guardar», Descargas reubicada y unidad
   de salida Q:/red. Si Chrome usa carpeta propia, configurarla en QGIS antes de ejecutar.
5. Cancelar durante espera/copia/FUSION: Chrome queda abierto, originales intactos;
   reanudar debe reutilizar las teselas completas sin nueva descarga.
6. Con FUSION 4.61 real y bibliotecas LAZ: comprobar descompresión, conteos, MDT clase 2,
   círculo y normalización ClipData, métricas y coincidencia de IDs en CSV/GPKG.
7. Inspeccionar proceso.log, estado.json, coberturas y recibos SHA-256; comparar cotas y
   métricas con una ejecución FUSION independiente antes de uso productivo.

La autorización CNIG depende del servidor. Esta versión permite el clic humano oficial;
no pretende eludir rechazos ni ser una descarga desatendida.
