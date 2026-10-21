import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
try:
    from qgis.core import QgsApplication, QgsVectorLayer, QgsFeature, QgsGeometry, NULL
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


@unittest.skipUnless(AVAILABLE, 'QGIS no disponible en este intérprete')
class PointLayersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)
        cls.app.initQgis()

    def layer(self, kind, data):
        layer = QgsVectorLayer(kind+'?crs=EPSG:25830&field=id:string', 'centros', 'memory')
        for identifier, wkt in data:
            f = QgsFeature(layer.fields())
            f['id'] = identifier
            if wkt is not None:
                f.setGeometry(QgsGeometry.fromWkt(wkt))
            self.assertTrue(layer.dataProvider().addFeatures([f])[0])
        return layer

    def test_points_and_singleton_multipoints_preserve_ids_and_source(self):
        from inventario_forestal_lidar.qgis_io import read_plot_centers
        for kind, wkt in [('Point','POINT (400000 4600000)'),
                          ('PointZ','POINT Z (400000 4600000 100)'),
                          ('PointM','POINT M (400000 4600000 7)'),
                          ('MultiPoint','MULTIPOINT ((400000 4600000))'),
                          ('MultiPointZM','MULTIPOINT ZM ((400000 4600000 100 7))')]:
            with self.subTest(kind=kind):
                layer = self.layer(kind, [('0042',wkt)])
                before = next(layer.getFeatures()).geometry().asWkt()
                points, origins = read_plot_centers(layer, 'id')
                self.assertEqual(points[0].id, '0042')
                self.assertEqual((points[0].x,points[0].y), (400000,4600000))
                self.assertEqual(origins[0]['id_origen'], '0042')
                self.assertEqual(next(layer.getFeatures()).geometry().asWkt(), before)

    def test_real_multipoint_requires_opt_in_and_keeps_mapping(self):
        from inventario_forestal_lidar.qgis_io import read_plot_centers
        layer = self.layer('MultiPoint', [('0042','MULTIPOINT ((1 2),(3 4))')])
        with self.assertRaisesRegex(ValueError, 'contiene 2 puntos'):
            read_plot_centers(layer, 'id')
        points, origins = read_plot_centers(layer, 'id', True)
        self.assertEqual([p.id for p in points], ['0042__p1','0042__p2'])
        self.assertEqual([(p.x,p.y) for p in points], [(1,2),(3,4)])
        self.assertEqual([o['parte'] for o in origins], [1,2])
        self.assertTrue(all(o['id_origen']=='0042' for o in origins))
        self.assertEqual(layer.featureCount(), 1)

    def test_generated_ids_cannot_collide_with_original_ids(self):
        from inventario_forestal_lidar.qgis_io import read_plot_centers
        layer = self.layer('MultiPoint', [('a','MULTIPOINT ((1 2),(3 4))'),
                                          ('a__p1','MULTIPOINT ((5 6))')])
        with self.assertRaisesRegex(ValueError, 'Colisión.*a__p1'):
            read_plot_centers(layer, 'id', True)

    def test_bad_geometry_ids_and_empty_layer_are_diagnosed(self):
        from inventario_forestal_lidar.qgis_io import read_plot_centers
        cases = [([], 'no contiene'), ([('1',None)], 'vacía'),
                 ([('1','MULTIPOINT EMPTY')], 'vacía'),
                 ([(NULL,'MULTIPOINT ((1 2))')], 'nulo'),
                 ([(' ','MULTIPOINT ((1 2))')], 'vacío'),
                 ([('1','MULTIPOINT ((1 2))'),('1','MULTIPOINT ((3 4))')], 'duplicado')]
        for data, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    read_plot_centers(self.layer('MultiPoint',data), 'id', True)
        with self.assertRaisesRegex(ValueError, 'no es Point/MultiPoint'):
            read_plot_centers(self.layer('LineString',[('1','LINESTRING (1 2,3 4)')]), 'id')
