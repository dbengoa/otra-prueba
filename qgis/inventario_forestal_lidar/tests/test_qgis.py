import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import tempfile
from pathlib import Path
import unittest
try:
    from qgis.core import QgsApplication,QgsVectorLayer,Qgis
    from osgeo import gdal
    AVAILABLE=True
except ImportError:
    AVAILABLE=False

@unittest.skipUnless(AVAILABLE,'QGIS/GDAL no disponibles en este intérprete')
class QgisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QgsApplication.instance() or QgsApplication([],False)
        cls.app.initQgis()
        print('QGIS probado:',Qgis.QGIS_VERSION)

    def terrain(self,path,nodata=False):
        import numpy as np
        ds=gdal.GetDriverByName('GTiff').Create(str(path),100,100,1,gdal.GDT_Float32)
        ds.SetGeoTransform((-50,1,0,50,0,-1))
        values=np.ones((100,100),dtype=np.float32)*100
        if nodata: values[50,50]=-9999
        ds.GetRasterBand(1).SetNoDataValue(-9999)
        ds.GetRasterBand(1).WriteArray(values)
        ds=None

    def test_terrain_hole_and_complete(self):
        from inventario_forestal_lidar.core import Plot
        from inventario_forestal_lidar.qgis_io import verify_terrain
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'terrain.tif'
            self.terrain(p)
            verify_terrain(p,Plot('a',0,0),15,lambda:None)
            self.terrain(p,True)
            with self.assertRaisesRegex(ValueError,'Huecos'):
                verify_terrain(p,Plot('a',0,0),15,lambda:None)

    def test_gpkg_csv_ids_and_geometry(self):
        from inventario_forestal_lidar.core import token
        from inventario_forestal_lidar.qgis_io import export_results
        with tempfile.TemporaryDirectory() as d:
            rows=[dict(parcela_id=id,x=400000+i,y=4600000,radio_m=15,n_puntos=100,cm_mean='12.3') for i,id in enumerate(('001','A/ñ'))]
            for row in rows:(Path(d)/token(row['parcela_id'])).mkdir()
            export_results(d,rows,25830,lambda:None)
            layer=QgsVectorLayer(str(Path(d)/'metricas.gpkg'),'test','ogr')
            self.assertTrue(layer.isValid())
            self.assertEqual(layer.featureCount(),2)
            self.assertEqual(layer.crs().authid(),'EPSG:25830')
            self.assertEqual({f['parcela_id'] for f in layer.getFeatures()},{'001','A/ñ'})
            for row in rows:
                single=QgsVectorLayer(str(Path(d)/token(row['parcela_id'])/'metricas.gpkg'),'test','ogr')
                self.assertEqual(single.featureCount(),1)
                f=next(single.getFeatures())
                self.assertEqual(f['parcela_id'],row['parcela_id'])
                self.assertEqual(f.geometry().asPoint().x(),row['x'])
                single=None
            layer=None

    def test_dialog_default_radius_and_fusion(self):
        from inventario_forestal_lidar.plugin import Dialog
        from qgis.PyQt.QtWidgets import QMainWindow
        window=QMainWindow()
        class Iface:
            def mainWindow(self):return window
        dialog=Dialog(Iface())
        self.assertEqual(dialog.radius.value(),15)
        self.assertEqual(dialog.fusion.text(),'C:\\FUSION')
        self.assertFalse(dialog.cancel_button.isEnabled())
        dialog.close()

if __name__=='__main__':unittest.main()
