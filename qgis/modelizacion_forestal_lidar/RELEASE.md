Modelización forestal LiDAR 0.2.0 experimental: admite desde ocho parcelas válidas
por variable en QGIS, sin consola. Modo exploratorio automático de 8 a 19: CV
anidada dejando una parcela/grupo fuera, máximo un predictor, preselección <=3,
tres observaciones por coeficiente. Desde 20 se conserva el método estándar.
Se exporta el aviso exploratorio y las opciones efectivas por variable; no se
fuerzan relaciones LiDAR si la media es el candidato preferido. Mantiene lectura
de modelos 0.1.0. Se aclara la selección de columnas cm_Elev frente a cm_gt2.
32 pruebas aprobadas en Linux, incluidas ocho de integración QGIS. Pendiente:
instalación y ejecución real en QGIS Windows y validación forestal independiente.
