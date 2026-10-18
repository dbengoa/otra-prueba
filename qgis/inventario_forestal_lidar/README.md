# Inventario forestal LiDAR — 0.1.0 experimental

Plugin QGIS para Windows que prepara métricas por centro de parcela con FUSION.
Esta entrega no incluye ajuste, selección ni validación de modelos estadísticos.

**Estado: experimental, no validado de extremo a extremo con FUSION en Windows.**
La interfaz, la exportación GeoPackage y la comprobación del MDT se han probado con
QGIS 3.40.6/GDAL en Linux. Consulte [VALIDACION.md](docs/VALIDACION.md).

## Instalación

1. Instale QGIS 3.34 o posterior para Windows (se recomienda 3.40 LTR).
2. Instale por separado FUSION 4.61 en `C:\FUSION`, con sus bibliotecas de lectura LAZ.
   No se redistribuyen los ejecutables de FUSION.
3. En QGIS: **Complementos → Administrar e instalar complementos → Instalar a partir de ZIP**.
   Seleccione `inventario_forestal_lidar-0.1.0-experimental.zip` y active el complemento.
4. Abra **Complementos → Inventario forestal LiDAR**.

## Uso

- Cargue una capa de puntos simples con un centro por parcela y un campo ID único,
  no vacío. Se procesan **todas** las entidades, no sólo la selección.
- Use el CRS UTM de las teselas: ETRS89 EPSG:25828–25831, o REGCAN95 EPSG:4083.
  Reproyecte antes si es necesario. No se reproyectan las nubes de puntos.
- Seleccione ID, radio (15 m de forma predeterminada), celda MDT (1 m) y una carpeta
  absoluta sin espacios, por ejemplo `C:\InventarioLidar`.
- Pulse **Consultar PNOA3 en CNIG** para abrir el catálogo oficial LIDA3.
- Prepare el índice CSV descrito abajo. Incluya las vecinas que cubren el círculo y
  **dos celdas de margen**. El margen es necesario para comprobar el MDT y su interpolación.
- Pulse **Ejecutar / reanudar**. Si faltan descargas autorizadas, consulte
  `resultados/<ejecucion>/descargas_pendientes.json`, complete el trámite oficial y vuelva
  a ejecutar. Una ejecución nueva conserva los resultados anteriores.
- **Cancelar** solicita detener la descarga o el proceso externo activo. Durante una
  lectura HTTP puede tardar hasta el timeout de 30 s. Los archivos parciales `.part`
  no se reutilizan como originales completos; el próximo intento reinicia esa descarga.

## CNIG y autorización: alcance real de esta versión

Se ha verificado documentalmente el catálogo de tercera cobertura **LIDA3**. No se ha
verificado una API pública de búsqueda espacial/descarga automática. Los intentos
HTTP desde el entorno de desarrollo devolvieron **503**, por lo que esta versión
**no descubre automáticamente las teselas a partir únicamente de los centros**.
La consulta se realiza en el portal oficial; el índice de sus resultados se aporta
explícitamente. Es una limitación funcional pendiente, no una prueba superada.

No se fabrican URL de descarga a partir del nombre o del ID `sec`. Puede proporcionar
un enlace HTTPS de descarga emitido por CNIG en la columna `url`. Se restringen los
redireccionamientos al mismo dominio oficial. Si requiere sesión, aceptación,
CAPTCHA u otra autorización, complete esos pasos **en el portal oficial**, descargue
los archivos y colóquelos en `originales/<sec>/<name>` o directamente en `originales/`.
El plugin enumera las descargas pendientes y permite continuar con esos originales.
No pide contraseñas, no extrae cookies ni elude controles del servicio.

La cesta oficial puede requerir su herramienta de descarga masiva. Un cambio publicado
por CNIG en septiembre de 2026 indica OpenWebStart/Java 17 para nuevos JNLP; siga las
instrucciones vigentes del portal. El plugin no ejecuta JNLP.

### Índice de teselas

CSV UTF-8 con estos encabezados:

```csv
series,sec,name,epsg,xmin,ymin,xmax,ymax,url,sha256
```

- `series`: siempre `LIDA3`, verificado en la ficha CNIG.
- `sec`: identificador numérico de la ficha `detalleArchivo?sec=...`.
- `name`: nombre exacto del archivo LAS/LAZ, sin rutas.
- `epsg`: CRS de la nube y de la capa de centros.
- `xmin,ymin,xmax,ymax`: huella rectangular **oficial**, en metros UTM, no grados.
- `url`: opcional, enlace de descarga oficial autorizado; déjelo vacío si descarga a mano.
- `sha256`: opcional, si dispone de una huella de integridad de confianza.

