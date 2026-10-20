"""Ejecutar con Python de QGIS; QT_QPA_PLATFORM=offscreen en CI."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qgis.core import QgsApplication
from modelizacion_forestal_lidar import engine
from modelizacion_forestal_lidar.plugin import Dialog, ModelTask, dependencies
app = QgsApplication.instance() or QgsApplication([], False)

class Integration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.lidar = self.root/'lidar.csv'; self.field = self.root/'campo.csv'
        self.lidar.write_text('parcela_id,cm_Elev P95,cm_Elev mean\n'+''.join(f'{i},{5+i/3},{3+i/4}\n' for i in range(40)))
        self.field.write_text('parcela_id,V_ha,G_ha,N_ha,Hdom\n'+''.join(f'{i},{20+i*2},{5+i/2},{100+i*3},{6+i/3}\n' for i in range(40)))
        self.dialog = Dialog()
        self.dialog.min_predictors.setValue(0)
        self.dialog.lidar.setText(str(self.lidar)); self.dialog.load_columns('lidar')
        self.dialog.field.setText(str(self.field)); self.dialog.load_columns('field')
        self.dialog.output.setText(str(self.root/'result'))
    def tearDown(self):
        self.dialog.close(); self.temp.cleanup()
    def test_dependencies_and_column_selection(self):
        self.assertEqual(dependencies(), [])
        self.assertEqual(self.dialog.id_lidar.currentText(), 'parcela_id')
        self.assertEqual([c.currentText() for c,_ in self.dialog.targets], engine.TARGETS)
    def test_template_and_no_overwrite(self):
        self.dialog.mode.setCurrentIndex(1)
        self.dialog.output.setText(str(self.root/'plantilla.csv'))
        task = ModelTask(self.dialog.arguments())
        self.assertTrue(task.run(), task.error)
        self.assertEqual(len(engine.read_table(self.root/'plantilla.csv')), 40)
        task = ModelTask(self.dialog.arguments()); self.assertFalse(task.run())
    def test_fit_graphs_predict(self):
        self.dialog.max_predictors.setValue(1)
        args = self.dialog.arguments()+['--preseleccion', '2']
        task = ModelTask(args); self.assertTrue(task.run(), task.error)
        result = self.root/'result'
        self.assertEqual(json.loads((result/'estado.json').read_text())['estado'], 'completado')
        self.assertEqual(len(list(result.glob('diagnostico_*.png'))),4)
        self.assertEqual(len(engine.read_table(result/'resumen_validacion.csv')),4)
        self.dialog.mode.setCurrentIndex(2)
        self.dialog.models.setText(str(result/'modelos.json'))
        self.dialog.output.setText(str(self.root/'pred.csv'))
        task=ModelTask(self.dialog.arguments()); self.assertTrue(task.run(),task.error)
        self.assertEqual(len(engine.read_table(self.root/'pred.csv')),40)
    def test_eight_plots_four_targets_gui_arguments(self):
        for path in (self.lidar,self.field):
            lines=path.read_text().splitlines()
            path.write_text('\n'.join(lines[:9])+'\n')
        args=self.dialog.arguments()
        self.assertEqual(args[args.index('--min-parcelas')+1],'8')
        task=ModelTask(args);self.assertTrue(task.run(),task.error)
        result=self.root/'result'
        package=json.loads((result/'modelos.json').read_text())
        self.assertEqual(len(package['modelos']),4)
        for model in package['modelos'].values():
            self.assertEqual(model['n_calibracion'],8)
            self.assertEqual(model['modo'],'exploratorio_muestra_pequena')
            self.assertLessEqual(len(model['predictores']),1)
        self.assertIn('EXPLORATORIO',(result/'ecuaciones.txt').read_text())
        self.assertEqual(len(engine.read_table(result/'predicciones_validacion.csv')),32)

    def test_gui_two_predictor_minimum_and_four_equations(self):
        fresh=Dialog()
        self.assertEqual(fresh.min_predictors.value(),2)
        fresh.close()
        self.lidar.write_text('parcela_id,cm_Elev P95,cm_Elev stddev\n'+''.join(f'{i},{i+2},{z}\n' for i,z in enumerate([.5,2.2,1.1,3.4,.9,2.7,4.8,1.7])))
        self.field.write_text('parcela_id,V_ha,G_ha,N_ha,Hdom\n'+''.join(f'{i},{5+3*(i+2)+4*z},{10+(i+2)+2*z},{50+4*(i+2)+3*z},{3+2*(i+2)+z}\n' for i,z in enumerate([.5,2.2,1.1,3.4,.9,2.7,4.8,1.7])))
        self.dialog.min_predictors.setValue(2)
        args=self.dialog.arguments()
        self.assertEqual(args[args.index('--min-predictores')+1],'2')
        task=ModelTask(args);self.assertTrue(task.run(),task.error)
        package=json.loads((self.root/'result'/'modelos.json').read_text())
        for model in package['modelos'].values():
            self.assertEqual(len(model['predictores']),2)
            self.assertNotEqual(model['familia'],'media')
        self.assertEqual(len(package['modelos']),4)

    def test_reject_mixed_protocol(self):
        self.lidar.write_text('parcela_id,cm_Elev P95,disponible_todos\n1,10,1\n2,,0\n')
        with self.assertRaisesRegex(ValueError,'homogéneo'): self.dialog.arguments()
    def test_cancel_during_fit(self):
        task=ModelTask(self.dialog.arguments()+['--preseleccion','2'])
        from modelizacion_forestal_lidar.plugin import LogHandler
        class CancelOnFold(__import__('logging').Handler):
            def emit(self,record):
                if 'partición externa' in record.getMessage(): task.cancel()
        handler=CancelOnFold(); engine.LOGGER.addHandler(handler)
        try: self.assertFalse(task.run())
        finally: engine.LOGGER.removeHandler(handler)
        self.assertIn('Cancelado',task.error)
        self.assertEqual(json.loads((self.root/'result'/'estado.json').read_text())['estado'],'cancelado')
        self.assertEqual(engine.LOGGER.handlers,[])
    def test_minimum_8_and_invalid_ids(self):
        self.lidar.write_text('parcela_id,cm_Elev P95\n1,10\n')
        self.field.write_text('parcela_id,V_ha,G_ha,N_ha,Hdom\n1,100,20,500,10\n')
        task=ModelTask(self.dialog.arguments()); self.assertFalse(task.run()); self.assertIn('8',task.error)
    def test_async_task(self):
        from qgis.PyQt.QtCore import QEventLoop, QTimer
        self.dialog.mode.setCurrentIndex(1)
        self.dialog.output.setText(str(self.root/'async.csv'))
        loop=QEventLoop(); timeout=QTimer(); timeout.setSingleShot(True)
        timeout.timeout.connect(loop.quit)
        self.dialog.execute()
        task=self.dialog.task; task.finished_result.connect(lambda *_: loop.quit())
        timeout.start(15000); loop.exec()
        self.assertIsNone(self.dialog.task)
        self.assertTrue((self.root/'async.csv').exists())
        self.assertTrue(self.dialog.start.isEnabled())

if __name__ == '__main__': unittest.main(verbosity=2)
