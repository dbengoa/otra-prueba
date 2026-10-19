0.4.3 experimental: altura de corte configurable para métricas LiDAR.

Casilla para activar/desactivar el filtro; corte inicial 2 m. CloudMetrics usa
/minht:h sobre la nube normalizada. MDT sigue usando clase 2. Se conservan todos
los puntos en LAZ, LAS y normalizada.las. CSV y GeoPackage registran altura de
corte, tipo de filtro y retornos usados; las métricas mantienen nombres cm_.
Se valida el recuento filtrado y se informa del ID si no quedan retornos.

Instalar ZIP y reiniciar QGIS. Reutilizar la misma carpeta y LAZ/LAS para generar
nuevos resultados homogéneos con el corte elegido. No mezclar filtros al modelizar.

Ejecutado: 90 pruebas Linux/QGIS 3.40.6, incluidas 6 nuevas pruebas portables del
corte, controles de interfaz y flujo con FUSION simulado + exportación CSV/GPKG.
Pendiente: ejecución real de CloudMetrics /minht y flujo completo en Windows.
La publicación automática comprueba almacenamiento y filtro con Python de Windows;
esas pruebas no ejecutan FUSION ni sustituyen la comprobación real en ese equipo.
