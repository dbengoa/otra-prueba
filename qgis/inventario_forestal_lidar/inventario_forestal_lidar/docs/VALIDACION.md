# Validación experimental

Fecha: 18 de octubre de 2026.

## Ejecutado en Linux

- Escritura y lectura de archivo de comprobación: correctas.
- Acceso a `dbengoa/otra-prueba`: correcto; conector con permiso `push`.
- Rama nueva `experimental/inventario-forestal-lidar-0.1.0` creada.
- 15 pruebas portables: aprobadas con Python estándar.
- 18 pruebas en total: aprobadas con `/usr/bin/python3`, QGIS **3.40.6-Bratislava**,
  GDAL y Qt en modo offscreen. Incluyen las 15 anteriores y 3 pruebas QGIS reales:
  construcción de interfaz, exportación/relectura CSV/GPKG por ID y detección de huecos MDT.
- Casos de cobertura: círculo entre cuatro teselas, hueco interior, vecinas ausentes,
  deduplicación y rechazo de niveles solapados.
- Casos de fallo: ID duplicado, radio inválido, CRS incompatible, HTML en lugar de nube,
  LAS truncado/vacío, falta de autorización, código de salida no cero y cancelación
  de proceso hijo. Se comprueban los estados persistidos.
- Verificación documental de parámetros FUSION y del catálogo CNIG.
- HTTP real a CNIG: **503, no superado**. No es una descarga probada.

Los comandos se guardan en `tests-linux.txt` en la distribución de esta entrega.
Las pruebas unitarias de parámetros comprueban la construcción de argumentos, no la
respuesta de ejecutables FUSION. Los LAS de esas pruebas son fixtures estructurales.

## Pendiente en Windows

- Instalar el ZIP desde QGIS y comprobar carga/descarga del complemento.
- Ejecutar `tools/windows_smoke.py` con FUSION 4.61 para verificar cuatro teselas,
  clase 2, MDT, círculo, alturas 0/10 m, número de puntos y CSV/GPKG.
- LAZ PNOA3 real (LAS 1.4, RGBI y niveles NPC utilizados) con las bibliotecas de FUSION.
- Un ID dentro de una tesela, uno en límite y uno en esquina de cuatro teselas.
- Descarga CNIG real: sin autorización, sesión/aceptación cuando proceda, enlace
  caducado, error HTTP y reconexión. Comprobar integración manual oficial.
- Cancelar durante descarga, conversión y cálculo; comprobar `taskkill /T`, registros,
  originales intactos y reanudación. La cancelación de procesos se probó sólo en Linux.
- Ejecutar dos veces y verificar reutilización SHA-256; cambiar un original y confirmar
  que se invalida su conversión, sin reutilizar métricas anteriores.
- Probar permisos de carpetas, Unicode, falta de disco y volúmenes de tamaño real.

## Pendiente funcional conocida

La búsqueda espacial y descubrimiento automático de teselas a partir sólo de los
centros **no están implementados** sin un índice explícito. Se necesita verificar el
servicio/contrato oficial antes de añadir un adaptador. Esta entrega es utilizable
experimentalmente con índice fiable y originales descargados por vía oficial, pero
no debe presentarse como una automatización CNIG completa ni como validación Windows.
