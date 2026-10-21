# Inventario forestal LiDAR — 0.4.5 experimental

**Entrada normal: capa de centros de parcelas, ID único, radio y carpeta de trabajo.
El plugin consulta CNIG, descarga los LAZ y continúa con LAS/FUSION. No pide CSV ni
seleccionar archivos LAZ/LAS.** La modelización estadística queda para otra fase.

## Novedades 0.4.5: cobertura y capas multipunto

Se admiten Point y MultiPoint, también con Z/M. Un MultiPoint con un solo centro
por entidad conserva su ID y no requiere conversión previa. Para entidades con
varios centros, active **Separar multipuntos con varios centros**: se crea una
parcela por punto con IDs `<ID>__p1`, `<ID>__p2`, etc., en el orden de los vértices.
La capa original no cambia. `parcelas_entrada.json` documenta el ID original,
ID de entidad y número de parte. Se rechazan colisiones de IDs generados,
IDs de origen repetidos/nulos/vacíos y geometrías vacías o no puntuales, con
identificación de la entidad. No se elige un centro ni un centroide arbitrariamente.
Se mantienen los requisitos de CRS UTM, ID único y coordenadas finitas.

El CSV y los GeoPackage incluyen estas columnas nuevas, sin cambiar las `cm_`:

| Columna | Significado |
| --- | --- |
| `n_primeros_retornos` | Todos los puntos con número de retorno 1 de la parcela; incluye suelo clase 2 y alturas negativas/cero. |
| `n_primeros_retornos_sobre_corte` | Primeros retornos cuya altura normalizada es estrictamente superior al umbral. |
| `altura_cobertura_m` | Umbral utilizado; corte activo de métricas, o 2 m si se desactiva el filtro. |
| `cobertura_primeros_retornos_pct` | 100 × primeros retornos sobre el umbral / primeros retornos totales. |
| `estado_cobertura` | `ok` o `sin_primeros_retornos`. |

El recuento se realiza sobre **normalizada.las completa**, antes de ejecutar
CloudMetrics `/minht`, sin filtrar por clase, orden de eco o flags de clasificación.
No se cuentan los segundos o posteriores retornos como primeros. Se soportan los
formatos LAS 0–10 con sus campos de orden de retorno de 3/4 bits. La lectura es por
bloques cancelables y utiliza los reintentos de acceso existentes. No requiere laspy.
Si el denominador es cero, el porcentaje queda vacío en CSV y NULL en GPKG, y se
registra un aviso: no se sustituye por una cobertura del 0 %. El 0 % con primeros
retornos válidos sí es un resultado posible. El detalle está en
`<hash-del-ID>/cobertura_retornos.json` y en el registro.

Es un **indicador LiDAR de cobertura**, no una medición idéntica a la FCC arbolada
de campo; puede incluir matorral que supere el umbral y depende del vuelo. Se conservan
todos los primeros retornos presentes en el recorte, incluidos los de suelo, sin
aplicar filtros adicionales de clase. Para calibrar/aplicar modelos use siempre
igual umbral y protocolo. No se obliga todavía al plugin de modelización a usar
esta columna: ese cambio sería independiente.

Actualice con el ZIP **0.4.5**, reinicie QGIS y use la misma carpeta. Se reutilizan
LAZ/LAS verificados; las parcelas se recalculan en una nueva carpeta de resultados.
No se añaden columnas a resultados históricos ni se requiere volver a descargar.

## Novedad 0.4.4: MDT desde un entorno recortado conjunto

GridSurfaceCreate recibe ahora una única nube `entorno_mdt.las`, creada con
ClipData /shape:0 a partir de TODAS las teselas seleccionadas para la parcela.
El margen por lado es 2 × celda MDT + distancia máxima sin apoyo (7 m con valores
predeterminados). Se conserva la cota absoluta y la clasificación de los puntos.
GridSurfaceCreate sigue usando /class:2. El recorte circular y la normalización
usan también el entorno, evitando releer las teselas completas en cada fase.

Se conservan las comprobaciones de apoyo de puntos y de suelo, cobertura CNIG,
y ausencia de huecos del MDT en el círculo y su halo. No se rellena un MDT inválido
ni se descarta la tesela vecina de una parcela entre teselas. `entorno_mdt.json`
registra las entradas, margen y recuento. Se conserva el corte configurable de 0.4.3.

