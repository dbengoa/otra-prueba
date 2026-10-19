# Validación QGIS 0.2.0 experimental — 19-10-2026

## Ejecutado en Linux

- 17 pruebas estadísticas del motor: lineal/potencial, Duan, selección anidada,
  grupos, IDs, errores y predicción.
- 7 pruebas nuevas de muestras pequeñas: ocho parcelas con candidato lineal y
  potencial, predicción externa única por parcela y entrenamientos internos de seis,
  rechazo de siete, límites estándar conservados desde 20, selección sin la parcela
  externa, separación de grupos, rechazo de grupos insuficientes y lectura de JSON
  de modelos 0.1.0 (algunos aspectos comparten prueba).
- 8 pruebas de integración QGIS 3.40.6/Python 3.13, incluidas cuatro respuestas con
  ocho parcelas, 32 predicciones externas, cuatro PNG y advertencias exportadas.
- Ejecución privada con los ocho registros aportados y sus datos de campo: las
  cuatro respuestas completaron el proceso y se generaron cuatro PNG. Los datos,
  coeficientes y resultados privados NO se incluyen en el repositorio ni el ZIP.
- ZIP con carpeta raíz válida, sintaxis de los módulos y SHA256 verificadas.

Total automatizado: 32 pruebas aprobadas (17 + 7 + 8).
Las buenas pruebas artificiales comprueban funcionamiento, no validez forestal.

## Pendiente en Windows

Instalación y uso de QGIS en el ordenador del usuario, dependencias de esa
instalación y comportamiento de sus unidades de red. Las pruebas Linux no son
pruebas Windows. El workflow añadido puede ejecutar las pruebas portables en
Windows/Linux; su configuración no equivale a haberlas ejecutado. No ejecuta QGIS
Windows. Falta validación forestal independiente con una muestra mayor.

## Reproducción

Desde qgis/modelizacion_forestal_lidar con dependencias disponibles:

```
python -m unittest discover -s tests -p test_engine.py -v
python -m unittest discover -s tests -p test_small_sample.py -v
QT_QPA_PLATFORM=offscreen python tests/test_qgis.py
python build.py
```
