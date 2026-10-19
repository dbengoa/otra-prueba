"""ZIP portable determinista y SHA-256. No incluye dependencias ni datos reales."""
from pathlib import Path
import hashlib
import sys
import zipfile
root=Path(__file__).resolve().parent
output=Path(sys.argv[1]) if len(sys.argv)>1 else root/'dist'
output.mkdir(parents=True,exist_ok=True)
archive=output/'modelizacion_lidar-0.1.0-experimental.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for file in sorted(root.rglob('*')):
        relative=file.relative_to(root)
        if not file.is_file() or any(part in ('__pycache__','dist','.git') for part in relative.parts) or file.suffix=='.pyc':continue
        name=str(Path('modelizacion_lidar')/relative).replace('\\','/')
        info=zipfile.ZipInfo(name,date_time=(2026,10,19,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
        z.writestr(info,file.read_bytes())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.zip.sha256').write_text(checksum+'  '+archive.name+'\n')
print(archive);print(checksum)
