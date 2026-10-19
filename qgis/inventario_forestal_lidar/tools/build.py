"""Deterministic QGIS install ZIP, no third-party dependencies."""
from pathlib import Path
import hashlib
import sys
import zipfile
root=Path(__file__).resolve().parents[1]
output=Path(sys.argv[1]) if len(sys.argv)>1 else root/'dist'
output.mkdir(parents=True,exist_ok=True)
archive=output/'inventario_forestal_lidar-0.4.0-experimental.zip'
package=root/'inventario_forestal_lidar'
files=[p for p in package.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        info=zipfile.ZipInfo(str(p.relative_to(root)).replace('\\','/'),date_time=(2026,10,18,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=0o100644<<16
        z.writestr(info,p.read_bytes())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert 'inventario_forestal_lidar/metadata.txt' in z.namelist()
    assert all(n.startswith('inventario_forestal_lidar/') for n in z.namelist())
checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
(archive.with_suffix('.zip.sha256')).write_text(checksum+'  '+archive.name+'\n')
print(archive)
print(checksum)
