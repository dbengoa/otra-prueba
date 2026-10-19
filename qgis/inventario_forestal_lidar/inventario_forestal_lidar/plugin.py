from pathlib import Path
import os
import threading
import webbrowser
from qgis.PyQt.QtCore import Qt, pyqtSignal, QVariant
from qgis.PyQt.QtWidgets import (QAction,QDialog,QVBoxLayout,QFormLayout,QLineEdit,
    QDoubleSpinBox,QPushButton,QFileDialog,QProgressBar,QPlainTextEdit,QMessageBox,QHBoxLayout,QLabel,QCheckBox)
from qgis.core import QgsApplication,QgsTask,QgsWkbTypes,QgsVectorLayer,QgsProject,NULL,QgsMapLayerProxyModel
from qgis.gui import QgsMapLayerComboBox,QgsFieldComboBox
from .core import Plot, CATALOG, validate
from .engine import Engine


class Job(QgsTask):
    status = pyqtSignal(float,str)
    completed = pyqtSignal(str,str)

    def __init__(self, config, plots):
        super().__init__('Inventario forestal LiDAR',QgsTask.CanCancel)
        self.retry_authorization = threading.Event()
        self.engine = Engine(config,plots,self.isCanceled,self.report,self.retry_authorization)
        self.message = ''
        self.result_dir = ''

    def report(self,n,text):
        self.setProgress(n)
        self.status.emit(n,text)

    def run(self):
        try:
            self.result_dir = self.engine.execute()
            return True
        except Exception as e:
            self.message = str(e)
            self.result_dir = str(getattr(self.engine,'run',''))
            return False

    def finished(self,success):
        self.completed.emit(self.result_dir,self.message)


