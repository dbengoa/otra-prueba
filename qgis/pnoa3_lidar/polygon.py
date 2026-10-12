"""Dibujo de un polígono sobre el mapa."""
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsGeometry, QgsPointXY, QgsWkbTypes
from qgis.gui import QgsMapTool, QgsRubberBand


class PolygonTool(QgsMapTool):
    completed = pyqtSignal(object)

    def __init__(self, canvas):
        super().__init__(canvas)
        self.points = []
        self.band = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)
        self.band.setColor(QColor(30, 170, 80, 80))
        self.band.setWidth(2)
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.points.append(QgsPointXY(self.toMapCoordinates(event.pos())))
            self.draw()
        elif event.button() == Qt.RightButton and len(self.points) >= 3:
            geometry = QgsGeometry.fromPolygonXY([self.points + [self.points[0]]])
            if not geometry.isGeosValid() or geometry.area() <= 0:
                return
            self.completed.emit(geometry)
            self.clear()

    def canvasMoveEvent(self, event):
        if self.points:
            self.draw(QgsPointXY(self.toMapCoordinates(event.pos())))

    def draw(self, preview=None):
        points = self.points + ([preview] if preview else [])
        if len(points) >= 2:
            self.band.setToGeometry(QgsGeometry.fromPolygonXY([points + [points[0]]]), None)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.clear()

    def clear(self):
        self.points = []
        self.band.reset(QgsWkbTypes.PolygonGeometry)

    def deactivate(self):
        self.clear()
        super().deactivate()
