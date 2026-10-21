# Modelización forestal LiDAR QGIS 0.3.1 experimental

Añade al diálogo, después de Altura dominante, Fracción de cabida cubierta (%)
y Diámetro medio (cm). Columnas predeterminadas FCC_pct y D_medio_cm.
Se modelizan como respuestas de campo, con ecuaciones, validación y predicciones.
No son predictores obligatorios para los modelos de volumen o área basal.

Cada respuesta puede dejarse en (no modelizar). Un CSV antiguo sin las nuevas
columnas funciona igual, sin seleccionar el ID u otra columna como sustitución.
La plantilla incluye las seis respuestas; el CLI conserva cuatro por defecto.
Se mantienen el mínimo de 8 parcelas y el mínimo inicial de 2 métricas por ecuación.

Instale el ZIP sin descomprimir, reinicie QGIS y compruebe versión 0.3.1.
Seleccione FCC_pct y D_medio_cm de campo; use porcentaje 0–100 y diámetro en cm.
Los nombres y unidades de columnas deben conservarse al aplicar modelos guardados.
Véase VALIDACION.md: pruebas de motor y GUI ejecutadas en Linux; pendiente QGIS Windows.

Ejecutadas 44 pruebas locales: 32 portables y 12 con QGIS 3.40.6 en Linux.
Los resultados sintéticos no validan modelos forestales con datos reales.
