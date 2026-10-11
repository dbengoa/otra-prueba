"""Descompresión LAZ a LAS con LASzip en una tarea cancelable."""
import os
import subprocess
import tempfile
from pathlib import Path
from qgis.core import QgsTask


def validate_las(path):
    with Path(path).open('rb') as stream:
        header = stream.read(227)
    if len(header) < 227 or header[:4] != b'LASF':
        raise RuntimeError('La conversión no produjo un archivo LAS válido.')
    if header[104] & 0xC0:
        raise RuntimeError('La salida sigue comprimida; se esperaba un LAS sin compresión.')


class ConversionTask(QgsTask):
    def __init__(self, source, executable, callback):
        super().__init__('PNOA3: convertir LAZ a LAS', QgsTask.CanCancel)
        self.source = Path(source)
        target = self.source.with_suffix('.las')
        number = 1
        while target.exists():
            target = self.source.with_name(self.source.stem + '_convertido_' + str(number) + '.las')
            number += 1
        self.target, self.executable, self.callback = target, executable, callback
        self.error, self.process = None, None
        self.temporary = None

    def run(self):
        try:
            with self.source.open('rb') as stream:
                if stream.read(4) != b'LASF':
                    raise RuntimeError('La entrada no es un archivo LAS/LAZ válido.')
            handle, name = tempfile.mkstemp(prefix='.pnoa3_', suffix='.las', dir=str(self.source.parent))
            os.close(handle)
            self.temporary = Path(name)
            with tempfile.TemporaryFile() as log:
                self.process = subprocess.Popen(
                    [self.executable, '-i', str(self.source), '-o', str(self.temporary), '-olas'],
                    stdout=log, stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                while self.process.poll() is None:
                    if self.isCanceled():
                        self.process.terminate()
                        try:
                            self.process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            self.process.kill()
                            self.process.wait()
                        return False
                    try:
                        self.process.wait(timeout=0.25)
                    except subprocess.TimeoutExpired:
                        pass
                log.seek(0, 2)
                log.seek(max(0, log.tell() - 6000))
                output = log.read().decode(errors='replace')
            if self.process.returncode != 0:
                raise RuntimeError('LASzip terminó con código ' + str(self.process.returncode) + ':\n' + output)
            if self.isCanceled():
                return False
            validate_las(self.temporary)
            # Publicación exclusiva: nunca sustituir un LAS del usuario.
            with self.temporary.open('rb') as source, self.target.open('xb') as destination:
                try:
                    while True:
                        if self.isCanceled():
                            raise RuntimeError('Conversión cancelada.')
                        chunk = source.read(8 * 1024 * 1024)
                        if not chunk:
                            break
                        destination.write(chunk)
                except Exception:
                    destination.close()
                    self.target.unlink()
                    raise
            return True
        except Exception as error:
            self.error = str(error)
            return False
        finally:
            if self.temporary is not None:
                self.temporary.unlink(missing_ok=True)

    def finished(self, success):
        self.callback(self.target if success else None,
                      self.error or ('Conversión cancelada.' if self.isCanceled() else None))
