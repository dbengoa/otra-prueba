# PNOA3 LiDAR para QGIS 3

Plugin independiente de NDVI Sentinel. Busca únicamente la serie oficial
**LIDA3: tercera cobertura LiDAR del PNOA** del Centro de Descargas del CNIG.

## Instalación y uso

1. Instala `pnoa3_lidar_v0.2.3.zip` desde el administrador de complementos,
   opción **Instalar a partir de ZIP**.
2. Pulsa el botón **Descargar PNOA3 en un punto** y haz clic en el mapa.
3. Elige la carpeta donde tu navegador va a guardar el archivo. Normalmente
   es **Descargas**. Si el navegador pregunta dónde guardarlo, usa esa carpeta.
4. El plugin consulta el catálogo CNIG. Si hay varias teselas coincidentes,
   permite elegir; si no hay tercera cobertura, lo indica sin usar otra.
5. Se abre la ficha oficial en el navegador. Pulsa **Descargar**, completa
   la autorización/reCAPTCHA y acepta las condiciones que muestre el CNIG.
6. QGIS detecta la descarga terminada, convierte LAZ a LAS y añade el LAS como nube de puntos.
   Puede necesitar tiempo adicional para generar su índice de visualización.

**La descarga no es completamente automática:** el portal exige autorización
de navegador. El complemento no la omite. La localización de tesela y la carga
del archivo descargado sí se automatizan. Convierte LAZ a LAS con LASzip antes de cargarlo.

La espera caduca al cabo de una hora. La vigilancia continúa aunque cambies de herramienta o desmarques el botón.
Se cancela al desactivar el complemento en el administrador. No cancela una
descarga que ya esté haciendo el navegador. No borra archivos del usuario.
Si la tesela ya existe, puedes cargarla directamente sin descargarla otra vez.

## Requisitos

- QGIS 3.22 o posterior de la serie 3, con proveedor **PDAL** para LAS/LAZ.
  El plugin informa si la distribución de QGIS no incluye ese proveedor.
- Internet hacia el CNIG y los servicios que su página necesite para autorizar
  la descarga en el navegador.
- Espacio suficiente para la tesela y para el índice que genere QGIS.

## Verificación y límites

Se verificó la consulta real del catálogo: responde a coordenadas geográficas
WGS84 y permite localizar una tesela de la tercera cobertura. El formato del
formulario web puede cambiar; se detectan respuestas incompatibles y se
reporta el error en vez de inventar enlaces. El módulo de descarga directa
se probó con un servidor local, pero no se usa para omitir la autorización.

La distribución QGIS 3.40 del entorno de desarrollo no incluye PDAL. Por ello
la apertura de un LAS/LAZ real y una descarga autorizada desde el navegador
de un usuario siguen pendientes de validación. El instalador y el flujo GUI
se comprueban con fixtures y una llamada de carga controlada en las pruebas.

## Cambios de 0.1.1

Vigila tanto la carpeta elegida como Descargas y mantiene la espera al desmarcar
la herramienta. En Complementos → PNOA3 LiDAR → Cargar LAS/LAZ ya descargado
puedes seleccionar un archivo existente. Los errores de carga se muestran
en un cuadro de diálogo, incluyendo la ausencia del proveedor PDAL.

## Conversión automática en 0.1.2

Tras detectar un LAZ terminado, convierte a LAS con LASzip y carga el LAS.
La primera vez selecciona `bin/laszip64.exe` del paquete LAStools descargado;
la ruta queda guardada. No selecciones una DLL. La conversión funciona en
segundo plano y puede cancelarse desde el gestor de tareas de QGIS.
Conserva el LAZ y escribe el LAS en la subcarpeta `LAS`. Si ya existe un LAS,
crea otro nombre con `_convertido_N` sin sobrescribirlo. El LAS ocupa más
espacio. Esta configuración requiere disponer del ejecutable de LASzip.
Para SilviLiDAR, copia únicamente el LAS completo a una carpeta de trabajo
separada: el plugin busca tanto LAS como LAZ e incluye archivos intermedios.
La conversión no cambia el sistema de coordenadas ni filtra puntos.

Se verificaron tareas asíncronas de QGIS, cancelación, colisiones y errores
con un ejecutable de prueba. La conversión con LASzip real y la carga PDAL
requieren validación en Windows; no están disponibles en este entorno.

