# PNOA3 LiDAR para QGIS 3

Plugin independiente de NDVI Sentinel. Busca únicamente la serie oficial
**LIDA3: tercera cobertura LiDAR del PNOA** del Centro de Descargas del CNIG.

## Instalación y uso

1. Instala `pnoa3_lidar_v0.1.0.zip` desde el administrador de complementos,
   opción **Instalar a partir de ZIP**.
2. Pulsa el botón **Descargar PNOA3 en un punto** y haz clic en el mapa.
3. Elige la carpeta donde tu navegador va a guardar el archivo. Normalmente
   es **Descargas**. Si el navegador pregunta dónde guardarlo, usa esa carpeta.
4. El plugin consulta el catálogo CNIG. Si hay varias teselas coincidentes,
   permite elegir; si no hay tercera cobertura, lo indica sin usar otra.
5. Se abre la ficha oficial en el navegador. Pulsa **Descargar**, completa
   la autorización/reCAPTCHA y acepta las condiciones que muestre el CNIG.
6. QGIS detecta el LAS/LAZ terminado y lo añade al proyecto como nube de puntos.
   Puede necesitar tiempo adicional para generar su índice de visualización.

**La descarga no es completamente automática:** el portal exige autorización
de navegador. El complemento no la omite. La localización de tesela y la carga
del archivo descargado sí se automatizan. No convierte LAZ a LAS: QGIS lee LAZ.

La espera caduca al cabo de una hora. Puedes cancelar la vigilancia pulsando
otra vez el botón del plugin o desactivando el complemento. No cancela una
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