class Dialog(QDialog):
    def __init__(self,iface):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.job = None
        self.setWindowTitle('Inventario forestal LiDAR · Experimental 0.3.2')
        self.resize(700,600)
        outer = QVBoxLayout(self)
        outer.addWidget(QLabel('Windows · FUSION 4.61 · PNOA tercera cobertura · Sin modelización estadística'))
        form = QFormLayout()
        self.layer = QgsMapLayerComboBox()
        self.layer.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.field = QgsFieldComboBox()
        self.layer.layerChanged.connect(self.field.setLayer)
        self.field.setLayer(self.layer.currentLayer())
        self.radius = QDoubleSpinBox()
        self.radius.setRange(.01,10000)
        self.radius.setValue(15)
        self.radius.setSuffix(' m')
        self.cell = QDoubleSpinBox()
        self.cell.setRange(.1,20)
        self.cell.setValue(1)
        self.output = QLineEdit()
        self.assume_crs = QCheckBox('Asumir CRS de parcelas sólo en archivos sin CRS (lo he comprobado)')
        self.support = QDoubleSpinBox()
        self.support.setRange(.5,20)
        self.support.setValue(5)
        self.support.setSuffix(' m')
        self.fusion = QLineEdit('C:\\FUSION')
        form.addRow('Centros de parcelas',self.layer)
        form.addRow('ID único (se conserva como texto)',self.field)
        form.addRow('Radio',self.radius)
        form.addRow('Celda MDT (m)',self.cell)
        form.addRow('Carpeta sin espacios',self.path_row(self.output,False))
        form.addRow('',self.assume_crs)
        form.addRow('Distancia máxima sin apoyo',self.support)
        form.addRow('FUSION',self.fusion)
        outer.addLayout(form)
        outer.addWidget(QLabel('Descarga automática PNOA3 desde las parcelas: consulta CNIG → LAZ → LAS → FUSION.\nSi CNIG exige autorización, complete el paso en la ventana de Google Chrome.\nEl plugin guarda las descargas y continúa el cálculo; no necesita cargar archivos ni CSV.'))
        buttons = QHBoxLayout()
        self.catalog = QPushButton('Ayuda / portal CNIG')
        self.catalog.clicked.connect(lambda:webbrowser.open(CATALOG))
        self.start = QPushButton('Ejecutar / reanudar')
        self.start.clicked.connect(self.execute)
        self.cancel_button = QPushButton('Cancelar')
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel)
        self.auth_button = QPushButton('Continuar autorización')
        self.auth_button.setEnabled(False)
        self.auth_button.clicked.connect(self.continue_authorization)
        for button in (self.catalog,self.start,self.auth_button,self.cancel_button):
            buttons.addWidget(button)
        outer.addLayout(buttons)
        self.bar = QProgressBar()
        outer.addWidget(self.bar)
        self.messages = QPlainTextEdit()
        self.messages.setReadOnly(True)
        outer.addWidget(self.messages)

    def continue_authorization(self):
        if self.job:
            self.job.retry_authorization.set()
            self.messages.appendPlainText('Se solicita reintentar el botón oficial de descarga, sin eludir la autorización.')

    def path_row(self,edit,file):
        from qgis.PyQt.QtWidgets import QWidget
        box = QWidget()
        layout = QHBoxLayout(box)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(edit)
        button = QPushButton('…')
        def choose():
            path = QFileDialog.getOpenFileName(self,'Índice CNIG','','CSV (*.csv)')[0] if file else QFileDialog.getExistingDirectory(self,'Carpeta de trabajo')
            if path:
                edit.setText(path)
        button.clicked.connect(choose)
        layout.addWidget(button)
        return box

    def execute(self):
        try:
            if os.name != 'nt':
                raise ValueError('El procesamiento FUSION requiere Windows')
            layer = self.layer.currentLayer()
            field = self.field.currentField()
            if not layer or not layer.isValid() or field not in layer.fields().names():
                raise ValueError('Seleccione capa de puntos y campo ID')
            if layer.crs().authid() not in ('EPSG:25828','EPSG:25829','EPSG:25830','EPSG:25831','EPSG:4083'):
                raise ValueError('Reproyecte la capa al CRS UTM de las teselas (ETRS89 o REGCAN95)')
            plots = []
            for feature in layer.getFeatures():
                geometry = feature.geometry()
                value = feature[field]
                if value is None or value == NULL or geometry.isEmpty() or geometry.isMultipart() or QgsWkbTypes.geometryType(geometry.wkbType()) != QgsWkbTypes.PointGeometry:
                    raise ValueError('Se requiere un centro puntual y un ID no nulo por parcela')
                point = geometry.asPoint()
                plots.append(Plot(str(value),point.x(),point.y()))
            output = self.output.text().strip()
            if not output or not Path(output).is_absolute():
                raise ValueError('Seleccione una carpeta absoluta de trabajo')
            validate(plots,self.radius.value(),output)
            config = {'output':output,'assume_missing_crs':self.assume_crs.isChecked(),
                      'support_distance':self.support.value(),'fusion':self.fusion.text(),
                      'epsg':int(layer.crs().authid().split(':')[1]),'radius':self.radius.value(),'cell':self.cell.value()}
            self.job = Job(config,plots)
            self.job.status.connect(self.status)
            self.job.completed.connect(self.finished)
            self.start.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.messages.appendPlainText('Inicio. Se procesan todas las entidades de la capa.')
            QgsApplication.taskManager().addTask(self.job)
        except Exception as e:
            QMessageBox.warning(self,'Validación',str(e))

    def status(self,n,text):
        self.bar.setValue(int(n))
        self.messages.appendPlainText(text)
        self.auth_button.setEnabled(self.job is not None and text.startswith('CNIG autorización:'))

    def cancel(self):
        if self.job:
            self.job.cancel()
            self.messages.appendPlainText('Cancelación solicitada; se detendrá el proceso activo.')

    def finished(self,path,message):
        self.start.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.auth_button.setEnabled(False)
        self.messages.appendPlainText((message or 'Completado')+'\nResultados y registro: '+path)
        self.job = None
        if not message:
            layer = QgsVectorLayer(str(Path(path)/'metricas.gpkg'),'Inventario LiDAR','ogr')
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)

    def closeEvent(self,event):
        if self.job:
            self.cancel()
            event.ignore()
        else:
            event.accept()

    def reject(self):
        if self.job:
            self.cancel()
        else:
            super().reject()


class Plugin:
    def __init__(self,iface):
        self.iface = iface
        self.dialog = None

    def initGui(self):
        self.action = QAction('Inventario forestal LiDAR',self.iface.mainWindow())
        self.action.triggered.connect(self.open)
        self.iface.addPluginToMenu('Inventario forestal LiDAR',self.action)
        self.iface.addToolBarIcon(self.action)

    def open(self):
        if self.dialog is None:
            self.dialog = Dialog(self.iface)
        self.dialog.show()
        self.dialog.raise_()

    def unload(self):
        if self.dialog and self.dialog.job:
            self.dialog.job.cancel()
        self.iface.removePluginMenu('Inventario forestal LiDAR',self.action)
        self.iface.removeToolBarIcon(self.action)
