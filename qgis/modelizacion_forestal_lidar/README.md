# Modelización forestal LiDAR — complemento QGIS 0.3.0 experimental

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
- Mínimo operativo en la interfaz: 8 parcelas válidas por respuesta. No garantiza suficiencia.
  Fechas, soporte espacial, filtros y normalización deben ser compatibles.
- Carpeta de salida nueva o vacía y permisos de escritura. Admite espacios.

## Instalación y uso, sin consola

1. Descargue `modelizacion_forestal_lidar-0.3.0-experimental.zip` de `dist`.
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
En el selector, «Columnas estándar: cm_Elev» sirve tanto para métricas sin filtro
como para salidas del inventario filtradas a una misma altura. «cm_gt2» se reserva
al antiguo maestro con ese prefijo.
En predicción se deben conservar exactamente los nombres de métricas y protocolo
usados al calibrar. No se hace conversión automática entre familias.

## Número de métricas: versión 0.3.0

El nuevo selector **Mínimo de métricas por ecuación** empieza en **2**. Exige
al menos dos predictores LiDAR tanto en la selección interna como en cada modelo
externo y el modelo final. La media se calcula y exporta sólo como referencia;
no puede ganar cuando se exige mínimo 2. El máximo solicitado no puede ser menor.

Con **8–19 parcelas válidas por respuesta y mínimo 2**:

- Exactamente dos predictores, lineal o potencial con corrección de Duan.
- CV anidada dejando una parcela fuera: con ocho parcelas, se entrena con siete
  en el nivel externo y seis en el interno. Cada ecuación tiene intercepto y dos
  efectos; sólo quedan tres grados de libertad residuales en cada ajuste interno.
- Dos observaciones por coeficiente, relajación explícita respecto a la versión
  0.2.0 necesaria para permitir dos predictores. No convierte la muestra en suficiente.
- Preselección de hasta diez posiciones del ranking por entrenamiento, manteniendo
  filtros de ausencias, constante, correlación, VIF y singularidad. La selección se
  repite dentro de cada entrenamiento; no utiliza la respuesta externa reservada.
- Una repetición. Con grupos se deja un grupo fuera en cada nivel sin mezclarlos.
  Puede resultar imposible estimar dos predictores con los grupos disponibles.
- Sin candidato de dos predictores válido, informa del error; no baja a un predictor,
  no sustituye por la media y no elimina parcelas externas para facilitar el ajuste.

**Exigir dos métricas no significa que mejoren la predicción.** RMSE y sesgo siguen
siendo los obtenidos por la selección restringida, comparados con la media. Se
conservan errores altos, R² negativos y predicciones negativas. Las ecuaciones son
exploratorias; con ocho parcelas la selección y los errores son muy inestables.
No constituyen validación independiente del modelo final. Amplíe la muestra antes
de uso operativo y valide con datos nuevos.

Desde 20 parcelas se conservan cinco observaciones por coeficiente. Si el mínimo
es 2 y hay 20–29 parcelas, se aumentan a 20 las particiones solicitadas externas e
internas (limitadas a parcelas/grupos disponibles) para mantener entrenamientos
suficientes. Desde 30 se mantiene CV 5/4 y el máximo solicitado, normalmente 3.
Las restricciones de tamaño y grupos siempre pueden limitar el ajuste.

El selector admite también 1 (exigir una métrica) o 0 (permitir la media). Con
mínimo 0/1 y menos de 20 parcelas se conserva el procedimiento de 0.2.0: máximo
un predictor, preselección <=3 y tres observaciones por coeficiente.
Los parámetros efectivos por respuesta y el mínimo exigido se guardan en JSON,
resumen CSV, tablas de candidatos, registro y ecuaciones.txt.

Se requieren al menos ocho respuestas de campo válidas por variable. Los CSV deben
coincidir por ID, tener unidades correctas y métricas homogéneas. No se calculan
predictores con una respuesta forestal ni se inventan filas para alcanzar el mínimo.
El motor CLI conserva los valores predeterminados anteriores: para repetir el
perfil de la interfaz use `--min-parcelas 8 --min-predictores 2`.
Acepta modelos JSON anteriores 0.1.0 y 0.2.0 para predicción.

## Método y resultados

Compara lineales y potenciales con corrección de Duan, incluida la media como
referencia. En modo estándar: CV externa 5 particiones, interna 4, semilla 2026. Preselección y
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
