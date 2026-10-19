# Inventario forestal LiDAR — 0.4.1 experimental

**Entrada normal: capa de centros de parcelas, ID único, radio y carpeta de trabajo.
El plugin consulta CNIG, descarga los LAZ y continúa con LAS/FUSION. No pide CSV ni
seleccionar archivos LAZ/LAS.** La modelización estadística queda para otra fase.

## Corrección 0.4.1: arranque de FUSION y diagnóstico por fase

El registro real recibido confirma conversión completa de ambas teselas, MDT y
DTM2ASCII correctos. ClipData de 32 bits termina con 3221225477 (0xC0000005) antes de
imprimir su cabecera. CloudMetrics no había comenzado. No se atribuye todavía la
causa a memoria insuficiente, permisos de Q:, datos ni una DLL concreta.

Esta versión prefiere `ClipData64.exe` y las otras variantes `*64.exe` que estén
instaladas. Si sólo hay ejecutables de 32 bits, lo registra y mantiene compatibilidad.
Para LDA2LAS conserva la pareja de 32 bits si existe LASzip.dll y falta LASzip64.dll.
El nombre del ejecutable seleccionado se muestra al empezar. No instala ni sustituye
FUSION o sus bibliotecas.

En Windows se prueba `ClipData /version` antes de descargar o convertir. Cada proceso
arranca desde la carpeta de su ejecutable y usa `/log:<resultados>/fusion.log` en vez
del registro compartido de C:\FUSION. No hereda los ajustes FUSION64/NOLASZIPDLL de
QGIS; se conservan las demás variables. El cambio sólo afecta al proceso hijo.
La selección de 64 bits y el arranque controlado son medidas de compatibilidad:
**no está confirmado que resuelvan el fallo real comunicado**.

Se informa cada LAS convertido/reutilizado, ruta y número de puntos. La conversión
es por tesela, no por parcela. El estado guarda la correspondencia nombre original →
LAS. En el caso comunicado, la segunda tesela está en
`LAS/7edad52739038a39f70159cf.las`; la primera en `LAS/0cb3bff22fa084fd6f06647a.las`.
La tabla por parcela empieza cuando todas las conversiones han sido verificadas.
Se distingue MDT, recorte, normalización, CloudMetrics y exportación. Hay un aviso
cada diez segundos mientras un ejecutable continúa y los fallos muestran fase,
parcela y código. Un aviso de actividad no garantiza que el ejecutable avance;
se puede cancelar. No se inventan métricas cuando ClipData falla.

**Reanudar:** instale el ZIP 0.4.1 y reinicie QGIS. Use la misma carpeta de trabajo
para aprovechar los LAZ y LAS existentes; no borre originales ni conversiones.
Si vuelve a fallar, el diagnóstico necesario está en `proceso.log`, `fusion.log`
(si el programa pudo crearlo) y `estado.json`, dentro de la nueva ejecución.
Compruebe en C:\FUSION si está instalado ClipData64.exe con sus dependencias oficiales.
No se recomienda desactivar antivirus ni cambiar permisos de la unidad de red.

## Descarga: Chrome normal y clic humano

El plugin abre la ficha oficial en su sesión habitual de Google Chrome. Usted pulsa
**Descargar** y completa CAPTCHA/licencia si CNIG los solicita. El plugin detecta el
archivo terminado y continúa automáticamente. Cada tesela pendiente puede requerir
un clic. No abre Edge ni un navegador controlado mediante depuración.

