"""Cancellable workflow. Original data are never overwritten or deleted."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import csv
import json
import os
import subprocess
import time
import uuid
from .core import (Cancelled, AuthorizationRequired, DETAIL, VERSION, token,
                   validate, read_index, select_tiles, las_header, digest, commands, atomic_json)


def official_url(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'centrodedescargas.cnig.es' or p.username or p.password or p.port not in (None,443):
        raise ValueError('Se requiere un enlace HTTPS oficial de centrodedescargas.cnig.es')
    return url


class OfficialRedirect(__import__('urllib.request', fromlist=['HTTPRedirectHandler']).HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        official_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Engine:
    def __init__(self, config, plots, cancelled=lambda:False, progress=lambda n,s:None):
        self.c = config
        self.plots = plots
        self.cancelled = cancelled
        self.progress = progress
        self.state = {'version':VERSION, 'status':'running', 'plots':[], 'tiles':[]}

    def check(self):
        if self.cancelled():
            raise Cancelled('Cancelado por el usuario')

    def log(self, text):
        with self.logfile.open('a', encoding='utf-8') as f:
            f.write(datetime.now(timezone.utc).isoformat()+' '+text+'\n')

    def run_command(self, args):
        self.check()
        self.log('COMANDO '+subprocess.list2cmdline(list(map(str,args))))
        with self.logfile.open('a', encoding='utf-8') as f:
            kwargs = {'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {}
            proc = subprocess.Popen(list(map(str,args)), stdout=f, stderr=subprocess.STDOUT, shell=False, **kwargs)
            try:
                while proc.poll() is None:
                    self.check()
                    time.sleep(.15)
            except BaseException:
                if os.name == 'nt':
                    subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'], capture_output=True, check=False)
                else:
                    proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                raise
            if proc.returncode != 0:
                raise RuntimeError(Path(args[0]).name+' devolvió '+str(proc.returncode))
        self.check()

    def download(self, tile, destination):
        self.check()
        if destination.exists():
            las_header(destination, True)
            if tile.sha256 and digest(destination).lower() != tile.sha256.lower():
                raise ValueError('SHA256 incorrecto: '+tile.name)
            self.log('REUTILIZADO original '+tile.name)
            return
        if not tile.url:
            raise AuthorizationRequired('Descargue '+tile.name+' en '+str(destination.parent)+' desde '+DETAIL+tile.sec)
        from urllib.request import build_opener
        opener = build_opener(OfficialRedirect())
        self.log('DESCARGA sec='+tile.sec+' '+tile.name)
        partial = destination.with_suffix(destination.suffix+'.part')
        # A fresh partial is used. No unsafe appending without ETag/Content-Range.
        try:
            with opener.open(Request(official_url(tile.url), headers={'User-Agent':'InventarioForestalLiDAR/0.1'}), timeout=30) as response:
                official_url(response.url)
                if response.status != 200:
                    raise AuthorizationRequired('La descarga requiere intervención oficial: '+DETAIL+tile.sec)
                expected = response.headers.get('Content-Length')
                received = 0
                with partial.open('wb') as f:
                    while True:
                        self.check()
                        block = response.read(1024*1024)
                        if not block:
                            break
                        f.write(block)
                        received += len(block)
                if expected and received != int(expected):
                    raise ValueError('Descarga incompleta: '+tile.name)
            try:
                las_header(partial, True)
            except ValueError as e:
                raise AuthorizationRequired('Respuesta sin nube LAS/LAZ; complete la descarga oficial: '+DETAIL+tile.sec) from e
            if tile.sha256 and digest(partial).lower() != tile.sha256.lower():
                raise ValueError('SHA256 incorrecto: '+tile.name)
            partial.replace(destination)
            self.log('DESCARGADO sec='+tile.sec+' bytes='+str(received))
        except HTTPError as e:
            if e.code in (401,403,429):
                raise AuthorizationRequired('Autorización o límite CNIG; abra '+DETAIL+tile.sec) from None
            raise RuntimeError('CNIG HTTP '+str(e.code)+' para sec='+tile.sec) from None

    def execute(self):
        validate(self.plots,self.c['radius'],self.c['output'])
        root = Path(self.c['output'])
        root.mkdir(parents=True,exist_ok=True)
        self.run = root/'resultados'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:8])
        self.run.mkdir(parents=True)
        self.logfile = self.run/'proceso.log'
        self.logfile.touch()
        self.state['config'] = {k:v for k,v in self.c.items() if k != 'index'}
        self.state['started_utc'] = datetime.now(timezone.utc).isoformat()
        try:
            self._execute(root)
            self.state['status'] = 'completed'
            self.progress(100,'Finalizado')
        except Cancelled as e:
            self.state.update(status='cancelled', error=str(e))
            self.log('CANCELADO '+str(e))
            raise
        except AuthorizationRequired as e:
            self.state.update(status='authorization_required', error=str(e))
            self.log('INTERVENCIÓN OFICIAL '+str(e))
            raise
        except Exception as e:
            # Avoid persisting signed download URLs embedded in network exceptions.
            message = str(e) if not ('https://' in str(e) and 'sec=' not in str(e)) else type(e).__name__+'; consulte conexión CNIG'
            self.state.update(status='failed', error=message)
            self.log('ERROR '+message)
            raise RuntimeError(message) from None
        finally:
            self.state['finished_utc'] = datetime.now(timezone.utc).isoformat()
            atomic_json(self.run/'estado.json',self.state)
        return str(self.run)

    def _execute(self, root):
        from .qgis_io import verify_terrain, export_results
        epsg = self.c['epsg']
        if epsg not in (25828,25829,25830,25831,4083):
            raise ValueError('Use ETRS89 UTM 28–31 o REGCAN95 UTM 28 (EPSG:4083)')
        fusion = Path(self.c['fusion'])
        for name in ('LDA2LAS','GridSurfaceCreate','ClipData','CloudMetrics','DTM2ASCII'):
            if not (fusion/(name+'.exe')).is_file():
                raise ValueError('Falta '+str(fusion/(name+'.exe')))
        tiles, mapping = select_tiles(self.plots,self.c['radius']+2*self.c['cell'],read_index(self.c['index'],epsg))
        # Snapshot deliberately excludes temporary or signed download URLs.
        atomic_json(self.run/'teselas.json',[{'sec':t.sec,'name':t.name,'bbox':t.bbox,'epsg':t.epsg} for t in tiles])
        laz, las = root/'originales', root/'LAS'
        laz.mkdir(exist_ok=True)
        las.mkdir(exist_ok=True)
        paths = {}
        pending = []
        for i,t in enumerate(tiles):
            self.check()
            self.progress(5+30*i/max(1,len(tiles)), 'Descarga/conversión '+t.name)
            # sec provides collision-free paths for identically named catalog records.
            srcdir = laz/t.sec
            srcdir.mkdir(exist_ok=True)
            src = srcdir/t.name
            # Flat manually downloaded originals are accepted without moving them.
            flat = laz/t.name
            if not src.exists() and flat.exists():
                src = flat
            try:
                self.download(t,src)
            except AuthorizationRequired:
                pending.append({'sec':t.sec,'name':t.name,'official_page':DETAIL+t.sec,'destination':str(src)})
                continue
            source_count = las_header(src, True)
            fingerprint = digest(src)
            out = las/(t.sec+'_'+Path(t.name).stem+'.las')
            receipt = out.with_suffix('.json')
            reusable = False
            if out.exists() and receipt.exists():
                previous = json.loads(receipt.read_text(encoding='utf-8'))
                reusable = previous.get('source_sha256') == fingerprint and previous.get('las_sha256') == digest(out)
                if reusable:
                    if las_header(out) != source_count:
                        reusable = False
            if not reusable:
                # Work in this run, then atomically replace our derived cache.
                temporary = self.run/(t.sec+'_conversion.las')
                self.run_command([str(fusion/'LDA2LAS.exe'),str(src),str(temporary)])
                if las_header(temporary) != source_count:
                    raise ValueError('La conversión perdió puntos: '+t.name)
                temporary.replace(out)
                atomic_json(receipt,{'source_sha256':fingerprint,'las_sha256':digest(out),'version':VERSION})
            paths[t.sec] = out
            self.state['tiles'].append({'sec':t.sec,'source_sha256':fingerprint,'las':str(out)})
        if pending:
            atomic_json(self.run/'descargas_pendientes.json',pending)
            raise AuthorizationRequired('Faltan '+str(len(pending))+' descargas oficiales. Consulte descargas_pendientes.json y reanude con Ejecutar.')
        rows = []
        zone = 28 if epsg == 4083 else epsg-25800
        for i,p in enumerate(self.plots):
            self.check()
            self.progress(35+60*i/len(self.plots),'Parcela '+p.id)
            work = self.run/token(p.id)
            work.mkdir()
            listing = work/'teselas.txt'
            listing.write_text('\n'.join(str(paths[t.sec]) for t in mapping[p.id])+'\n',encoding='utf-8')
            terrain, raw, normalized, metrics = [work/n for n in ('mdt.dtm','original.las','normalizada.las','cloudmetrics.csv')]
            cmd = commands(fusion,'','',listing,terrain,raw,normalized,metrics,p,self.c['radius'],zone,self.c['cell'])
            self.run_command(cmd['terrain'])
            if not terrain.is_file() or not terrain.stat().st_size:
                raise ValueError('FUSION no generó MDT')
            ascii_file = work/'mdt.asc'
            self.run_command([str(fusion/'DTM2ASCII.exe'),'/raster',str(terrain),str(ascii_file)])
            verify_terrain(ascii_file,p,self.c['radius'],self.check)
            self.run_command(cmd['raw'])
            raw_count = las_header(raw)
            self.run_command(cmd['normalize'])
            count = las_header(normalized)
            if count != raw_count:
                raise ValueError('La normalización perdió puntos para ID '+p.id)
            self.run_command(cmd['metrics'])
            with metrics.open(encoding='utf-8-sig',newline='') as f:
                result = list(csv.DictReader(f))
            if len(result) != 1:
                raise ValueError('CloudMetrics debe producir exactamente una fila por parcela')
            row = {'parcela_id':p.id,'x':p.x,'y':p.y,'radio_m':self.c['radius'],'n_puntos':count,**{'cm_'+k:v for k,v in result[0].items()}}
            rows.append(row)
            with (work/'metricas.csv').open('w',encoding='utf-8-sig',newline='') as f:
                writer = csv.DictWriter(f,fieldnames=list(row))
                writer.writeheader()
                writer.writerow(row)
            self.state['plots'].append({'id':p.id,'directory':work.name,'points':count,'status':'completed'})
            atomic_json(self.run/'estado.json',self.state)
        self.check()
        export_results(self.run,rows,epsg,self.check)
