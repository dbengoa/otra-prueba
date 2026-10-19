0.4.0 experimental: Chrome normal con clic humano; resto automático.

El plugin consulta/deduplica PNOA3, abre cada ficha oficial en Chrome habitual y espera
que pulse Descargar. Vigila la carpeta Descargas indicada en la interfaz y recoge
la tesela completa sin seleccionar archivos. Conserva la descarga y la copia a
originales/<sec>/. Continúa con LAS, MDT clase 2, ClipData, CloudMetrics y CSV/GPKG.
Retira CDP, perfiles temporales y clics programados que CNIG detectaba. Cancelar no
cierra Chrome ni sus descargas. Reanudar reutiliza los originales completos.

Instale el ZIP desde QGIS y reinicie. Revise que «Descargas de Chrome» coincide con
su carpeta habitual. Cada tesela pendiente puede requerir un clic y autorización.

Validación: 56 pruebas Linux/QGIS aprobadas; 46 portables y 10 omitidas sin QGIS.
Pendiente: clic/descarga real CNIG con Chrome Windows y ejecución FUSION real.
No incluye modelización estadística ni garantiza autorización del servidor.