**¿Dónde guardar?** En la carpeta indicada en **Descargas de Chrome**. Se inicializa
con la carpeta Descargas de Windows, incluso si está reubicada. Si Chrome guarda en
otra carpeta, selecciónela en ese campo antes de ejecutar; puede contener espacios.
No cambie el nombre de la tesela. Se admiten guiones/guiones bajos y sufijos `(1)`.
El plugin copia cada archivo completo a `<carpeta de trabajo>/originales/<sec>/`,
conservando también el archivo de Descargas. Para su configuración la copia quedará
en `Q:\LIDAR\prueba2total\originales\<sec>\`.
También vigila `originales/` y la subcarpeta de la tesela si prefiere guardar allí.
No tiene que seleccionar archivos LAZ/LAS ni pulsar otro botón después de descargarlos.

## Corrección 0.3.1

Admite nombres sin huso, como `PNOA-2024-PNR-523-4654-NPC01.laz`. La ausencia de
`Hxx` no declara ningún CRS: se mantienen las comprobaciones de huella oficial y
metadatos del LAZ. Las variantes con/sin huso se comparan como ediciones de la misma
tesela, sin mezclar niveles NPC ni admitir husos explícitamente incompatibles.

## Instalación / actualización

1. Instale QGIS 3.34 o posterior para Windows, preferiblemente 3.40 LTR.
2. Instale FUSION 4.61 y sus bibliotecas LAZ en `C:\FUSION`.
3. Tenga instalado Google Chrome. Se necesita para ejecutar la
   autorización oficial de CNIG, incluido reCAPTCHA. No se requieren extensiones,
   Selenium, laspy ni paquetes Python adicionales.
4. Descargue `inventario_forestal_lidar-0.4.1-experimental.zip`. En QGIS:
   **Complementos → Administrar e instalar complementos → Instalar a partir de ZIP**.
   Instale sin descomprimir y **reinicie QGIS** para retirar el código de la versión anterior.
5. La ventana debe indicar **Experimental 0.4.1**, sin campo de CSV ni selector de nubes.

FUSION no está incluido en el ZIP. Numpy, GDAL y Qt se utilizan desde QGIS.

## Uso

1. Cargue la capa de puntos simples: un centro por parcela. Seleccione un campo ID
   único y no nulo. Se procesan todas las entidades, no sólo la selección.
2. La capa debe estar en el CRS UTM de las teselas: ETRS89 EPSG:25828–25831 o REGCAN95
   EPSG:4083. Reproyecte los centros antes si hace falta. No se reproyectan las nubes.
3. Radio predeterminado: **15 m**. Carpeta absoluta sin espacios, por ejemplo
   `Q:\LIDAR\prueba2total`. Deje FUSION en `C:\FUSION` si ésa es su instalación.
4. Revise **Descargas de Chrome**: debe coincidir con la carpeta donde Chrome guarda
   los archivos. Pulse **Ejecutar / reanudar**. Se consultan PNOA3 y sus huellas.
5. En cada ficha que se abre en **Chrome normal**, pulse **Descargar** y complete
   cualquier autorización oficial. Si aparece «Guardar como», use la carpeta indicada
   en QGIS, manteniendo el nombre. Espere a que termine la transferencia.
6. El plugin reconoce la tesela, espera a que esté estable y sin `.crdownload`, valida
   la cabecera y la copia a `originales/<sec>/`. Continúa con LAS, MDT, recortes
   normalizados, CloudMetrics y CSV/GeoPackage automáticamente.

**Volver a abrir ficha** sólo abre otra vez la ficha oficial; no activa la descarga.
Chrome permanece abierto al terminar o cancelar. Cancelar detiene la espera y FUSION,
pero no las descargas del navegador: puede dejarlas terminar y reanudar el plugin.
No se leen cookies, preferencias ni credenciales de Chrome.

**La autorización la decide CNIG.** El 403 comunicado correspondía a `descargaDir`,
una ruta de formulario, no un enlace directo reutilizable. El portal comprueba si el
navegador está automatizado. Esta versión retira CDP y los clics programados; no altera
sus controles. No se garantiza que CNIG conceda autorización en cada equipo.
La espera máxima es de una hora por tesela; al expirar se conserva lo descargado.

## Flujo automático implementado

1. Transforma a longitud/latitud una envolvente densificada de cada círculo, con margen.
   Consulta `archivosSerie` por **POST**, con `codAgr=MOMDT` y `codSerie=LIDA3`.
2. Interpreta todas las páginas, comprueba el total y deduplica por identificador `sec`.
   Si el portal cambia el HTML o repite páginas, falla explícitamente; no lo interpreta
   como «sin cobertura». No recurre a un CSV o selección manual.
3. Elige para cada tesela el vuelo más reciente y, dentro de ese año, el mayor nivel
   NPC (03 > 02+ > 02 > 01). Registra las alternativas descartadas. Dos candidatos
   indistinguibles en año/nivel provocan error en lugar de mezclarse. El huso debe
   coincidir con los centros. La nomenclatura sólo se usa para comparar ediciones,
   **no para fabricar la huella espacial**.
4. Obtiene las geometrías oficiales con `localizarCoordsSec`, las reproyecta y comprueba
   su unión para cada círculo y dos celdas de margen. Incluye parcelas entre teselas y
   esquinas de cuatro teselas. Tolera **2 cm** en límites: las huellas verificadas del
   servicio terminan a 0,01 m de la siguiente tesela. Rechaza superficie restante sin
   cobertura superior a 0,01 m²; no exporta métricas de cobertura parcial.
5. Abre la ficha oficial de cada tesela en Chrome habitual y espera el clic humano.
   El navegador ejecuta el flujo oficial de CNIG sin intervención programada.
6. Vigila sólo las carpetas indicadas, sin recorrido recursivo. Acepta el nombre esperado
   (guiones/guiones bajos y sufijo de duplicado), ignora temporales, enlaces simbólicos
   y archivos ajenos. Exige tamaño/fecha estables durante dos segundos y cabecera válida.
   Copia por bloques cancelables y confirma en la unidad de salida; conserva la fuente.
   Esto comprueba la entrega del archivo, no acredita su procedencia criptográficamente;
   la conversión posterior verifica lectura y número de puntos.
7. Reutiliza originales con cabecera válida y recibo SHA-256. Un original existente sin
   recibo se adopta con validación de cabecera y nueva huella, dejando constancia de ello.
   Se reconocen también originales planos en `originales/`, con guiones o guiones bajos.
   Si el recibo existente no coincide, se detiene y conserva el archivo para revisión.
8. Convierte con `LDA2LAS` a `LAS/`, conserva el número de puntos y reutiliza conversiones
   verificadas por SHA-256. Lee CRS y metadatos de las nubes descargadas; un CRS declarado
   incompatible se rechaza. La casilla de asumir CRS sólo sirve para archivos sin CRS
   cuando usted lo haya comprobado expresamente.
9. Comprueba apoyo de retornos y suelo clase 2 antes del cálculo. Por defecto: muestras
   cada 2,5 m y apoyo a 5 m o menos, también en el margen. Ese control detecta huecos a
   su escala, no certifica ausencia de huecos menores ni calidad de clasificación.
10. Genera MDT común con **clase 2**, comprueba NoData y ejecuta `ClipData /shape:1`
    con `/dtm` y `/height`. Conserva el recorte con cotas originales y exige igual número
    de puntos en el recorte normalizado. Ejecuta `CloudMetrics /new` y exporta por ID.

## Resultados, progreso y cancelación

```text
<carpeta de trabajo>/
  originales/<sec>/<nombre>.LAZ      # original conservado; recibo SHA-256 junto a él
  LAS/<huella>.las y <huella>.json    # conversión reutilizable
  resultados/<fechaUTC>_<azar>/
    catalogo_cnig.json               # candidatos y geometrías oficiales
    plan_cnig.json                   # selección y versiones descartadas
    cobertura_cnig.json              # unión de huellas y parcela/teselas
    archivos_locales.json            # metadatos comprobados de lo descargado
    estado.json / proceso.log
    metricas.csv / metricas.gpkg
    <hash-del-ID>/
      cobertura.json / teselas.txt
      mdt.dtm / mdt.asc
      original.las / normalizada.las
      cloudmetrics.csv
      metricas.csv / metricas.gpkg
