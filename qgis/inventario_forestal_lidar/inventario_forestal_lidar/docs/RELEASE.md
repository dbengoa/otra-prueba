0.4.1 experimental: arranque FUSION, selección de 64 bits y diagnóstico del fallo ClipData.

El registro recibido confirma ambas conversiones LAZ→LAS y el MDT, seguido de un
fallo 0xC0000005 de ClipData 32-bit antes de su cabecera. CloudMetrics no llegó a correr.
La causa interna aún no está confirmada ni el arreglo validado en Windows.

Cambios: preferencia por ejecutables *64.exe instalados, conservación de la pareja
LDA2LAS/LASzip 32-bit cuando falta LASzip64.dll, prueba ClipData /version previa al
cálculo, directorio de arranque del ejecutable y /log propio por ejecución. Muestra
cada LAS verificado, ruta y conteo; identifica fase/parcela/código al fallar. Añade
aviso de actividad cada 10 s. Mantiene descarga humana Chrome y resto automático.

Instalar ZIP y reiniciar QGIS. Reutilizar la misma carpeta de trabajo sin borrar LAZ
ni LAS. Si sólo hay FUSION de 32 bits, se registra; el plugin no instala programas.
Si persiste, conservar proceso.log, estado.json y fusion.log de la nueva ejecución.

Ejecutado: 65 pruebas Linux/QGIS aprobadas; 55 portables y 10 omitidas sin QGIS.
Pendiente: reproducir el caso real y comprobar ClipData/CloudMetrics en Windows.
No se afirma que 64 bits elimine por sí solo la causa del fallo; no incluye modelos.
