# Validación QGIS 0.3.0 experimental — 20-10-2026

## Ejecutado en Linux

39 pruebas aprobadas: 17 del motor original, 7 de muestras pequeñas heredadas,
6 nuevas de selección con mínimo dos predictores y 9 de integración QGIS 3.40.6.
Las nuevas verificaciones cubren: modelos externos y final con dos métricas,
media no elegible, rechazo de parejas colineales o de un solo predictor,
entrenamientos internos de seis parcelas, opciones incompatibles y ajuste del
número de particiones para veinte parcelas. Se verifican cuatro ecuaciones desde
los argumentos de la interfaz y que su nuevo mínimo inicial es 2.

También se ejecutó el perfil de mínimo dos con los ocho registros del usuario:
cuatro ecuaciones y cuatro PNG completados. Es una comprobación de funcionamiento;
los datos, coeficientes y resultados privados no se publican en el repositorio.
La preselección de hasta diez métricas evita restringir la búsqueda a las pocas
métricas de altura más correlacionadas. No se relaja VIF ni se oculta la comparación
con la media. No hay garantía de mejora ni de validez forestal externa.

Pendiente: instalar y ejecutar esta versión en QGIS Windows del usuario. Las
pruebas Linux no son pruebas Windows. El workflow configura pruebas portables en
Windows/Linux y publicación experimental, pero su configuración no demuestra su
resultado ni ejecuta la interfaz QGIS en Windows. Falta validación forestal
independiente con más parcelas.

## Reproducción

```
python -m unittest discover -s tests -p test_engine.py -v
python -m unittest discover -s tests -p test_small_sample.py -v
python -m unittest discover -s tests -p test_two_predictors.py -v
QT_QPA_PLATFORM=offscreen python tests/test_qgis.py
python build.py
```
