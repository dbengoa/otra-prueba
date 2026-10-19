"""Reutiliza las pruebas estadísticas contra el motor distribuido en el plugin."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'modelizacion_lidar'))
from modelizacion_forestal_lidar import engine
sys.modules['modelizacion_lidar'] = engine
from test_modelizacion import ModelsTests
