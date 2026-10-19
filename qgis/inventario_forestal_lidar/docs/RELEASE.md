0.3.2 experimental: utiliza Google Chrome para la descarga oficial CNIG.

Corrige la selección que abría Edge aunque hubiera Chrome instalado en otra ubicación.
Busca instalaciones de Chrome de equipo/usuario y PATH; si no existe, informa y no
cambia automáticamente a Edge. Se mantiene la autorización oficial y la recogida
automática del archivo. Instale el ZIP sin descomprimir y reinicie QGIS.

Las descargas automáticas van a <carpeta de trabajo>/originales/<sec>/. Si descargó
por su cuenta en otra ventana, puede dejar el LAZ con su nombre original en
<carpeta de trabajo>/originales/ y volver a ejecutar, sin seleccionarlo manualmente.

48 pruebas Linux/QGIS aprobadas, incluidas selección de navegador y tres con Chromium
real contra servidor local. Pendiente: validar Chrome/CNIG y FUSION reales en Windows.
La corrección de nombres PNR sin Hxx de 0.3.1 se conserva.
