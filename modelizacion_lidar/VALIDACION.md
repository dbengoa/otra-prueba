# Validación — 19 de octubre de 2026

## Ejecutado localmente en Linux

- 17 pruebas unitarias y de integración aprobadas. Python 3.12.14, NumPy 2.3.5,
  pandas 2.2.3 y matplotlib 3.10.8. Registro: `validacion/pruebas_linux.txt`.
- Recuperación de coeficientes lineales y potenciales en relaciones artificiales sin
  ruido; corrección de retransformación; rechazo de ceros/negativos en potenciales.
- Imputación calculada exclusivamente con datos de entrenamiento; rechazo por VIF.
- Verificación del signo de sesgo, RMSE, IDs/ceros iniciales, colisiones al normalizar,
  coma decimal y cabeceras duplicadas.
- Auditoría de cada llamada a ranking interno y selección externa: los índices
  corresponden sólo a sus entrenamientos; cada parcela se predice una vez por
  repetición externa. Particiones agrupadas sin cruce de grupos.
- Calibración CSV, exportación JSON y aplicación a nuevas métricas, conservando
  entradas y rechazando sobrescribir salidas. Señales de extrapolación, imputación,
  valores negativos y dominio no válido; rechazo de modelos inconsistentes.
- Ensayo completo con 80 parcelas **sintéticas**, cuatro respuestas y opciones por
  defecto, incluidos cuatro gráficos de diagnóstico. Unidades de ejemplo y buenos
  errores no acreditan un modelo forestal real.
- Otro ensayo sintético por grupos, para V_ha y Hdom: 5 folds externos, 4 internos,
  dos repeticiones, 10 bloques artificiales. No es una validación de autocorrelación
  espacial real; los bloques artificiales no son ubicaciones.
- Creación de plantilla a partir del CSV del usuario de dos parcelas, manteniendo
  sus IDs. No se calibraron modelos con ese archivo. No se publica dicho CSV.

Los ejemplos en `validacion/ejemplo_sintetico/` son evidencias de la ejecución local;
se incluye el generador y los CSV artificiales para repetirla. No se distribuyen
coeficientes de esos ejemplos como calibración aplicable al inventario del usuario.

## Comprobaciones automáticas al publicar

El workflow `modelizacion-lidar.yml` ejecuta las mismas 17 pruebas en runners
**Ubuntu y Windows**, y un ensayo sintético con gráficos y predicción en ambos.
La publicación experimental depende de que los dos jobs terminen correctamente.
Consulte el enlace Actions de la versión para el resultado ejecutado de cada sistema;
esta sección describe el protocolo y no sustituye el estado real de esa ejecución.
No intervienen QGIS ni FUSION en esos ensayos.

## Pendiente con datos del usuario

- Instalación en su Windows y comprobación de que las unidades, IDs, fecha, radio y
  definición de las cuatro variables de campo coinciden con sus métricas LiDAR.
- Calibración y validación con una muestra real suficiente y representativa.
- Revisión forestal de ecuaciones, grupos, residuos y estabilidad; comparación con
  parcelas o montes independientes que no se usaron para decidir opciones.
- Validación externa de las ecuaciones definitivas. El script no proporciona
  intervalos de predicción ni estima un error de inventario de monte completo.

No se promete ausencia de sobreajuste o sesgo futuro: la validación anidada separa
selección y evaluación, pero depende del diseño muestral, los grupos y la cobertura
forestal de los datos. La tolerancia de 2 % del score favorece parsimonia; configure
0 si quiere el mínimo estricto dentro de la búsqueda.