Obtenga las huellas del índice de distribución o de la información espacial de CNIG;
no deduzca la esquina ni la extensión exclusivamente del nombre. No se incluye un
índice nacional ni se presentan huellas sintéticas como oficiales. Si no dispone de
huellas fiables, no use el plugin para afirmar cobertura completa.

Las filas repetidas con el mismo `sec` y metadatos se deduplican; un conflicto se
rechaza. Si coexisten vuelos, años o niveles NPC sobre la misma zona, elija una sola
versión de cada tesela antes de ejecutar. Los solapes con superficie positiva dentro
de las parcelas se rechazan, para evitar duplicar retornos.

El archivo de índice puede contener enlaces de sesión. Manténgalo fuera de repositorios
públicos. Los registros y la copia de teselas de cada ejecución excluyen esos enlaces.

## Flujo y salidas

1. Valida ID, CRS, radio, archivos FUSION y cobertura por unión de huellas, incluyendo
   las parcelas en límites y esquinas de cuatro teselas. Un hueco aborta el análisis.
2. Descarga o reutiliza originales; valida cabeceras, longitud HTTP cuando se proporciona
   y SHA-256 opcional. Las respuestas HTML de autorización no se aceptan como LAZ.
3. Convierte con `LDA2LAS` a `LAS/`; comprueba que conserva el número de puntos.
   Reutiliza una conversión sólo si las huellas SHA-256 del original y del LAS coinciden
   con su recibo. Los derivados sin recibo se regeneran; los originales se conservan.
4. Para cada parcela, construye un MDT común con todos los LAS vecinos y **clase 2**.
   El MDT FUSION se mantiene en formato PLANS y se convierte a ASCII para verificar
   ausencia de NoData en el círculo y un margen de interpolación.
5. `ClipData` recorta el círculo y lo normaliza con `/dtm` y `/height`. Conserva además
   el recorte con cotas originales. Comprueba igual número de puntos antes/después.
6. `CloudMetrics /new` calcula métricas completas sobre todos los retornos normalizados.
   No aplica filtros de altura, clase ni primer retorno sin una decisión del usuario.
7. Exporta CSV y GeoPackage **por ID**, además de archivos conjuntos y un registro.

```text
C:\InventarioLidar\
  originales\<sec>\<name>        # nunca se modifica ni elimina
  LAS\<sec>_<nombre>.las         # caché de conversión con recibo SHA-256
  resultados\<fechaUTC>_<azar>\
    proceso.log                  # comandos, salida FUSION, errores y cancelación
    estado.json                  # estado final y asociación ID/directorio
    teselas.json                 # procedencia sin enlaces temporales
    descargas_pendientes.json    # cuando procede
    metricas.csv
    metricas.gpkg                # centros, una entidad por ID, CRS UTM
    <hash-del-ID>\
      teselas.txt
      mdt.dtm / mdt.asc
      original.las / normalizada.las
      cloudmetrics.csv           # salida nativa intacta
      metricas.csv / metricas.gpkg
```

El ID se conserva literalmente como texto, incluidos ceros iniciales. Los directorios
usan una huella para admitir IDs con caracteres no válidos en Windows; la correspondencia
está en `estado.json`. Los campos `cm_` conservan las columnas FUSION como texto para
no perder diagnósticos ni representaciones originales; conviértalos a numérico cuando
prepare la fase de modelización. El GeoPackage representa centros, no polígonos de parcela.

La cobertura de huellas no garantiza densidad uniforme, ausencia de agua, calidad de
clasificación ni completitud de adquisición. El control del MDT y el recuento detectan
algunos problemas adicionales, pero no sustituyen una validación científica de datos.

## Desarrollo y publicación

```sh
python -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen /usr/bin/python3 -m unittest discover -s tests -v
python tools/build.py
```

El primer comando omite las pruebas QGIS si no está instalado en ese intérprete.
El segundo usa la instalación QGIS/GDAL del sistema Linux. En Windows use el intérprete
Python del entorno QGIS/OSGeo4W. Para ejecutar FUSION realmente:

```powershell
python tools/windows_smoke.py C:/lidar_smoke_nuevo
```

El smoke test genera cuatro teselas artificiales y verifica alturas conocidas de 0 y
10 m, número de puntos y exportación. Necesita carpeta vacía y FUSION. **No se ha
ejecutado en Windows durante esta entrega.** No prueba descarga real de CNIG.

La acción GitHub de la rama experimental ejecuta pruebas portables, crea el ZIP y
publica una prerelease con el activo ZIP y su SHA-256. La prueba QGIS se ejecuta aparte
en esta entrega; no se sustituye por los tests portables de CI.

Licencia GPL-3.0 del repositorio. Atribuya CNIG conforme a la licencia del producto de
entrada; registre año y nivel NPC utilizados. Consulte [fuentes y parámetros](docs/FUENTES.md).
