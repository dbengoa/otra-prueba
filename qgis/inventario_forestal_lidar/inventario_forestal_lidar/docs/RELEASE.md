# Inventario forestal LiDAR 0.4.5 experimental

Admite capas Point y MultiPoint (incluidas Z/M). Un MultiPoint con un centro conserva
su ID. La separación de entidades con varios centros requiere activar la casilla;
crea IDs <ID>__p1, <ID>__p2, etc., con correspondencia en parcelas_entrada.json.
Identifica geometrías vacías e IDs nulos, duplicados o generados en colisión.

Añade al CSV y GPKG n_primeros_retornos, n_primeros_retornos_sobre_corte,
altura_cobertura_m, cobertura_primeros_retornos_pct y estado_cobertura.
Cobertura = 100 × primeros retornos > corte / primeros retornos totales, incluido
suelo clase 2. Se lee normalizada.las completa antes de CloudMetrics /minht.
Usa el corte activo o 2 m si el filtro está desactivado. Sin primeros retornos:
porcentaje vacío/NULL y aviso. Es indicador LiDAR, no FCC de campo idéntica.

Instalar el ZIP sin descomprimir y reiniciar QGIS. Puede reutilizar la carpeta con
los LAZ/LAS anteriores; cada ejecución genera nuevos resultados sin borrar originales.

Validación local: 104 pruebas aprobadas con QGIS 3.40.6 en Linux; 89 aprobadas y
15 omitidas con Python sin QGIS. Binarios FUSION simulados en pruebas de flujo.
Pendiente local: instalación, Point/MultiPoint y cálculo real FUSION 4.61 en Windows.
La CI comprueba además la lectura de retornos en Windows; no equivale a FUSION real.
