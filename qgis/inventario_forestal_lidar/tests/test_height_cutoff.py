import math
import unittest
from inventario_forestal_lidar.core import commands, Plot, validate_height_cutoff, metrics_row

class HeightCutoffTests(unittest.TestCase):
    def command(self, cutoff=None):
        return commands('C:/FUSION','a.laz','a.las','tiles.txt','ground.dtm','raw.las','norm.las','metrics.csv',Plot('001',100,200),15,30,height_cutoff=cutoff)
    def test_switch_only_changes_metrics(self):
        raw=self.command(); filtered=self.command(2)
        self.assertEqual(filtered['metrics'][1:],['/new','/minht:2','norm.las','metrics.csv'])
        for key in ('convert','terrain','raw','normalize'): self.assertEqual(raw[key],filtered[key])
        self.assertIn('/class:2',filtered['terrain'])
    def test_zero_is_filter_and_fraction_uses_decimal_point(self):
        self.assertIn('/minht:0',self.command(0)['metrics'])
        self.assertIn('/minht:1.75',self.command(1.75)['metrics'])
        self.assertNotIn('/minht', ' '.join(self.command()['metrics']))
    def test_invalid_threshold(self):
        for value in (-1, math.nan, math.inf, -math.inf, True, 'abc'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError): validate_height_cutoff(value)
    def test_filtered_metadata_and_ids(self):
        row=metrics_row(Plot('001',1,2),15,100,{'Total return count':'100','Total return count above 2.00':'60','Elev minimum':'2.01','Elev mean':'12'},2)
        self.assertEqual(row['parcela_id'],'001')
        self.assertEqual(row['n_puntos'],100); self.assertEqual(row['n_puntos_metricas'],60)
        self.assertEqual(row['altura_corte_m'],2); self.assertEqual(row['filtro_altura'],'mayor_que')
        self.assertEqual(row['cm_Elev mean'],'12')
    def test_no_filter_metadata(self):
        row=metrics_row(Plot('1',1,2),15,100,{'Elev minimum':'-0.1'})
        self.assertEqual(row['altura_corte_m'],'')
        self.assertEqual(row['filtro_altura'],'sin_filtro')
        self.assertEqual(row['n_puntos_metricas'],100)
    def test_empty_or_inconsistent_metrics_rejected(self):
        for result in ({'Elev minimum':'3'}, {'Total return count above 2.00':'0','Elev minimum':'0'}, {'Total return count above 2.00':'101','Elev minimum':'3'}, {'Total return count above 2.00':'60','Elev minimum':'1'}, {'Total return count above 2.00':'60','Elev minimum':'nan'}):
            with self.assertRaises(ValueError): metrics_row(Plot('1',1,2),15,100,result,2)
