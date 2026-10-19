0.3.1 experimental: corrige el bloqueo «Nomenclatura PNOA3 no reconocida».

Admite `PNOA-2024-PNR-523-4654-NPC01.laz` y otras variantes sin Hxx. El huso ausente
no se usa como CRS: permanecen las comprobaciones de huellas oficiales y del CRS leído
del archivo. Se conserva la selección de año/NPC y el rechazo de husos explícitos
incompatibles.

Instale el ZIP sin descomprimir y reinicie QGIS. Mantiene el flujo automático CNIG →
LAZ → LAS → FUSION → métricas, sin CSV ni selección de archivos.

43 pruebas Linux/QGIS aprobadas; 3 de navegador omitidas porque su código no cambia.
Las pruebas de navegador de 0.3.0 se realizaron contra un servidor local. Sigue pendiente
validar autorización/descarga y FUSION de extremo a extremo en Windows.