Motivo: cierre de GridSurfaceCreate64 con 0xC0000409 durante la lectura directa de
una lista de dos teselas completas. No se ha confirmado la causa interna. Este
cambio evita esa entrada y reduce el tamaño del cálculo; no garantiza resolver
cualquier fallo del ejecutable o de una unidad de red. Si persiste, conserve
proceso.log, fusion.log y entorno_mdt.json para el diagnóstico.

Instale el ZIP 0.4.4 y reinicie QGIS. Reutilice la misma carpeta sin borrar originales
ni LAS. Obtendrá una nueva carpeta de resultados. Pendiente: probar FUSION real
en Windows con el caso que produjo el cierre.

## Novedad 0.4.3: altura de corte configurable

La opción **Aplicar altura de corte a las métricas**, activada inicialmente,
usa **2 m** por defecto. Puede elegir otro valor (incluido 0 m) o desactivar
la casilla para incluir todos los retornos. Un corte de 0 m sigue excluyendo
alturas no superiores a cero; no equivale a desactivar el filtro.

El corte se aplica a alturas ya normalizadas mediante **CloudMetrics /minht:h**.
No se aplica al MDT de clase 2 ni elimina puntos de los archivos originales,
LAS convertidos o normalizada.las. No se confunde con /above (cobertura).
Se mantiene el prefijo de métricas `cm_` para el programa de modelización.

CSV y GeoPackage incorporan `altura_corte_m` (vacío/NULL si no se filtra),
`filtro_altura` (mayor_que/sin_filtro) y `n_puntos_metricas` (retornos usados).
`n_puntos` conserva el total de la nube circular normalizada. CloudMetrics
conserva sus nombres originales de columnas, incluidos los recuentos filtrados.
El comando y el filtro se guardan en proceso.log y estado.json.
Sin retornos por encima del corte, se detiene indicando el ID; no se inventan
estadísticas ni se eliminan parcelas silenciosamente.

Para actualizar: instale **inventario_forestal_lidar-0.4.3-experimental.zip**,
reinicie QGIS, seleccione la misma carpeta de trabajo y el corte deseado y
pulse Ejecutar/reanudar. Reutiliza LAZ/LAS verificados; calcula de nuevo las
parcelas en una nueva carpeta de resultados. No borre los originales ni
mezcle resultados con cortes distintos para calibrar modelos.

