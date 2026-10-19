Script independiente: ecuaciones forestales con métricas LiDAR, 0.1.0 experimental.

Descomprima el ZIP y siga README.md; no es un ZIP instalable como plugin QGIS.
Entradas: CSV de campo con ID,V_ha,G_ha,N_ha,Hdom y CSV de métricas del plugin.
Incluye generador de plantilla con los IDs del LiDAR y ejemplos artificiales.

Ajusta ecuaciones lineales/potenciales por respuesta. Selecciona métricas y familia
dentro de validación cruzada anidada, opcionalmente por grupos. Evalúa RMSE, sesgo,
porcentajes, MAE y R² en unidades originales. Criterio configurable de RMSE/|sesgo|,
control de complejidad, VIF, colinealidad y corrección de retransformación.
Exporta ecuaciones, coeficientes JSON, validación por parcela, rankings y gráficos;
aplica modelos a métricas nuevas con avisos de extrapolación y dominio no válido.

17 pruebas locales Linux aprobadas; publicación condicionada a pruebas y ensayo
sintético en Ubuntu y Windows de GitHub Actions. Pendiente: instalación y calibración
con datos reales del usuario. Los ejemplos y ecuaciones incluidos son sintéticos.
Dos parcelas no bastan; mínimo operativo por defecto 20 válidas por respuesta,
sin considerarlo una garantía de suficiencia. El plugin QGIS permanece sin cambios.
