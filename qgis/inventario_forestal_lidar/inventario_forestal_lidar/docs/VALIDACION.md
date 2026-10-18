# Validación de la versión 0.3.0 experimental

Fecha: 18 de octubre de 2026. Se distingue cada entorno y cada sustituto.

## Ejecutado con servicio CNIG real

- Catálogo, ficha y código JavaScript oficial: HTTP 200 con cabecera AJAX.
- Búsqueda espacial **POST** LIDA3 para radio y margen, no sólo centro.
- Caso de esquina de cuatro teselas en EPSG:25829 `(629000,4780000)`.
- Identificación de cuatro secuenciales diferentes y solicitud de sus huellas oficiales.
- Unión de geometrías con tolerancia de 2 cm: círculo ampliado cubierto, 0 m² restante.
- Revisión del flujo oficial reCAPTCHA → preAutorizarDescarga → initDescargaDir →
  licencia si procede → formulario descargaDir.
- **No se ejecutó autorización ni descarga LAZ real**. La respuesta de initDescargaDir
  de diagnóstico no se consideró autorización. No se llamó directamente al endpoint
  binario para omitir reCAPTCHA.

Evidencia: `live-cnig-plan.json`, `live-cnig-coverage.json` y FUENTES.md.

## Ejecutado en Linux/QGIS y Chromium

**44 pruebas aprobadas**, con `/usr/bin/python3`, QGIS 3.40.6-Bratislava, GDAL/Numpy,
Qt offscreen y Chromium real headless para los tres ensayos locales del navegador.

- **31 portables:** validaciones, metadatos LAS/LAZ, deduplicación, argumentos FUSION,
  errores/cancelación y parser CNIG con una fila real del portal. Catálogo vacío se
  distingue de respuesta HTML inesperada. Se prueban paginación, página repetida,
  política de año/NPC, empate ambiguo y contrato de huellas.
- **10 QGIS/GDAL:** CRS WKT/GeoTIFF, reproyección de huella real, ejes lon/lat, unión de
  cuatro huellas, vecina ausente, control de puntos/suelo, interfaz sin entradas manuales,
  exportación CSV/GPKG por ID, reutilización e integración del motor.
- El ensayo **motor automático sin `files` ni `index`** sustituye consulta/descarga CNIG
  y ejecutables FUSION por fixtures. QGIS/GDAL, recibos, originales y exportaciones son
  reales. No se presenta como cálculo FUSION ni descarga de CNIG reales.
- **3 Chromium/CDP reales contra servidor loopback:** espera de aprobación simulada sin
  petición binaria previa; descarga tras aprobación; rechazo de nombre inesperado;
  cancelación y cierre de la instancia dedicada. El servidor entrega LAS sintético y
  simula una autorización con una bandera JavaScript. **No prueba reCAPTCHA de CNIG**.
- Lectura de cabecera marcada como LAZ sin descompresión: fixture estructural, no LAZ
  comprimido real. Cancelación de procesos FUSION sólo simulada en Linux.

Salida completa: `tests-linux.txt`. La CI sin QGIS/navegador ejecuta las 31 portables y
omite explícitamente 13 ensayos de integración. El control FUSION independiente de
`tools/windows_smoke.py` usa LAS sintéticos y no cubre descarga CNIG.

## Pendiente de ejecutar en Windows

1. Instalar el ZIP 0.3.0 y reiniciar QGIS; comprobar que no pide LAZ/LAS ni CSV.
2. Con Edge/Chrome y FUSION 4.61, usar parcelas de cobertura LIDA3 conocida: una interior,
   otra en borde y otra en esquina. El plugin debe localizar y descargar cada tesela una
   sola vez y continuar sin selección de archivos.
3. Completar reCAPTCHA/licencia únicamente en el portal oficial cuando lo solicite.
   Confirmar que una autorización denegada no se elude y que «Continuar autorización»
   sólo vuelve a activar el control oficial. Probar rechazo, espera y cierre del navegador.
4. LAZ PNOA3 real (LAS 1.4/RGBI): validar CRS, recuentos, terreno clase 2, alturas
   normalizadas y concordancia CSV/GeoPackage por ID.
5. Ejecutar `tools/windows_smoke.py` para verificar FUSION con terreno de 100 m,
   alturas 0/10 m y círculo entre cuatro teselas sintéticas.
6. Repetir ejecución: originales y LAS verificados se reutilizan, métricas nuevas.
7. Cancelar durante descarga, copia a Q:/NAS, conversión y CloudMetrics. Verificar
   cierre sólo del navegador dedicado, `taskkill /T`, originales completos intactos,
   `.part` no admitido como original y reanudación.
8. Permisos, disco lleno, carpetas Unicode, proxy local, política empresarial de Edge
   que deshabilite depuración, y volúmenes de trabajo reales.

El adaptador depende del protocolo actual del portal, sin API pública estable. La
cobertura oficial tiene tolerancia centimétrica y el apoyo de puntos se comprueba a
escala configurable; no se certifica completitud de adquisición a cualquier escala.
