"""Descarga y carga de una tesela PNOA3 ya identificada en el catálogo CNIG.

El adaptador de consulta del catálogo oficial requiere verificación de red.
Este módulo no inventa URLs ni busca coberturas distintas a la tercera.
"""

from pathlib import Path
from urllib.parse import urlparse
import uuid

from qgis.PyQt import sip
from qgis.PyQt.QtCore import QObject, QUrl, pyqtSignal
from qgis.core import QgsFileDownloader, QgsPointCloudLayer, QgsProject, QgsProviderRegistry


def validate_tile(tile):
    if tile.get("coverage") != 3:
        raise ValueError("Solo se permite la tercera cobertura PNOA LiDAR.")
    parsed = urlparse(tile.get("url", ""))
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or parsed.username or parsed.password or not (
        host == "cnig.es" or host.endswith(".cnig.es")
        or host == "ign.es" or host.endswith(".ign.es")
    ):
        raise ValueError("La descarga debe proceder de una URL HTTPS del CNIG/IGN.")
    filename = tile.get("filename", "")
    if not filename or Path(filename).name != filename or "/" in filename or "\\" in filename:
        raise ValueError("Nombre de archivo no válido.")
    if Path(filename).suffix.lower() not in (".las", ".laz"):
        raise ValueError("Se requiere un archivo LAS o LAZ.")
    return filename


def load_point_cloud(path):
    path = Path(path)
    with path.open("rb") as stream:
        if stream.read(4) != b"LASF":
            raise ValueError("El archivo no es LAS/LAZ; puede ser una página HTML del servidor.")
    if QgsProviderRegistry.instance().providerMetadata("pdal") is None:
        raise RuntimeError("Esta instalación de QGIS no dispone del proveedor PDAL para abrir LAS/LAZ.")
    layer = QgsPointCloudLayer(str(path), path.stem, "pdal")
    if not layer.isValid():
        raise RuntimeError("QGIS no pudo abrir la nube de puntos: " + layer.error().message())
    QgsProject.instance().addMapLayer(layer)
    # QGIS/PDAL gestiona la indexación necesaria para visualizar LAS/LAZ.
    return layer


class LidarDownload(QObject):
    progress = pyqtSignal(int)
    ready = pyqtSignal(str)
    failed = pyqtSignal(str)
    closed = pyqtSignal()

    def __init__(self, tile, output_directory, parent=None):
        super().__init__(parent)
        filename = validate_tile(tile)
        directory = Path(output_directory).expanduser()
        if not directory.is_dir():
            raise ValueError("La carpeta de descarga no existe.")
        self.directory = directory / ("PNOA3_" + uuid.uuid4().hex[:12])
        self.directory.mkdir(exist_ok=False)
        self.target = self.directory / filename
        self.partial = self.directory / (filename + ".part")
        self.completed = False
        self.error_reported = False
        self.downloader = QgsFileDownloader(QUrl(tile["url"]), str(self.partial), delayStart=True)
        self.downloader.setParent(self)
        self.downloader.downloadProgress.connect(self.update_progress)
        self.downloader.downloadCompleted.connect(self.complete)
        self.downloader.downloadError.connect(self.report_error)
        self.downloader.downloadExited.connect(self.finish)

    def start(self):
        self.downloader.startDownload()

    def cancel(self):
        downloader = self.downloader
        if downloader is not None and not sip.isdeleted(downloader):
            downloader.cancelDownload()

    def update_progress(self, received, total):
        self.progress.emit(int(100 * received / total) if total > 0 else 0)

    def complete(self):
        try:
            with self.partial.open("rb") as stream:
                if stream.read(4) != b"LASF":
                    raise ValueError("El CNIG no devolvió un archivo LAS/LAZ válido.")
            self.partial.rename(self.target)
            # Conservar una descarga válida si la carga/indexación de QGIS falla.
            self.completed = True
            load_point_cloud(self.target)
            self.ready.emit(str(self.target))
        except Exception as error:
            self.report_error([str(error)])

    def report_error(self, errors):
        if not self.error_reported:
            self.error_reported = True
            self.failed.emit("; ".join(errors))

    def finish(self):
        downloader = self.downloader
        self.downloader = None
        if downloader is not None and not sip.isdeleted(downloader):
            downloader.deleteLater()
        if not self.completed:
            self.partial.unlink(missing_ok=True)
            try:
                self.directory.rmdir()
            except OSError:
                pass
        self.closed.emit()