La opción está diseñada con el manual oficial FUSION 4.61, CloudMetrics,
páginas impresas 49–53: [manual oficial](https://forsys.sefs.uw.edu/software/fusion/FUSION_manual.pdf).

## Corrección 0.4.2: lectura LAS y conservación del error original

El último registro recibido muestra dos errores: primero `[Errno 22] Invalid argument`
durante la comprobación de cobertura; después un fallo al guardar `estado.json.tmp`.
En 0.4.1 el guardado final podía ocultar el error inicial. Las conversiones LAS del
registro habían terminado y estaban verificadas. No se afirma que el origen sea
una desconexión, permisos, FUSION o una tesela concreta: el registro anterior no
identifica la operación de lectura exacta.

Ahora la comprobación lee los LAS sin búfer Python, en bloques de puntos de hasta
1 MiB. Ante un error transitorio o errno 22, reabre el archivo y reintenta **el mismo
rango de bytes**, como máximo tres veces adicionales. Una lectura parcial fallida
se descarta y se vuelve a leer; no se duplican ni saltan puntos. También se reintenta
la lectura de metadatos. Si persiste, el error informa del archivo y, para los bloques
de puntos, del byte y tamaño solicitados; el registro incluye el traceback de cobertura.
Se indica el LAS que se está comprobando y el progreso de lectura.
Esta medida de compatibilidad necesita comprobación con su unidad Q:; no garantiza
que una carpeta o archivo no disponible pueda leerse.

La escritura JSON usa temporales únicos junto al destino, conserva el JSON anterior
hasta completar el reemplazo y reintenta sólo fallos transitorios, con pausas de
0,2/0,5/1 s. WinError 5 también se reintenta de forma acotada porque Windows puede
producirlo durante un reemplazo concurrente. Si la denegación persiste se informa;
no se cambian permisos. **No recrea una carpeta de red desaparecida ni omite la cobertura.**
Si el guardado del estado sigue fallando, se detiene con un diagnóstico alternativo.
Al finalizar, un fallo de guardado no sustituye el error inicial, la cancelación o
la autorización pendiente. Si el cálculo terminó pero no se pudo confirmar el estado,
se informa expresamente de ello en vez de anunciar un éxito completo.

Diagnóstico alternativo en Windows:

```text
%LOCALAPPDATA%\InventarioForestalLiDAR\diagnosticos\<ejecución>\estado.json
%LOCALAPPDATA%\InventarioForestalLiDAR\diagnosticos\<ejecución>\proceso.log
```

El registro alternativo sólo recoge mensajes posteriores al fallo de escritura;
no se promete una copia del historial de red. Si falta LOCALAPPDATA se usa TEMP.
La ventana muestra las rutas que se hayan podido guardar. Si también falla ese
almacenamiento, se conserva el error original en el mensaje; no se promete un respaldo.

**Actualizar y reanudar:** instale el ZIP 0.4.2, reinicie QGIS y use la misma carpeta.
No borre `originales/`, `LAS/` ni sus recibos JSON: los archivos completos verificados
se reutilizan. Si Q: no está disponible de forma estable, espere a recuperarla o haga
una **copia**, sin mover los originales, de `originales/` y `LAS/` con sus recibos a una
carpeta local sin espacios y selecciónela como carpeta de trabajo. La disponibilidad
de espacio y los permisos deben permitir leer y escribir; el plugin no los cambia.

## Compatibilidad incorporada en 0.4.1: arranque de FUSION y diagnóstico por fase

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

**Reanudar:** instale el ZIP 0.4.2 y reinicie QGIS. Use la misma carpeta de trabajo
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
4. Descargue `inventario_forestal_lidar-0.4.5-experimental.zip`. En QGIS:
   **Complementos → Administrar e instalar complementos → Instalar a partir de ZIP**.
   Instale sin descomprimir y **reinicie QGIS** para retirar el código de la versión anterior.
5. La ventana debe indicar **Experimental 0.4.5**, sin campo de CSV ni selector de nubes.

FUSION no está incluido en el ZIP. Numpy, GDAL y Qt se utilizan desde QGIS.

## Uso

1. Cargue una capa Point/MultiPoint. Si hay varios centros en una entidad, active la separación explícita. Seleccione un campo ID
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
    parcelas_entrada.json            # ID original y partes; entradas desde la interfaz
    estado.json / proceso.log
    metricas.csv / metricas.gpkg
    <hash-del-ID>/
      cobertura.json / teselas.txt
      mdt.dtm / mdt.asc
      original.las / normalizada.las
      cobertura_retornos.json        # primeros retornos antes del filtro de altura
      cloudmetrics.csv
      metricas.csv / metricas.gpkg
```

El ID se conserva como texto, incluidos ceros iniciales. Los directorios usan un hash
para admitir IDs no válidos como nombres Windows; `estado.json` guarda la correspondencia.
El GeoPackage contiene centros en el CRS UTM de entrada. Las columnas `cm_` conservan
como texto los valores/diagnósticos FUSION. El corte configurable afecta a las métricas
CloudMetrics. La cobertura tiene su propio denominador completo antes del filtro.

El registro incluye consulta, carpetas vigiladas, incorporación, reutilización,
comandos FUSION, errores y cancelación. Las teselas completas se conservan; `.part`
y `.crdownload` no se tratan como originales. Cada ejecución recalcula métricas y
reutiliza conversiones verificadas.

## Verificación y límites de la versión experimental

**Ejecutado en 0.4.5:** 104 pruebas aprobadas en Linux/QGIS 3.40.6, incluidas
Point/MultiPoint, formatos LAS 0–10, suelo, igualdad al umbral, cancelación,
cobertura NULL y exportación CSV/GPKG. Con Python sin QGIS: 89 aprobadas, 15
omitidas. El flujo FUSION está simulado; no se ejecutaron sus binarios Windows.
Véase el protocolo de 0.4.5 en VALIDACION.md.

**Histórico 0.4.2:** 83 pruebas aprobadas en Linux/QGIS 3.40.6. Incluyen vigilancia,
archivos parciales, nombres, copia, cancelación y flujo hasta GeoPackage con descarga
humana simulada y FUSION sustituido. Con Python sin QGIS: 73 aprobadas y 10 omitidas.
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