```

El ID se conserva como texto, incluidos ceros iniciales. Los directorios usan un hash
para admitir IDs no válidos como nombres Windows; `estado.json` guarda la correspondencia.
El GeoPackage contiene centros en el CRS UTM de entrada. Las columnas `cm_` conservan
como texto los valores/diagnósticos FUSION. No se aplican filtros de altura o primer retorno
sin una decisión posterior de modelización.

El registro incluye consulta, carpetas vigiladas, incorporación, reutilización,
comandos FUSION, errores y cancelación. Las teselas completas se conservan; `.part`
y `.crdownload` no se tratan como originales. Cada ejecución recalcula métricas y
reutiliza conversiones verificadas.

## Verificación y límites de la versión experimental

**Ejecutado en 0.4.1:** 65 pruebas aprobadas en Linux/QGIS 3.40.6. Incluyen vigilancia,
archivos parciales, nombres, copia, cancelación y flujo hasta GeoPackage con descarga
humana simulada y FUSION sustituido. Con Python sin QGIS: 55 aprobadas y 10 omitidas.
La consulta real CNIG y sus huellas se verificaron en versiones anteriores; evidencias
en FUENTES.md. Véase VALIDACION.md para el alcance exacto.

**Pendiente en Windows:** sesión Chrome habitual, clic/autorización y LAZ real CNIG;
carpeta Descargas reubicada, unidades de red y ejecución FUSION real completa.
Los ensayos con fixtures no certifican esos pasos reales.
El adaptador consulta el protocolo web del portal; no es una API pública estable.
La modelización estadística sigue fuera de esta fase.

## Desarrollo

```sh
python -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen /usr/bin/python3 -m unittest discover -s tests -v
python tools/build.py
```

El ZIP es determinista e incluye SHA-256. La CI ejecuta las pruebas portables y
publica una versión experimental con ZIP. Las pruebas de vigilancia usan archivos
sintéticos y el lanzamiento de Chrome se verifica sin automatizar su contenido.

Consulta de diagnóstico de sólo lectura, sin descarga ni FUSION:

```sh
python tools/cnig_probe.py --x 629000 --y 4780000 --epsg 25829 --output carpeta_diagnostico
```

`tools/windows_smoke.py` sigue siendo un ensayo FUSION independiente con LAS sintéticos,
**no una prueba de descarga CNIG**. Para verificar el flujo real, ejecute la interfaz
con parcelas de cobertura PNOA3 conocida y siga el protocolo de VALIDACION.

Licencia GPL-3.0 del repositorio. Datos y huellas CNIG: conserve la atribución según su
licencia, año de vuelo y nivel NPC. FUSION y el navegador no se redistribuyen.
