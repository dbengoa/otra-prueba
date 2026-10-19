"""Interfaz QGIS. No ejecuta procesos externos ni instala paquetes."""
import importlib
import logging
import sys
from pathlib import Path
from qgis.core import QgsApplication, QgsTask
from qgis.PyQt.QtCore import Qt, pyqtSignal, QUrl
from qgis.PyQt.QtGui import QDesktopServices
try:
    from qgis.PyQt.QtGui import QAction
except ImportError:
    from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QFormLayout,
    QHBoxLayout, QWidget, QLineEdit, QPushButton, QFileDialog, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QPlainTextEdit, QProgressBar, QMessageBox, QScrollArea)


def dependencies():
    errors = []
    if sys.version_info < (3, 10):
        errors.append('Python 3.10 o posterior')
    for name in ('numpy', 'pandas', 'matplotlib'):
        try:
            importlib.import_module(name)
        except Exception as error:
            errors.append(f'{name}: {error}')
    return errors


class LogHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
    def emit(self, record):
        self.signal.emit(self.format(record))


class ModelTask(QgsTask):
    message = pyqtSignal(str)
    finished_result = pyqtSignal(bool, str)
    def __init__(self, argv):
        super().__init__('Modelización forestal LiDAR', QgsTask.CanCancel)
        self.argv = argv
        self.error = ''
    def run(self):
        from . import engine
        handler = LogHandler(self.message)
        def check():
            if self.isCanceled():
                raise KeyboardInterrupt('Cancelado por el usuario')
        engine.CHECK_CANCEL = check
        engine.LOGGER.addHandler(handler)
        try:
            check()
            args = engine.parser().parse_args(self.argv)
            if args.command == 'ajustar':
                engine.fit_command(args)
            elif args.command == 'predecir':
                engine.predict_command(args)
            else:
                frame = engine.read_table(args.lidar, args.sep_lidar)
                identifiers = engine.ids(frame, args.id_lidar)
                path = Path(args.salida)
                if path.exists(): raise ValueError('La plantilla ya existe; no se sobrescribe')
                result = engine.pd.DataFrame({'parcela_id': identifiers})
                for target in engine.TARGETS: result[target] = ''
                path.parent.mkdir(parents=True, exist_ok=True)
                engine.write_csv(result, path)
            return True
        except KeyboardInterrupt:
            self.error = 'Cancelado. Los resultados parciales no son modelos completados.'
            return False
        except Exception as error:
            self.error = str(error)
            return False
        finally:
            engine.CHECK_CANCEL = lambda: None
            engine.LOGGER.removeHandler(handler)
    def finished(self, result):
        self.finished_result.emit(result, self.error or ('Cancelado antes de empezar.' if self.isCanceled() else ''))


class Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Modelización forestal LiDAR · 0.2.0 experimental')
        self.resize(820, 760)
        self.task = None
        self.result_path = None
        layout = QVBoxLayout(self)
        self.form_widget = QWidget()
        form = QFormLayout(self.form_widget)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setWidget(self.form_widget); scroll.setMinimumHeight(300)
        layout.addWidget(scroll, 3)
        self.mode = QComboBox()
        self.mode.addItems(['Ajustar y validar modelos', 'Crear plantilla de campo', 'Predecir con modelos guardados'])
        form.addRow('Operación', self.mode)
        self.lidar = self.path_row(form, 'Métricas LiDAR (CSV)', 'csv')
        self.field = self.path_row(form, 'Datos de campo (CSV)', 'csv')
        self.models = self.path_row(form, 'Modelos guardados (JSON)', 'json')
        self.output = self.path_row(form, 'Salida (carpeta o CSV según operación)', 'output')
        self.id_lidar = QComboBox(); self.id_field = QComboBox()
        form.addRow('ID en métricas', self.id_lidar); form.addRow('ID en campo', self.id_field)
        self.dec_lidar = QComboBox(); self.dec_lidar.addItems(['.', ','])
        self.dec_field = QComboBox(); self.dec_field.addItems(['.', ','])
        form.addRow('Decimal métricas', self.dec_lidar); form.addRow('Decimal campo', self.dec_field)
        self.targets = []
        for title, default in [('Volumen (m³/ha)', 'V_ha'), ('Área basal (m²/ha)', 'G_ha'), ('Pies/ha', 'N_ha'), ('Altura dominante (m)', 'Hdom')]:
            box = QComboBox(); box.addItem(default); form.addRow(title, box); self.targets.append((box, default))
        self.group = QComboBox(); self.group.addItem('(sin grupos)')
        form.addRow('Grupo / monte en campo (opcional)', self.group)
        self.protocol = QComboBox(); self.protocol.addItems(['Columnas estándar: cm_Elev … (corte según CSV)', 'Sólo >2 m: cm_gt2_Elev … (CSV maestro)'])
        form.addRow('Familia de métricas del CSV', self.protocol)
        self.max_predictors = QSpinBox(); self.max_predictors.setRange(1, 3); self.max_predictors.setValue(3)
        self.max_predictors.setToolTip('Con 8–19 parcelas se limita automáticamente a 1 predictor por ecuación.')
        form.addRow('Máximo de predictores (desde 20 parcelas)', self.max_predictors)
        self.bias = QDoubleSpinBox(); self.bias.setRange(0, 10); self.bias.setSingleStep(.1); self.bias.setValue(.5)
        form.addRow('Peso de |sesgo| en selección', self.bias)
        self.normalize = QCheckBox('Normalizar ID: 226.0 → 226 (conservar ceros iniciales)')
        self.partial = QCheckBox('Permitir IDs sin pareja y registrarlos en auditoría')
        self.graphs = QCheckBox('Generar gráficos de validación'); self.graphs.setChecked(True)
        for box in (self.normalize, self.partial, self.graphs): form.addRow(box)
        self.info = QPlainTextEdit(); self.info.setReadOnly(True)
        self.info.setPlainText('Mínimo: 8 parcelas válidas por variable. Con 8–19: modo exploratorio, máximo 1 predictor.\nCV anidada dejando una parcela/grupo fuera; preselección <=3. Desde 20: CV 5/4 y hasta 3 predictores.\nUse métricas homogéneas: el filtro de altura debe coincidir en calibración y aplicación.\nLa CV evalúa la selección; no sustituye una prueba independiente del modelo final.')
        layout.addWidget(self.info, 1)
        self.progress = QProgressBar(); layout.addWidget(self.progress)
        buttons = QHBoxLayout(); layout.addLayout(buttons)
        self.start = QPushButton('Ejecutar'); self.cancel = QPushButton('Cancelar'); self.cancel.setEnabled(False)
        self.open_output = QPushButton('Abrir resultados'); self.open_output.setEnabled(False)
        help_button = QPushButton('Instrucciones')
        for button in (self.start, self.cancel, self.open_output, help_button): buttons.addWidget(button)
        self.start.clicked.connect(self.execute)
        self.cancel.clicked.connect(self.cancel_task)
        self.open_output.clicked.connect(self.open_results)
        help_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(__file__).with_name('README.html')))))
        self.lidar.editingFinished.connect(lambda: self.load_columns('lidar'))
        self.field.editingFinished.connect(lambda: self.load_columns('field'))
        self.mode.currentIndexChanged.connect(self.update_mode)
        self.update_mode()

    def path_row(self, form, title, kind):
        row = QWidget(); h = QHBoxLayout(row); h.setContentsMargins(0, 0, 0, 0)
        edit = QLineEdit(); button = QPushButton('…'); h.addWidget(edit); h.addWidget(button)
        def browse():
            if kind == 'output':
                if self.mode.currentIndex() == 0:
                    path = QFileDialog.getExistingDirectory(self, 'Carpeta nueva o vacía')
                else:
                    path, _ = QFileDialog.getSaveFileName(self, 'CSV de salida', '', 'CSV (*.csv)')
            else:
                path, _ = QFileDialog.getOpenFileName(self, title, '', f'{kind.upper()} (*.{kind})')
            if path:
                edit.setText(path)
                if kind == 'csv':
                    self.load_columns('lidar' if edit is self.lidar else 'field')
        button.clicked.connect(browse); form.addRow(title, row)
        return edit

    def load_columns(self, which):
        from . import engine
        edit = self.lidar if which == 'lidar' else self.field
        if not edit.text().strip(): return
        try:
            columns = list(engine.read_table(edit.text().strip()).columns)
            combos = [(self.id_lidar, 'parcela_id')] if which == 'lidar' else [(self.id_field, 'parcela_id'), *self.targets]
            for combo, default in combos:
                previous = combo.currentText()
                combo.clear(); combo.addItems(columns)
                choice = previous if previous in columns else default
                if choice in columns: combo.setCurrentText(choice)
            if which == 'field':
                self.group.clear(); self.group.addItems(['(sin grupos)', *columns])
        except Exception as error:
            self.info.appendPlainText('No se pudo leer el CSV: '+str(error))

    def update_mode(self):
        fit = self.mode.currentIndex() == 0
        pred = self.mode.currentIndex() == 2
        self.field.parentWidget().setEnabled(fit)
        self.models.parentWidget().setEnabled(pred)
        for widget in (self.id_field, self.dec_field, self.group, self.protocol, self.max_predictors, self.bias, self.partial, self.graphs): widget.setEnabled(fit)
        for box, _ in self.targets: box.setEnabled(fit)
        self.normalize.setEnabled(fit or pred)

    def arguments(self):
        mode = self.mode.currentIndex()
        lidar = self.lidar.text().strip(); output = self.output.text().strip()
        if not Path(lidar).is_file() or not output or not self.id_lidar.currentText():
            raise ValueError('Seleccione métricas CSV, su campo ID y una salida.')
        common = ['--lidar', lidar, '--id-lidar', self.id_lidar.currentText(), '--salida', output]
        if mode == 1: return ['plantilla', *common]
        common += ['--decimal-lidar', self.dec_lidar.currentText()]
        if self.normalize.isChecked(): common.append('--normalizar-id-decimal')
        if mode == 2:
            if not Path(self.models.text().strip()).is_file(): raise ValueError('Seleccione modelos.json')
            return ['predecir', *common, '--modelos', self.models.text().strip()]
        field = self.field.text().strip()
        if not Path(field).is_file(): raise ValueError('Seleccione el CSV de campo')
        targets = [box.currentText() for box, _ in self.targets]
        if len(set(targets)) != 4: raise ValueError('Las cuatro variables de campo deben ser columnas diferentes')
        argv = ['ajustar', *common, '--campo', field, '--id-campo', self.id_field.currentText(), '--decimal-campo', self.dec_field.currentText(), '--objetivos', *targets,
                '--min-parcelas', '8', '--max-predictores', str(self.max_predictors.value()), '--peso-sesgo', str(self.bias.value())]
        if self.partial.isChecked(): argv.append('--permitir-no-coincidentes')
        if not self.graphs.isChecked(): argv.append('--sin-graficos')
        if self.group.currentIndex() > 0: argv += ['--grupo', self.group.currentText()]
        if self.protocol.currentIndex() == 1:
            argv += ['--regex', r'^(cm_gt2_Elev |cm_gt2_Canopy relief ratio$|cm_gt2_Profile area$)']
        # Prevent mixing protocols through missing-value imputation.
        from . import engine
        frame = engine.read_table(lidar)
        flag = 'disponible_gt2' if self.protocol.currentIndex() == 1 else 'disponible_todos'
        if flag in frame and not frame[flag].eq('1').all():
            raise ValueError('El CSV maestro incluye parcelas sin el tipo de métricas elegido. Prepare un CSV homogéneo; no se mezclarán protocolos ni se rellenará esa ausencia.')
        return argv

    def execute(self):
        if self.task is not None: return
        try:
            argv = self.arguments()
        except Exception as error:
            QMessageBox.warning(self, 'Revise las entradas', str(error)); return
        self.result_path = Path(self.output.text().strip())
        self.task = ModelTask(argv)
        self.task.message.connect(self.info.appendPlainText)
        self.task.finished_result.connect(self.done_task)
        self.form_widget.setEnabled(False); self.start.setEnabled(False); self.cancel.setEnabled(True); self.open_output.setEnabled(False)
        self.progress.setRange(0, 0)
        self.info.appendPlainText('Inicio. El cálculo se ejecuta en segundo plano; puede cancelar.')
        QgsApplication.taskManager().addTask(self.task)

    def cancel_task(self):
        if self.task:
            self.task.cancel(); self.cancel.setEnabled(False)
            self.info.appendPlainText('Cancelación solicitada. Se espera a que termine la operación numérica activa.')

    def done_task(self, success, error):
        self.task = None
        self.form_widget.setEnabled(True); self.start.setEnabled(True); self.cancel.setEnabled(False)
        self.progress.setRange(0, 100); self.progress.setValue(100 if success else 0)
        self.open_output.setEnabled(success)
        if success:
            self.info.appendPlainText('Completado: '+str(self.result_path))
            directory = self.result_path if self.result_path.is_dir() else self.result_path.parent
            equations = directory/'ecuaciones.txt'
            if equations.is_file(): self.info.appendPlainText(equations.read_text(encoding='utf-8'))
            summary = directory/'resumen_validacion.csv'
            if summary.is_file(): self.info.appendPlainText('Validación externa (CSV):\n'+summary.read_text(encoding='utf-8-sig'))
        else:
            self.info.appendPlainText('ERROR / CANCELACIÓN: '+error)

    def open_results(self):
        if self.result_path:
            directory = self.result_path if self.result_path.is_dir() else self.result_path.parent
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory.resolve())))

    def closeEvent(self, event):
        if self.task is not None:
            self.cancel_task(); event.ignore()
        else: event.accept()

    def reject(self):
        if self.task is not None: self.cancel_task()
        else: super().reject()


