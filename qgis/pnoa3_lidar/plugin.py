"""Clic, consulta de tesela, descarga oficial en navegador y carga automática."""
import re
import os
import json
import time
from pathlib import Path
from functools import partial

from qgis.PyQt import sip
from qgis.PyQt.QtCore import Qt, QTimer, QUrl, QStandardPaths, QSettings
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QInputDialog, QMessageBox
from qgis.core import (QgsApplication, QgsTask, QgsCoordinateTransform,
                       QgsCoordinateReferenceSystem, QgsProject)
from qgis.gui import QgsMapToolEmitPoint

from .catalog import search_tiles
from .download import load_point_cloud
from .conversion import ConversionTask
from .polygon import PolygonTool
from .batch import create_directory, PolygonSearch, BatchDialog


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
        self.conversion_task = None
        self.polygon_task = None
        self.batch_dialog = None
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
        self.load_action = QAction("Convertir LAZ a LAS y cargar archivo…", self.iface.mainWindow())
        self.load_action.triggered.connect(self.load_downloaded)
        self.iface.addPluginToMenu(self.MENU, self.load_action)
        self.configure_action = QAction("Configurar LASzip…", self.iface.mainWindow())
        self.configure_action.triggered.connect(lambda: self.configure_laszip(True))
        self.iface.addPluginToMenu(self.MENU, self.configure_action)
        self.polygon_tool = PolygonTool(self.iface.mapCanvas())
        self.polygon_tool.completed.connect(self.polygon_completed)
        self.polygon_action = QAction("Dibujar polígono y descargar teselas…", self.iface.mainWindow())
        self.polygon_action.triggered.connect(self.activate_polygon)
        self.iface.addPluginToMenu(self.MENU, self.polygon_action)
        self.iface.addToolBarIcon(self.polygon_action)
        self.tool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.tool.setCursor(Qt.CrossCursor)
        self.tool.canvasClicked.connect(self.clicked)
        self.iface.mapCanvas().mapToolSet.connect(self.sync_action)

    def activate_polygon(self):
        if self.searching or self.pending is not None or self.conversion_task is not None or self.polygon_task is not None:
            self.iface.messageBar().pushWarning("PNOA3", "Espera a que termine la operación actual.")
            return
        if self.batch_dialog is not None and self.batch_dialog.alive:
            self.batch_dialog.show()
            self.batch_dialog.raise_()
            return
        self.iface.mapCanvas().setMapTool(self.polygon_tool)
        self.iface.messageBar().pushInfo("PNOA3", "Clic izquierdo: vértices. Clic derecho: terminar (mínimo 3). Escape: borrar dibujo.")

    def polygon_completed(self, geometry):
        if os.name != "nt":
            QMessageBox.warning(self.iface.mainWindow(), "PNOA3", "La creación de carpetas en C:\\ está disponible en Windows.")
            return
        executable = self.configure_laszip()
        if not executable:
            return
        name, ok = QInputDialog.getText(self.iface.mainWindow(), "Carpeta de las teselas",
            "Nombre de una carpeta NUEVA dentro de C:\\ (sin espacios para SilviLiDAR):")
        if not ok:
            return
        if any(char.isspace() for char in name):
            QMessageBox.warning(self.iface.mainWindow(), "PNOA3", "Usa un nombre sin espacios, por ejemplo PNOA_Zona1.")
            return
        try:
            geometry = geometry.clone() if hasattr(geometry, "clone") else type(geometry)(geometry)
            geometry.transform(QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(),
                QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance()))
            folder = create_directory(name)
            self.polygon_task = PolygonSearch(json.loads(geometry.asJson()),
                lambda tiles, error: self.polygon_found(tiles, error, folder, executable))
            QgsApplication.taskManager().addTask(self.polygon_task)
            self.iface.mapCanvas().unsetMapTool(self.polygon_tool)
            self.iface.messageBar().pushInfo("PNOA3", "Carpeta creada: " + str(folder) + ". Buscando todas las teselas que intersectan el polígono…")
        except Exception as error:
            QMessageBox.warning(self.iface.mainWindow(), "PNOA3", "No se pudo preparar la selección: " + str(error))

    def polygon_found(self, tiles, error, folder, executable):
        self.polygon_task = None
        if not self.alive:
            return
        if tiles is None:
            self.report_load_error(error or "Falló la búsqueda del polígono.")
        elif not tiles:
            QMessageBox.information(self.iface.mainWindow(), "PNOA3", "No hay teselas de tercera cobertura en el polígono. La carpeta creada queda vacía.")
        else:
            self.batch_dialog = BatchDialog(self.iface, tiles, folder, executable)
            self.batch_dialog.show()

    def activate(self, checked):
        canvas = self.iface.mapCanvas()
        if checked:
            if canvas.mapTool() is not self.tool:
                self.previous_tool = canvas.mapTool()
            canvas.setMapTool(self.tool)
            self.iface.messageBar().pushInfo("PNOA3", "PNOA3 0.2.0: haz clic para descargar, convertir a LAS y cargar.")
        else:
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
        if self.searching or self.pending is not None or self.conversion_task is not None or self.polygon_task is not None or (self.batch_dialog is not None and self.batch_dialog.alive):
            self.iface.messageBar().pushWarning("PNOA3", "Hay una consulta o descarga pendiente. Comprueba la descarga en el navegador o usa Complementos → PNOA3 LiDAR → Cargar LAS/LAZ ya descargado.")
            return
        if not self.configure_laszip():
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
                self.prepare_cloud(existing)
            except Exception as failure:
                self.report_load_error(failure)
            return
        QMessageBox.information(self.iface.mainWindow(), "Descarga oficial del CNIG",
            "Tesela: " + tile["filename"] + "\n\nSe abrirá su ficha en el navegador. "
            "Pulsa Descargar y completa la autorización del CNIG si la solicita.\n\n"
            "Guarda el LAS/LAZ en: " + str(folder) + "\nEl plugin convertirá el LAZ a LAS en esa carpeta y cargará el LAS.")
        folders = [folder]
        downloads = Path(QStandardPaths.writableLocation(QStandardPaths.DownloadLocation))
        if downloads.is_dir() and downloads.resolve() != folder.resolve():
            folders.append(downloads)
        before = {str(path): (path.stat().st_size, path.stat().st_mtime_ns)
                  for directory in folders for path in directory.iterdir() if path.is_file()}
        self.pending = {"tile": tile, "folder": folder, "folders": folders,
                        "before": before, "started": time.monotonic()}
        self.stable = {}
        if not QDesktopServices.openUrl(QUrl(tile["page_url"])):
            self.pending = None
            self.iface.messageBar().pushCritical("PNOA3", "No se pudo abrir el navegador.")
            return
        self.timer.start()
        self.iface.messageBar().pushInfo("PNOA3", "Esperando " + tile["filename"] + " en: " +
            "; ".join(str(directory) for directory in folders) +
            ". Si lo guardas en otra carpeta, usa Convertir LAZ a LAS y cargar archivo.")

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
        # CNIG puede alternar guiones y guiones bajos en el nombre publicado.
        normalized_stem = stem.replace("-", "_")
        pattern = re.compile(re.escape(normalized_stem) + r"(?: \(\d+\))?" + re.escape(suffix) + "$", re.I)
        folder = self.pending["folder"]
        try:
            for path in (path for directory in self.pending.get("folders", [folder]) for path in directory.iterdir()):
                if not path.is_file() or not pattern.fullmatch(path.name.replace("-", "_")):
                    continue
                info = path.stat()
                fingerprint = (info.st_size, info.st_mtime_ns)
                if self.pending["before"].get(str(path)) == fingerprint or info.st_size < 227:
                    continue
                if any((path.parent / (path.name + extension)).exists() for extension in (".part", ".crdownload", ".tmp")):
                    continue
                previous = self.stable.get(str(path))
                self.stable[str(path)] = (fingerprint, previous[1] + 1 if previous and previous[0] == fingerprint else 0)
                if self.stable[str(path)][1] < 3:
                    continue
                self.stop_watch()
                self.prepare_cloud(path)
                return
        except Exception as error:
            self.stop_watch()
            self.report_load_error(error)

    def configure_laszip(self, force=False):
        settings = QSettings()
        executable = settings.value("pnoa3_lidar/laszip_executable", "", type=str)
        if force or not executable or not Path(executable).is_file():
            QMessageBox.information(self.iface.mainWindow(), "Configurar conversión LAZ a LAS",
                "Selecciona laszip64.exe de la carpeta bin de LAStools (no una DLL). "
                "Se recordará para convertir las descargas. El LAS ocupará más espacio y se conservará el LAZ.")
            selected, unused = QFileDialog.getOpenFileName(self.iface.mainWindow(),
                "Seleccionar laszip64.exe", "", "LASzip (laszip64.exe laszip.exe);;Todos los archivos (*)")
            if not selected:
                self.iface.messageBar().pushWarning("PNOA3", "Configuración cancelada: no se iniciará la conversión automática.")
                return None
            if Path(selected).name.lower() not in ("laszip64.exe", "laszip.exe", "laszip64", "laszip"):
                QMessageBox.warning(self.iface.mainWindow(), "LASzip", "Selecciona el ejecutable laszip64.exe, no una DLL ni otra herramienta.")
                return None
            executable = selected
            settings.setValue("pnoa3_lidar/laszip_executable", executable)
        return executable

    def prepare_cloud(self, path):
        if self.conversion_task is not None:
            self.iface.messageBar().pushWarning("PNOA3", "Hay una conversión en curso.")
            return
        path = Path(path)
        if path.suffix.lower() == ".las":
            load_point_cloud(path)
            self.iface.messageBar().pushSuccess("PNOA3", "LAS cargado: " + str(path))
            return
        executable = self.configure_laszip()
        if not executable:
            self.iface.messageBar().pushWarning("PNOA3", "El LAZ se conserva. Conversión pendiente: configura LASzip y usa Convertir LAZ a LAS y cargar archivo.")
            return
        self.conversion_task = ConversionTask(path, executable, self.conversion_finished)
        QgsApplication.taskManager().addTask(self.conversion_task)
        self.iface.messageBar().pushInfo("PNOA3", "Convirtiendo LAZ a LAS: " + path.name +
            ". Puedes seguir la tarea en el gestor de tareas de QGIS.")

    def conversion_finished(self, path, error):
        self.conversion_task = None
        if not self.alive:
            return
        if path is None:
            self.report_load_error(error or "Falló la conversión.")
            return
        try:
            load_point_cloud(path)
            self.iface.messageBar().pushSuccess("PNOA3", "LAS creado y cargado: " + str(path))
        except Exception as failure:
            self.report_load_error("El LAS se ha guardado en " + str(path) + "\n" + str(failure))

    def report_load_error(self, error):
        message = "El archivo se conserva. No se pudo cargar la nube de puntos:\n\n" + str(error)
        self.iface.messageBar().pushCritical("PNOA3", message)
        QMessageBox.warning(self.iface.mainWindow(), "PNOA3: error de carga", message)

    def load_downloaded(self):
        filename, unused = QFileDialog.getOpenFileName(
            self.iface.mainWindow(), "Cargar nube de puntos descargada",
            str(self.pending["folder"]) if self.pending else
            QStandardPaths.writableLocation(QStandardPaths.DownloadLocation),
            "Nubes de puntos (*.las *.laz *.LAS *.LAZ)")
        if not filename:
            return
        try:
            self.stop_watch()
            self.prepare_cloud(Path(filename))
        except Exception as error:
            self.report_load_error(error)

    def stop_watch(self):
        self.timer.stop()
        self.pending, self.stable = None, {}

    def unload(self):
        self.alive = False
        if self.polygon_task is not None and not sip.isdeleted(self.polygon_task):
            self.polygon_task.cancel()
        if self.batch_dialog is not None:
            self.batch_dialog.close()
        if self.iface.mapCanvas().mapTool() is self.polygon_tool:
            self.iface.mapCanvas().unsetMapTool(self.polygon_tool)
        self.polygon_tool.clear()
        self.iface.mapCanvas().scene().removeItem(self.polygon_tool.band)
        sip.delete(self.polygon_tool.band)
        self.polygon_tool.deleteLater()
        self.iface.removePluginMenu(self.MENU, self.polygon_action)
        self.iface.removeToolBarIcon(self.polygon_action)
        self.polygon_action.deleteLater()
        if self.conversion_task is not None and not sip.isdeleted(self.conversion_task):
            self.conversion_task.cancel()
        self.stop_watch()
        if self.task is not None and not sip.isdeleted(self.task):
            self.task.cancel()
        self.task = None
        self.iface.mapCanvas().mapToolSet.disconnect(self.sync_action)
        if self.iface.mapCanvas().mapTool() is self.tool:
            self.restore_tool()
        self.iface.removePluginMenu(self.MENU, self.configure_action)
        self.configure_action.deleteLater()
        self.iface.removePluginMenu(self.MENU, self.load_action)
        self.load_action.deleteLater()
        self.iface.removePluginMenu(self.MENU, self.action)
        self.iface.removeToolBarIcon(self.action)
        self.action.deleteLater()
        self.tool.deleteLater()
        self.timer.deleteLater()
