"""Construir ZIP QGIS reproducible, sin cachés ni datos privados."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import hashlib
root=Path(__file__).resolve().parent
package=root/'modelizacion_forestal_lidar'
out=root/'dist'; out.mkdir(exist_ok=True)
zip_path=out/'modelizacion_forestal_lidar-0.1.0-experimental.zip'
with ZipFile(zip_path,'w',compression=ZIP_DEFLATED) as archive:
    for path in sorted(package.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts or path.suffix=='.pyc': continue
        info=ZipInfo(path.relative_to(root).as_posix(), (2026,10,19,0,0,0))
        info.compress_type=ZIP_DEFLATED; info.external_attr=0o644<<16
        archive.writestr(info,path.read_bytes())
digest=hashlib.sha256(zip_path.read_bytes()).hexdigest()
zip_path.with_suffix('.zip.sha256').write_text(digest+'  '+zip_path.name+'\n')
print(zip_path.name,digest)
