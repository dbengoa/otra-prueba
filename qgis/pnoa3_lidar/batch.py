"""Cola de teselas CNIG con descarga autorizada y conversión secuencial."""
import re
from pathlib import Path
from qgis.PyQt import sip
from qgis.PyQt.QtCore import QTimer, QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton
from qgis.core import QgsTask, QgsApplication
from .catalog import search_geometry
from .conversion import ConversionTask
from .download import load_point_cloud


def matches_tile(filename, tile_filename):
    candidate = Path(filename)
    if candidate.suffix.lower() not in ('.las', '.laz'):
        return False
    stem = re.sub(r' \(\d+\)$', '', candidate.stem)
    normalize = lambda value: re.sub(r'[-_]+', '_', value).casefold()
    return normalize(stem) == normalize(Path(tile_filename).stem)


def create_directory(name, root=Path('C:/')):
    name = name.strip()
    if (not name or name in ('.', '..') or len(name) > 100 or
        re.search(r'[<>:"/\\|?*\x00-\x1f]', name) or name.endswith(('.', ' ')) or
        name.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *('COM'+str(n) for n in range(1,10)), *('LPT'+str(n) for n in range(1,10))}):
        raise ValueError('Nombre de carpeta no válido en Windows. Usa letras, números o guiones.')
    folder = root / name
    folder.mkdir(exist_ok=False)
    return folder


class PolygonSearch(QgsTask):
    def __init__(self, geometry, callback):
        super().__init__('PNOA3: buscar todas las teselas del polígono', QgsTask.CanCancel)
        self.geometry, self.callback, self.tiles, self.error = geometry, callback, [], None

    def run(self):
        try:
            self.tiles = search_geometry(self.geometry, self.isCanceled)
            return not self.isCanceled()
        except Exception as error:
            self.error = str(error)
            return False

    def finished(self, success):
        self.callback(self.tiles if success else None, self.error or ('Consulta cancelada.' if self.isCanceled() else None))


class BatchDialog(QDialog):
    def __init__(self, iface, tiles, folder, executable):
        super().__init__(iface.mainWindow())
        self.iface, self.tiles, self.folder, self.executable = iface, tiles, Path(folder), executable
        self.alive, self.task, self.stable = True, None, {}
        self.states = ['Esperando LAZ/LAS'] * len(tiles)
        self.setWindowTitle('PNOA3 0.2.2 — descarga y conversión por polígono')
        self.resize(850, 450)
        layout = QVBoxLayout(self)
        label = QLabel('Carpeta: ' + str(folder) + '\nAbre cada ficha y descarga en esta carpeta. '
                       'El CNIG puede pedir autorización.\nSe conservan los LAZ y se convierten a LAS uno a uno. '
                       'Mantén esta ventana abierta; cerrarla cancela la cola.')
        label.setWordWrap(True)
        layout.addWidget(label)
        self.table = QTableWidget(len(tiles), 2)
        self.table.setHorizontalHeaderLabels(['Tesela', 'Estado'])
        for row, tile in enumerate(tiles):
            self.table.setItem(row, 0, QTableWidgetItem(tile['filename']))
            self.table.setItem(row, 1, QTableWidgetItem(self.states[row]))
        self.table.setColumnWidth(0, 420)
        self.table.setColumnWidth(1, 350)
        layout.addWidget(self.table)
        button = QPushButton('Abrir ficha CNIG de la tesela seleccionada (o siguiente pendiente)')
        button.clicked.connect(self.open_tile)
        layout.addWidget(button)
        self.diagnostic = QLabel('Vigilancia activa: esperando archivos en ' + str(folder))
        self.diagnostic.setWordWrap(True)
        layout.addWidget(self.diagnostic)
        rescan = QPushButton('Comprobar ahora los archivos descargados')
        rescan.clicked.connect(self.check)
        layout.addWidget(rescan)
        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.check)
        self.timer.start()

    def state(self, row, message):
        self.states[row] = message
        self.table.item(row, 1).setText(message)
        self.table.item(row, 1).setToolTip(message)

    def open_tile(self):
        row = self.table.currentRow()
        if row < 0:
            row = next((i for i, state in enumerate(self.states) if state == 'Esperando LAZ/LAS'), -1)
        if row >= 0 and self.tiles[row].get('page_url'):
            if not QDesktopServices.openUrl(QUrl(self.tiles[row]['page_url'])):
                self.iface.messageBar().pushCritical('PNOA3', 'No se pudo abrir la ficha CNIG.')
            self.table.clearSelection()
            self.table.setCurrentCell(-1, -1)

    def check(self):
        if self.task is not None or not self.alive:
            return
        try:
            files = [path for path in self.folder.iterdir() if path.is_file()]
            matching = sum(any(matches_tile(path.name, tile['filename']) for tile in self.tiles) for path in files)
            self.diagnostic.setText('Comprobando ' + str(self.folder) + ': ' + str(matching) +
                ' archivos LAS/LAZ reconocidos. Espera de estabilidad: unos 6 segundos.')
        except OSError as error:
            self.diagnostic.setText('No se puede leer la carpeta: ' + str(error))
            return
        for row, tile in enumerate(self.tiles):
            if self.states[row] != 'Esperando LAZ/LAS':
                continue
            try:
                candidates = sorted(self.folder.iterdir(), key=lambda p: p.suffix.lower() != '.las')
                for path in candidates:
                    if not path.is_file() or not matches_tile(path.name, tile['filename']):
                        continue
                    info = path.stat()
                    if info.st_size < 227 or any(Path(str(path)+ext).exists() for ext in ('.part','.crdownload','.tmp')):
                        continue
                    fingerprint = (info.st_size, info.st_mtime_ns)
                    previous = self.stable.get(str(path))
                    count = previous[1]+1 if previous and previous[0] == fingerprint else 0
                    self.stable[str(path)] = (fingerprint, count)
                    if count < 3:
                        continue
                    if path.suffix.lower() == '.las':
                        self.tile_done(row, path, None)
                    else:
                        self.state(row, 'Convirtiendo a LAS…')
                        self.task = ConversionTask(path, self.executable,
                            lambda output, error, index=row: self.tile_done(index, output, error))
                        QgsApplication.taskManager().addTask(self.task)
                    return
            except Exception as error:
                self.state(row, 'Error: ' + str(error))

    def tile_done(self, row, path, error):
        self.task = None
        if not self.alive:
            return
        if path is None:
            self.state(row, 'Error de conversión: ' + str(error))
            return
        try:
            load_point_cloud(path)
            self.state(row, 'LAS creado y cargado: ' + Path(path).name)
        except Exception as failure:
            self.state(row, 'LAS guardado; error de carga: ' + str(failure))
        if all(state != 'Esperando LAZ/LAS' and state != 'Convirtiendo a LAS…' for state in self.states):
            self.timer.stop()
            self.iface.messageBar().pushInfo('PNOA3', 'Cola terminada. Revisa los estados de las teselas en la ventana.')

    def reject(self):
        self.stop_queue()
        super().reject()

    def stop_queue(self):
        if not self.alive:
            return
        self.alive = False
        self.timer.stop()
        if self.task is not None and not sip.isdeleted(self.task):
            self.task.cancel()

    def closeEvent(self, event):
        self.stop_queue()
        super().closeEvent(event)