## Cambios en 0.1.3

Configura LASzip antes de abrir la descarga del navegador y muestra las
carpetas vigiladas. Acepta guiones o guiones bajos en el nombre de la misma
tesela. Añade Configurar LASzip y renombra el acceso manual como
Convertir LAZ a LAS y cargar archivo. Cancelar la configuración muestra
un aviso explícito. La activación identifica la versión 0.1.3.

## Selección por polígono — 0.2.0

1. En Complementos → PNOA3 LiDAR, elige **Dibujar polígono y descargar teselas**.
2. Añade vértices con clic izquierdo. Termina con clic derecho tras al menos
   tres vértices. Escape borra el dibujo. Evita polígonos que se cruzan.
3. Configura `laszip64.exe` si aún no está guardado. Escribe el nombre de una
   carpeta nueva, sin espacios, dentro de `C:\`, por ejemplo `PNOA_Zona1`.
   La función de crear carpetas en C está disponible en Windows. Si Windows
   deniega escritura, se informa del error; no se elevan permisos ni se reutiliza
   una carpeta existente.
4. Se consultan todas las páginas del catálogo oficial LIDA3. Se incluyen las
   teselas completas que intersectan el polígono, no solo las totalmente dentro.
   No recorta la nube por el polígono y no usa otras coberturas como alternativa.
5. La ventana muestra todas las teselas. Selecciona una y pulsa **Abrir ficha
   CNIG**. Descarga el LAZ/LAS desde esa ficha y guárdalo en la carpeta creada.
   Repite con las demás teselas. El CNIG puede pedir condiciones y reCAPTCHA;
   no se automatiza ni se omite esa autorización. No es una descarga masiva
   completamente desatendida.
6. Mantén la ventana de cola abierta. Detecta archivos terminados, convierte
   los LAZ a LAS secuencialmente en la subcarpeta `LAS` y carga cada LAS al
   proyecto. Los estados de la tabla indican conversión, carga o error. Cerrar
   la ventana cancela la cola y la conversión activa; el navegador puede seguir
   descargando. Las teselas terminadas y los LAZ originales se conservan.

La selección debe tener cobertura publicada. Una carpeta sin resultados queda
vacía si no hay teselas o falla la consulta. Para SilviLiDAR usa otra carpeta
con solo los LAS completos: esta carpeta conserva también los LAZ.

Se comprobó una consulta real por polígono al CNIG (dos teselas), paginación
con respuestas de prueba y la cola asíncrona de dos archivos en QGIS real con
un ejecutable conversor de prueba. La creación bajo C, LASzip real, autorización
en navegador y lectura final PDAL requieren validación en Windows.

## Diagnóstico y recuperación — 0.2.1

La cola muestra cuántos archivos reconoce en la carpeta y añade Comprobar
ahora los archivos descargados. Normaliza guiones y guiones bajos en los
nombres y conserva la espera para archivos temporales e inestables.
En Complementos → PNOA3 LiDAR → Convertir todos los LAZ de una carpeta
puedes procesar una carpeta existente sin dibujar o descargar de nuevo.
Selecciona LASzip si lo pide. Mantén la cola abierta. No espera a que se hayan
descargado todas las teselas antes de convertir las que ya estén completas.
Se comprobó el temporizador real de Qt y los nombres con separadores mixtos
con un conversor de prueba; la causa concreta del fallo reportado en Windows
no se ha reproducido en el entorno de desarrollo.

## Corrección de cierre — 0.2.2

La X y Escape cierran correctamente la ventana de cola. Al cerrarla se detiene
la vigilancia y se cancela la conversión activa, conservando los archivos
completos. Se elimina la llamada circular entre reject() y close().
Se renombra el callback de teselas para no sobrescribir QDialog.done().
Verificado con Qt real: X, Escape y reject(), con cola pendiente, terminada
y conversión activa (nueve casos).

## Salida en subcarpeta LAS — 0.2.3

Todas las conversiones guardan su resultado en una subcarpeta `LAS` junto
al archivo original. Se crea automáticamente y QGIS carga el resultado desde
ella. Los archivos originales se conservan. Si el nombre ya existe, se usa
`_convertido_N` sin sobrescribirlo.
