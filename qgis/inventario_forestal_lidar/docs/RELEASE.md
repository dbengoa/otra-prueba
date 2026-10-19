0.4.2 experimental: lectura LAS más robusta y conservación del error original.

El registro recibido muestra primero errno 22 durante cobertura y después un fallo
al escribir estado.json.tmp que ocultaba el error inicial. Los LAS se habían convertido.
La causa interna del primer error no está confirmada con el registro disponible.

Ahora se leen puntos sin búfer Python, en bloques <=1 MiB y con reapertura/reintento
del mismo rango ante errno 22 o fallos transitorios. Se conserva cada punto; no se
omite cobertura. El error persistente indica archivo/byte y se registra el traceback.

JSON: temporales únicos, tres reintentos adicionales breves, conservación del archivo
anterior y diagnóstico alternativo en LOCALAPPDATA/InventarioForestalLiDAR/diagnosticos.
Un fallo final de escritura no sustituye errores, cancelaciones o autorizaciones.
No se crean automáticamente carpetas de red desaparecidas ni se promete reparar Q:.

Instalar ZIP, reiniciar QGIS y reanudar en la misma carpeta sin borrar LAZ, LAS o recibos.
Validación Linux/QGIS: 83 pruebas aprobadas; 72 portables y 10 omitidas sin QGIS.
La publicación requiere las 18 pruebas de almacenamiento/lectura en Windows CI.
Pendiente: reproducir el caso real en Q: y la ejecución FUSION/CNIG completa en ese equipo.
