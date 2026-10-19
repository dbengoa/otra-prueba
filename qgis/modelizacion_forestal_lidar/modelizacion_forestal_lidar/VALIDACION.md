# Validación 0.1.0 experimental (19-10-2026)

## Ejecutado en este entorno Linux

Integración: QGIS 3.40.6, Python 3.13, pandas 3.0.6, NumPy 2.5.4 y matplotlib 3.11.2.
Motor adicional: Python 3.12 con las dependencias disponibles del entorno.

- 17 pruebas estadísticas reutilizadas contra el motor incluido en el complemento:
  lineal/potencial, retransformation, selección/CV, grupos, IDs, errores y predicción.
- 7 pruebas con las clases reales de QGIS/PyQt en modo offscreen: dependencias y
  selección de columnas; plantilla y rechazo de sobrescritura; ajuste de las cuatro
  respuestas con 40 parcelas artificiales, 4 PNG y predicción; rechazo de mezcla de
  protocolos; cancelación durante CV con estado cancelado; mínimo de 20 parcelas;
  ejecución asíncrona real con QgsTask y recuperación de los controles de interfaz.
- ZIP construido con una carpeta raíz válida y sin cachés ni datos privados.
- pandas/matplotlib de prueba instalados sólo en carpeta aislada de este entorno;
  esos paquetes binarios NO se incluyen en el complemento.

Comandos para reproducir, desde un entorno que disponga de QGIS y dependencias:

```
python -m unittest discover -s tests -p test_engine.py -v
QT_QPA_PLATFORM=offscreen python tests/test_qgis.py
python build.py
```

## Pendiente en Windows

- Instalación desde ZIP y uso manual en el QGIS concreto del usuario.
- Disponibilidad y compatibilidad de NumPy/pandas/matplotlib de esa instalación.
- Restricciones del ordenador corporativo y permisos de carpeta/unidad de red.
- Apertura de ayuda/resultados con aplicaciones Windows y cancelación de un ajuste
  largo desde la interfaz en ese sistema.
- Validación forestal con datos de campo reales, homogéneos e independientes.

No se afirma que las pruebas Linux sean pruebas Windows ni que los ejemplos
artificiales validen ecuaciones de inventario reales.