class Plugin:
    def __init__(self, iface):
        self.iface = iface; self.dialog = None; self.action = None
    def initGui(self):
        self.action = QAction('Modelización forestal LiDAR', self.iface.mainWindow())
        self.action.setIcon(QgsApplication.getThemeIcon('/mIconTableLayer.svg'))
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu('Modelización forestal LiDAR', self.action)
        self.iface.addToolBarIcon(self.action)
    def run(self):
        if self.dialog is None and any(t.description() == 'Modelización forestal LiDAR' and t.isActive() for t in QgsApplication.taskManager().tasks()):
            QMessageBox.information(self.iface.mainWindow(), 'Cálculo activo', 'Espere a que termine o se cancele el cálculo anterior.')
            return
        errors = dependencies()
        if errors:
            QMessageBox.warning(self.iface.mainWindow(), 'Dependencias de QGIS', 'Faltan o no funcionan dependencias en el Python de QGIS:\n'+ '\n'.join(errors)+'\n\nSolicite a informática una instalación de QGIS con estos paquetes. El complemento no instala software ni cambia la protección del equipo.')
            return
        if self.dialog is None: self.dialog = Dialog(self.iface.mainWindow())
        self.dialog.show(); self.dialog.raise_(); self.dialog.activateWindow()
    def unload(self):
        if self.dialog:
            if self.dialog.task: self.dialog.cancel_task()
            self.dialog.hide()
        if self.action:
            self.iface.removePluginMenu('Modelización forestal LiDAR', self.action)
            self.iface.removeToolBarIcon(self.action)
