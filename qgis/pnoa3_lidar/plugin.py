"""Clic, consulta de tesela, descarga oficial en navegador y carga automática."""
import re
import time
from pathlib import Path
from functools import partial

from qgis.PyQt import sip
from qgis.PyQt.QtCore import Qt, QTimer, QUrl, QStandardPaths
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QInputDialog, QMessageBox
from qgis.core import (QgsApplication, QgsTask, QgsCoordinateTransform,
                       QgsCoordinateReferenceSystem, QgsProject)
from qgis.gui import QgsMapToolEmitPoint

from .catalog import search_tiles
from .download import load_point_cloud


class SearchTask(QgsTask):
    def __init__(self, lon, lat, callback):
        super().__init__("Buscar tesela PNOA3 en CNIG", QgsTask.CanCancel)
        self.lon, self.lat, self.callback = lon, lat, callback
        self.tiles, self.error = [], None

    def run(self):
        try:
            self.tiles = search_tiles(self.lon, self.lat)
            return not self.isCanceled()
        except Exception as error:
            self.error = str(error)
            return False

    def finished(self, success):
        if not self.isCanceled():
            self.callback(self.tiles if success else None, self.error)


class PNOA3Plugin:
    MENU = "&PNOA3 LiDAR"

    def __init__(self, iface):
        self.iface, self.action, self.tool, self.previous_tool = iface, None, None, None
        self.alive, self.searching, self.task = True, False, None
        self.search_token = 0
        self.pending, self.stable = None, {}
        self.timer = QTimer(iface.mainWindow())
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.check_download)

    def initGui(self):
        self.action = QAction(QIcon(str(Path(__file__).with_name("icon.svg"))),
                              "Descargar PNOA3 en un punto", self.iface.mainWindow())
        self.action.setCheckable(True)
        self.action.triggered.connect(self.activate)
        self.iface.addPluginToMenu(self.MENU, self.action)
        self.iface.addToolBarIcon(self.action)
        self.tool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.tool.setCursor(Qt.CrossCursor)
        self.tool.canvasClicked.connect(self.clicked)
        self.iface.mapCanvas().mapToolSet.connect(self.sync_action)

    def activate(self, checked):
        canvas = self.iface.mapCanvas()
        if checked:
            if canvas.mapTool() is not self.tool:
                self.previous_tool = canvas.mapTool()
            canvas.setMapTool(self.tool)
            self.iface.messageBar().pushInfo("PNOA3", "Haz clic para localizar la tesela del CNIG.")
        else:
            self.stop_watch()
            if self.task is not None and not sip.isdeleted(self.task):
                self.task.cancel()
            self.search_token += 1
            self.searching, self.task = False, None
            if canvas.mapTool() is self.tool:
                self.restore_tool()

    def sync_action(self, *unused):
        if self.action is not None:
            self.action.setChecked(self.iface.mapCanvas().mapTool() is self.tool)

    def restore_tool(self):
        canvas = self.iface.mapCanvas()
        if self.previous_tool is not None and not sip.isdeleted(self.previous_tool):
            canvas.setMapTool(self.previous_tool)
        else:
            canvas.unsetMapTool(self.tool)
            self.iface.actionPan().trigger()

    def clicked(self, point, button):
        if button != Qt.LeftButton:
            return
        if self.searching or self.pending is not None:
            self.iface.messageBar().pushWarning("PNOA3", "Hay una consulta o descarga pendiente. Espera o desactiva el plugin para cancelarla.")
            return
        folder = QFileDialog.getExistingDirectory(
            self.iface.mainWindow(), "Carpeta donde el navegador guardará el LAS/LAZ",
            QStandardPaths.writableLocation(QStandardPaths.DownloadLocation),
        )
        if not folder:
            return
        try:
            transform = QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(),
                QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance())
            geographic = transform.transform(point)
            self.searching = True
            self.search_token += 1
            token = self.search_token
            self.task = SearchTask(geographic.x(), geographic.y(),
                                   lambda tiles, error: self.found(tiles, error, Path(folder), token))
            self.task.taskCompleted.connect(partial(self.search_done, token))
            self.task.taskTerminated.connect(partial(self.search_done, token))
            self.task.destroyed.connect(partial(self.search_done, token))
            QgsApplication.taskManager().addTask(self.task)
            self.iface.messageBar().pushInfo("PNOA3", "Consultando la tercera cobertura del CNIG…")
        except Exception as error:
            self.searching = False
            self.iface.messageBar().pushCritical("PNOA3", str(error))

    def search_done(self, token, *unused):
        if token == self.search_token:
            self.searching, self.task = False, None

    def found(self, tiles, error, folder, token):
        if not self.alive or token != self.search_token:
            return
        self.search_done(token)
        if tiles is None:
            self.iface.messageBar().pushCritical("PNOA3", error or "Falló la consulta CNIG.")
            return
        if not tiles:
            self.iface.messageBar().pushWarning("PNOA3", "El CNIG no ofrece una tesela de tercera cobertura en este punto.")
            return
        tile = tiles[0]
        if len(tiles) > 1:
            names = [tile["filename"] for tile in tiles]
            selected, ok = QInputDialog.getItem(self.iface.mainWindow(), "PNOA3", "Teselas coincidentes:", names, 0, False)
            if not ok:
                return
            tile = tiles[names.index(selected)]
        existing = folder / tile["filename"]
        if existing.is_file() and QMessageBox.question(self.iface.mainWindow(), "PNOA3",
                "La tesela ya está en esa carpeta. ¿Cargarla?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                load_point_cloud(existing)
            except Exception as failure:
                self.iface.messageBar().pushCritical("PNOA3", str(failure))
            return
        QMessageBox.information(self.iface.mainWindow(), "Descarga oficial del CNIG",
            "Tesela: " + tile["filename"] + "\n\nSe abrirá su ficha en el navegador. "
            "Pulsa Descargar y completa la autorización del CNIG si la solicita.\n\n"
            "Guarda el LAS/LAZ en: " + str(folder) + "\nQGIS lo cargará al terminar. No hace falta descomprimir LAZ.")
        before = {path.name: (path.stat().st_size, path.stat().st_mtime_ns)
                  for path in folder.iterdir() if path.is_file()}
        self.pending = {"tile": tile, "folder": folder, "before": before, "started": time.monotonic()}
        self.stable = {}
        if not QDesktopServices.openUrl(QUrl(tile["page_url"])):
            self.pending = None
            self.iface.messageBar().pushCritical("PNOA3", "No se pudo abrir el navegador.")
            return
        self.timer.start()

    def check_download(self):
        if self.pending is None:
            self.timer.stop()
            return
        if time.monotonic() - self.pending["started"] > 3600:
            self.stop_watch()
            self.iface.messageBar().pushWarning("PNOA3", "Se agotó la espera de la descarga. Vuelve a hacer clic para reintentar.")
            return
        filename = self.pending["tile"]["filename"]
        stem, suffix = Path(filename).stem, Path(filename).suffix
        pattern = re.compile(re.escape(stem) + r"(?: \(\d+\))?" + re.escape(suffix) + "$", re.I)
        folder = self.pending["folder"]
        try:
            for path in folder.iterdir():
                if not path.is_file() or not pattern.fullmatch(path.name):
                    continue
                info = path.stat()
                fingerprint = (info.st_size, info.st_mtime_ns)
                if self.pending["before"].get(path.name) == fingerprint or info.st_size < 227:
                    continue
                if any((folder / (path.name + extension)).exists() for extension in (".part", ".crdownload", ".tmp")):
                    continue
                previous = self.stable.get(path.name)
                self.stable[path.name] = (fingerprint, previous[1] + 1 if previous and previous[0] == fingerprint else 0)
                if self.stable[path.name][1] < 3:
                    continue
                load_point_cloud(path)
                self.stop_watch()
                self.iface.messageBar().pushSuccess("PNOA3", "Nube de puntos cargada: " + str(path))
                return
        except Exception as error:
            self.stop_watch()
            self.iface.messageBar().pushCritical("PNOA3", "El archivo se conserva. No se pudo cargar: " + str(error))

    def stop_watch(self):
        self.timer.stop()
        self.pending, self.stable = None, {}

    def unload(self):
        self.alive = False
        self.stop_watch()
        if self.task is not None and not sip.isdeleted(self.task):
            self.task.cancel()
        self.task = None
        self.iface.mapCanvas().mapToolSet.disconnect(self.sync_action)
        if self.iface.mapCanvas().mapTool() is self.tool:
            self.restore_tool()
        self.iface.removePluginMenu(self.MENU, self.action)
        self.iface.removeToolBarIcon(self.action)
        self.action.deleteLater()
        self.tool.deleteLater()
        self.timer.deleteLater()
