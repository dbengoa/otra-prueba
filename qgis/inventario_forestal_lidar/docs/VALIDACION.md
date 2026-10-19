# Validación 0.4.2 — 19 de octubre de 2026

Ejecutado: 83 pruebas aprobadas en Linux con QGIS 3.40.6; ninguna omitida.
Python sin QGIS: 73 aprobadas y 10 de integración omitidas. Registros en tests-linux.txt
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
evidencias conservadas en FUENTES.md. No se repitió descarga binaria CNIG en 0.4.2.

## Regresión del fallo ClipData comunicado

Nueve pruebas portables adicionales verifican selección de variantes 64/32, pareja
LDA2LAS/LASzip, instalación sólo 64-bit, directorio de arranque, registro privado,
variables heredadas sin modificar el entorno QGIS y códigos de error firmados o no.
La prueba de arranque sustituye Popen; verifica el comando persistido cuando el
proceso termina con 3221225477. No ejecuta un binario FUSION real.

La integración QGIS reproduce el fallo de ClipData tras las conversiones (FUSION
sustituido): estado failed en recorte circular, todas las teselas verificadas y
reutilizadas, sin CSV final ni falsas métricas. Verifica también la ruta de cada
LAS, aviso CloudMetrics y salida GeoPackage en el caso satisfactorio.

El registro real del usuario prueba dos conversiones y un MDT satisfactorios con
FUSION 4.61 de 32 bits, no una prueba satisfactoria de ClipData/CloudMetrics. No se
ha reproducido aquí el fallo real. No se conserva su registro íntegro en el repositorio
por contener rutas personales de red; sólo el código de error en pruebas sintéticas.

## Regresiones de lectura y estado 0.4.2

18 pruebas adicionales reproducen I/O fallida: reintento de ENOENT, temporales únicos
con escritores concurrentes, conservación de JSON previo, cancelación, disco lleno,
carpeta desaparecida y diagnóstico alternativo. Verifican que un fallo de estado final
no sustituye el error original, la cancelación o la autorización, y que un fallo de
confirmación después del cálculo no se anuncia como éxito completo.

Para errno 22 se simulan lecturas de metadatos y puntos fallidas, reapertura con el
mismo offset, descarte de una lectura parcial y límites de 1 MiB. Se comprueba que los
archivos fuente permanecen intactos. El error persistente conserva errno, ruta y byte.
La prueba no reproduce la causa real de errno 22 en el servidor del usuario.

El workflow ejecuta estas 18 pruebas en Windows antes de permitir la publicación;
consulte Actions para confirmar el resultado del runner de la versión descargada.
En Linux se ejecutó además toda la suite QGIS/GDAL con 83 pruebas aprobadas. Las
pruebas portables son 73 aprobadas y 10 omitidas por requerir QGIS.

## Pendiente en Windows, con datos reales

1. Comprobar que ClipData64.exe y dependencias oficiales están en C:\FUSION si se desea 64 bits.
   Instalar ZIP y reiniciar QGIS; comprobar versión 0.4.2 y carpeta Descargas.
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
7. Reproducir la parcela 213.0 del incidente, confirmar lectura de LAS/cobertura y
   que un fallo primario aparece antes del aviso de guardado. Probar desconexión y
   reconexión de Q: sin datos originales únicos en riesgo; revisar el respaldo local.
8. Si ClipData falla, comprobar fase/ejecutable/código y /version en proceso.log;
   guardar estado.json y fusion.log. Distinguir fallo de arranque de fallo al recortar.
9. Inspeccionar proceso.log, estado.json, coberturas y recibos SHA-256; comparar cotas y
   métricas con una ejecución FUSION independiente antes de uso productivo.

La autorización CNIG depende del servidor. Esta versión permite el clic humano oficial;
no pretende eludir rechazos ni ser una descarga desatendida.

En la primera ejecución Windows, la prueba de escritores concurrentes reprodujo
WinError 5 al reemplazar el JSON. Se añadió reintento acotado también para ese código,
que puede corresponder a un bloqueo de reemplazo. Una denegación persistente se
sigue notificando sin cambiar permisos; se comprueba que mantiene el JSON anterior.


## Versión 0.4.3 — corte de altura (19-10-2026)

Ejecutadas 90 pruebas aprobadas en Linux con QGIS 3.40.6. Las nuevas comprobaciones
incluyen /minht sólo en CloudMetrics, umbral cero/fractional/desactivado, parámetros
inválidos, recuentos y metadatos, ausencia de retornos, controles de la interfaz y
flujo automático con FUSION simulado que exporta el corte a CSV y GeoPackage.
No se ejecutó FUSION real ni CloudMetrics.exe en Linux. Pendiente: instalación y
flujo real en Windows, y comprobar los estadísticos numéricos filtrados con FUSION
4.61 sobre datos reales. El manual oficial 4.61 respalda /minht; /above no sustituye
el filtrado de las estadísticas.
