# Modelización forestal LiDAR — complemento QGIS 0.1.0 experimental

Interfaz de QGIS para el motor de modelización 0.1.0. No abre PowerShell,
no ejecuta programas externos y no instala paquetes. No requiere FUSION para
ajustar; utiliza los CSV de métricas ya calculados.

## Necesario

- QGIS 3.28–3.x con Python 3.10 o posterior. Recomendado QGIS LTR de 64 bits.
- NumPy, pandas y matplotlib disponibles en el Python de QGIS. La comprobación
  al abrir informa de paquetes ausentes o incompatibles. Si falta alguno,
  informática debe proporcionarlo en una instalación autorizada de QGIS;
  no se elude ninguna protección corporativa.
- CSV UTF-8 LiDAR: `parcela_id` y métricas numéricas `cm_Elev ...`.
- CSV UTF-8 de campo: un ID único por parcela, volumen m³/ha, área basal m²/ha,
  pies/ha y altura dominante en metros. Nombres predeterminados:
  `parcela_id,V_ha,G_ha,N_ha,Hdom`; se pueden seleccionar otras columnas.
- Mínimo operativo: 20 parcelas válidas por respuesta; no garantiza suficiencia.
  Fechas, soporte espacial, filtros y normalización deben ser compatibles.
- Carpeta de salida nueva o vacía y permisos de escritura. Admite espacios.

## Instalación y uso, sin consola

1. Descargue `modelizacion_forestal_lidar-0.1.0-experimental.zip` de `dist`.
   No use el ZIP de todo el repositorio y no descomprima el ZIP instalable.
2. QGIS → Complementos → Administrar e instalar complementos → Instalar a partir
   de ZIP → seleccione el archivo → Instalar complemento.
3. Active «Modelización forestal LiDAR». Ábralo desde Complementos o su botón.
4. Si no tiene campo.csv, elija «Crear plantilla de campo», seleccione métricas,
   seleccione su campo ID y el CSV de salida. Ejecute. Rellene en Excel y guarde
   como CSV UTF-8, conservando el ID como texto. No sustituya Hdom por un percentil.
5. Elija «Ajustar y validar modelos». Seleccione CSV LiDAR y campo; compruebe los
   IDs, las cuatro columnas de respuesta y los separadores decimales. El separador
   de columnas coma/punto y coma/tabulador se detecta automáticamente.
6. Seleccione grupo/monte si corresponde. Cada grupo se mantiene entero en CV
   externa e interna. Con muy pocos grupos no se puede validar.
7. Escoja carpeta nueva/vacía y pulse Ejecutar. El cálculo se hace en segundo plano.
   La barra indica actividad, no una estimación del tiempo restante. El registro
   muestra variables y particiones externas. Cancelar espera a la operación
   numérica activa; no cierre QGIS mientras se está cancelando.
8. Consulte las ecuaciones y resumen mostrados; «Abrir resultados» abre la carpeta.
9. Para aplicar ecuaciones, elija «Predecir con modelos guardados», seleccione
   modelos.json, nuevas métricas y un CSV de salida que no exista.

## CSV maestro y filtros de altura

`cm_Elev ...` significa todos los retornos en el CSV maestro previamente preparado;
`cm_gt2_Elev ...` corresponde a >2 m. La interfaz permite escoger una familia.
Si el maestro contiene parcelas sin esa familia (indicadores disponible_todos / 
disponible_gt2), rechaza el ajuste. Prepare un CSV con parcelas homogéneas o vuelva
 a calcular las métricas con el mismo criterio. No interprete los vacíos como cero.
Un CSV CloudMetrics filtrado que aún usa nombres `cm_Elev ...` debe documentarse
como filtrado: la cabecera por sí sola no permite reconocer ese protocolo.
En predicción se deben conservar exactamente los nombres de métricas y protocolo
usados al calibrar. No se hace conversión automática entre familias.

## Método y resultados

Compara lineales y potenciales con corrección de Duan, incluida la media como
referencia. CV externa 5 particiones, interna 4, semilla 2026. Preselección y
selección dentro de cada entrenamiento; hasta 3 predictores, 5 observaciones por
coeficiente. Selección RMSE + peso × |sesgo|, peso inicial 0.5; tolerancia del 2 %
para favorecer modelos más sencillos. Sesgo = predicho − observado.
No se asegura un mínimo global ni sesgo cero. Intensidad excluida por defecto.
La CV evalúa el procedimiento de selección, no es prueba independiente del
modelo final reajustado. Evite validación aleatoria de parcelas espacialmente
dependientes: seleccione grupos adecuados. Más detalles en METODOLOGIA.md.

- ecuaciones.txt: ecuaciones explícitas; modelos.json: coeficientes y aplicación.
- resumen_validacion.csv: RMSE, sesgo, porcentajes, MAE y R² externos.
- predicciones_validacion.csv: predicciones fuera de muestra por ID.
- diagnostico_*.png: gráficos; candidatos_*.csv: comparación interna.
- auditoria_union.json y exclusiones.csv: IDs y observaciones excluidas.
- ajuste.log y estado.json: progreso y completado/fallido/cancelado.

No se sobrescriben resultados ni originales. Una ejecución cancelada/fallida no
es una calibración completa. No use modelos parciales. Los datos permanecen en
el equipo; el complemento no realiza llamadas de red. Los modelos no ofrecen
intervalos de predicción. Revise extrapolación y plausibilidad forestal.

## Pruebas

Consulte VALIDACION.md: separa lo ejecutado en Linux/QGIS de lo pendiente en
Windows. Se incluyen ejemplos artificiales en ejemplo_sintetico; no son datos
reales ni ecuaciones válidas para un monte concreto.
