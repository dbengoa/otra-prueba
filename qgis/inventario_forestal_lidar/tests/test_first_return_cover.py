import math
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fixtures import write_cloud
from inventario_forestal_lidar.coverage import first_return_cover
from inventario_forestal_lidar.core import Cancelled, digest
from inventario_forestal_lidar.local import MIN_RECORD


def cloud(path, fmt=0, returns=None, zoffset=0):
    # Ground first, low first, exactly-at-cutoff first, canopy first,
    # canopy second and a high-numbered extended return (must NOT count as first).
    returns = returns or [(0, 2, 1), (1, 5, 1), (2, 5, 1), (10, 5, 1),
                          (12, 5, 2), (5, 5, 9 if fmt >= 6 else 3)]
    points = [(400000+i, 4600000+i, z, c) for i, (z, c, rn) in enumerate(returns)]
    write_cloud(path, points)
    data = bytearray(path.read_bytes())
    offset = struct.unpack_from('<I', data, 96)[0]
    header = data[:offset]
    header[104] = fmt
    size = MIN_RECORD[fmt]
    struct.pack_into('<H', header, 105, size)
    struct.pack_into('<d', header, 171, zoffset)
    records = []
    for i, (z, classification, rn) in enumerate(returns):
        rec = bytearray(size)
        struct.pack_into('<iii', rec, 0, (400000+i)*100, (4600000+i)*100,
                         round((z-zoffset)*100))
        # Multiple-return counts and scan/flight flags exercise correct bit masks.
        if fmt < 6:
            rec[14] = rn | (3 << 3) | 128
            rec[15] = classification
        else:
            rec[14] = rn | (9 << 4)
            rec[15] = 128
            rec[16] = classification
        records.append(rec)
    path.write_bytes(header+b''.join(records))


class FirstReturnCoverTests(unittest.TestCase):
    def test_formats_0_to_10_ground_denominator_and_strict_cutoff(self):
        with tempfile.TemporaryDirectory() as d:
            for fmt in range(11):
                with self.subTest(fmt=fmt):
                    p = Path(d)/('format'+str(fmt)+'.las')
                    cloud(p, fmt)
                    before = digest(p)
                    r = first_return_cover(p, 2)
                    self.assertEqual(r['n_primeros_retornos'], 4)
                    self.assertEqual(r['n_primeros_retornos_sobre_corte'], 1)
                    self.assertEqual(r['cobertura_primeros_retornos_pct'], 25)
                    self.assertEqual(r['estado_cobertura'], 'ok')
                    self.assertEqual(before, digest(p))

    def test_scaled_offset_negative_and_fractional_heights(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'scaled.las'
            cloud(p, 6, [(-1, 2, 1), (1.75, 5, 1), (1.76, 5, 1), (0, 2, 1)], zoffset=-100)
            self.assertEqual(first_return_cover(p, 1.75)['cobertura_primeros_retornos_pct'], 25)
            self.assertEqual(first_return_cover(p, 0)['cobertura_primeros_retornos_pct'], 50)

    def test_no_first_returns_is_missing_not_zero(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'no-first.las'
            cloud(p, 6, [(0, 2, 2), (10, 5, 9)])
            r = first_return_cover(p)
            self.assertEqual(r['n_primeros_retornos'], 0)
            self.assertEqual(r['cobertura_primeros_retornos_pct'], '')
            self.assertEqual(r['estado_cobertura'], 'sin_primeros_retornos')

    def test_ground_only_cover_is_real_zero(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'ground.las'
            cloud(p, 0, [(0, 2, 1), (.1, 2, 1)])
            self.assertEqual(first_return_cover(p)['cobertura_primeros_retornos_pct'], 0)
            self.assertEqual(first_return_cover(p)['estado_cobertura'], 'ok')

    def test_bad_cutoffs_and_truncated_input(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'bad.las'
            cloud(p)
            for v in (None, -1, math.nan, math.inf, True):
                with self.subTest(value=v), self.assertRaises(ValueError):
                    first_return_cover(p, v)
            p.write_bytes(p.read_bytes()[:-1])
            with self.assertRaisesRegex(ValueError, 'truncado'):
                first_return_cover(p)

    def test_cancel_and_read_error_are_not_hidden(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'test.las'
            cloud(p)
            def cancel(): raise Cancelled('cancelar')
            with self.assertRaises(Cancelled):
                first_return_cover(p, check=cancel)
            with patch('inventario_forestal_lidar.coverage.LASBlockReader.read_exact', side_effect=OSError('sin acceso')):
                with self.assertRaisesRegex(OSError, 'sin acceso'):
                    first_return_cover(p)
