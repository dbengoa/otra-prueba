# Validación 0.2.0 experimental

Fecha: 18 de octubre de 2026. No se afirma validación Windows.

## Ejecutado

- 24 pruebas portables aprobadas con Python estándar.
- 30 pruebas aprobadas con QGIS 3.40.6-Bratislava/GDAL/Numpy en Linux, Qt offscreen:
  las 24 anteriores y 6 pruebas QGIS/GDAL reales.
- Interfaz sin campo de índice; selección múltiple sin rutas repetidas, defaults y
  casilla de asumir CRS desactivada. La apertura del selector nativo Windows no se prueba.
- Lectura binaria de metadatos LAS 1.2 y 1.4, VLR/EVLR, GeoTIFF, WKT y CRS compuesto;
  rechazo de WKT/GeoTIFF contradictorios, CRS incompatible, registros truncados,
  escalas o extensiones inválidas. CRS ausente exige consentimiento explícito.
- Fixture de cabecera marcada LAZ: lectura de metadatos sin descompresión. **No es
  un flujo LAZ comprimido real ni acredita compatibilidad del decodificador FUSION.**
- Deduplicación por contenido de copias con nombres distintos y detección de solapes.
- Cuatro LAS sintéticos reales con coordenadas y suelo: apoyo muestreado correcto;
  falta una tesela: error; sólo vegetación y ningún suelo: error.
- Flujo del motor sin `index` ni CSV, usando cuatro LAS y rutas fuente con espacios.
  **FUSION sustituido por un fake** que produce salidas de prueba. Se comprueban los
  comandos encadenados, QGIS/GDAL real, exportaciones, manifiestos, originales intactos
  y segunda ejecución sin repetir conversiones. No acredita los cálculos FUSION.
- Pruebas heredadas de error, cancelación, cabecera, cobertura oficial declarada,
  autorización del adaptador antiguo y CSV/GPKG por ID siguen aprobadas.
- Nueva consulta HTTP real CNIG: 503. La descarga no está validada.

Salida completa en `tests-linux.txt`. La CI ejecuta sólo las 24 portables y omite
explícitamente las 6 pruebas que dependen del entorno QGIS.

## Pendiente en Windows

1. Instalar el ZIP 0.2.0, reiniciar QGIS y comprobar el selector de archivos/carpeta.
2. Ejecutar `tools/windows_smoke.py` con FUSION 4.61: cuatro LAS con CRS, círculo en
   esquina, terreno de 100 m, alturas 0/10 m y exportaciones. El script ya usa la nueva
   entrada local sin índice CSV.
3. LAZ PNOA3 real (LAS 1.4 RGBI): metadatos CRS, conversión y control de apoyo. Revisar
   año, NPC y datum vertical en la fuente oficial; no se infieren de la cabecera.
4. Parcelas dentro de una tesela, en un borde y en esquina de cuatro teselas.
5. Cancelación durante lectura, conversión y cálculo; `taskkill /T` y originales intactos.
6. Unicode, falta de espacio/permisos, lotes grandes, biblioteca LAZ de FUSION y
   recuperación tras una ejecución interrumpida.
7. Autorización y descarga CNIG en el portal real. La búsqueda espacial y descarga
   programática en línea siguen pendientes de un contrato oficial verificable.

La comprobación local de apoyo tiene una escala configurable; no puede certificar
completitud de adquisición ni detectar huecos más pequeños que esa escala. Los límites
de cabecera son envolventes de puntos, no huellas oficiales de entrega.
