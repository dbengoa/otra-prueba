import unittest
from inventario_forestal_lidar.core import Plot, terrain_clip_command, commands
from inventario_forestal_lidar.fusion import failure_message

class TerrainSubsetTests(unittest.TestCase):
    def test_cross_tile_halo_is_unfiltered_rectangle(self):
        p=Plot('synthetic-edge',500008.5,4600000.5)
        cmd=terrain_clip_command('C:/FUSION','both_tiles.txt','entorno_mdt.las',p,15,1,5)
        self.assertEqual(cmd[1:4],['/shape:0','both_tiles.txt','entorno_mdt.las'])
        self.assertEqual(list(map(float,cmd[-4:])),[499986.5,4599978.5,500030.5,4600022.5])
        self.assertFalse(any(s.startswith(('/height','/minht','/class:')) for s in cmd))
    def test_single_input_retains_ground_class_and_cutoff_only_in_metrics(self):
        c=commands('C:/FUSION','','','entorno_mdt.las','mdt.dtm','raw.las','norm.las','m.csv',Plot('1',0,0),15,30,height_cutoff=2)
        self.assertEqual(c['terrain'][-1],'entorno_mdt.las')
        self.assertIn('/class:2',c['terrain']);self.assertIn('/minht:2',c['metrics'])
        self.assertIn('entorno_mdt.las',c['normalize']);self.assertIn('entorno_mdt.las',c['raw'])
    def test_fail_fast_is_explained_without_claiming_root_cause(self):
        self.assertIn('0xC0000409',failure_message('GridSurfaceCreate64.exe',3221226505))
    def test_invalid_buffer_is_rejected(self):
        with self.assertRaises(ValueError):terrain_clip_command('C:/FUSION','a','b',Plot('1',0,0),15,0)
