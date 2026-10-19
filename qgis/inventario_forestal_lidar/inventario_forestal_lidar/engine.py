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
import threading
import uuid
from .fusion import PROGRAMS, program, invocation, failure_message
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
    def __init__(self, config, plots, cancelled=lambda:False, progress=lambda n,s:None,retry_authorization=None):
        self.c = config
        self.plots = plots
        self.cancelled = cancelled
        self._progress = progress
        self._last_progress = 0
        self.progress = self.report_progress
        self.retry_authorization = retry_authorization or threading.Event()
        self.state = {'version':VERSION, 'status':'running', 'plots':[], 'tiles':[]}

    def report_progress(self,n,text):
        n=max(self._last_progress,min(100,float(n)))
        self._last_progress=n
        self._progress(n,text)
        if hasattr(self,'logfile'):
            self.log('PROGRESO '+format(n,'.1f')+' '+text)

    def check(self):
        if self.cancelled():
            raise Cancelled('Cancelado por el usuario')

    def log(self, text):
        with self.logfile.open('a', encoding='utf-8') as f:
            f.write(datetime.now(timezone.utc).isoformat()+' '+text+'\n')

    def run_command(self, args):
        self.check()
        args,launch=invocation(args,self.logfile)
        self.state['active_command']=list(map(str,args))
        if hasattr(self,'run'):atomic_json(self.run/'estado.json',self.state)
        self.log('COMANDO '+subprocess.list2cmdline(args))
        started=time.monotonic();last_report=started
        with self.logfile.open('a', encoding='utf-8') as f:
            kwargs = {'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {}
            proc = subprocess.Popen(list(map(str,args)), stdout=f, stderr=subprocess.STDOUT, shell=False, **launch, **kwargs)
            try:
                while proc.poll() is None:
                    self.check()
                    if time.monotonic()-last_report>=10:
                        self.progress(self._last_progress,Path(args[0]).name+' sigue ejecutándose ('+str(int(time.monotonic()-started))+' s)')
                        last_report=time.monotonic()
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
                raise RuntimeError(failure_message(args[0],proc.returncode))
        self.log('COMPLETADO '+Path(args[0]).name+' en '+format(time.monotonic()-started,'.1f')+' s')
        self.check()

    def phase(self,name,plot=None):
        self.state['phase']=name
        self.state['active_plot']=plot
        self.state.pop('active_command',None)
        atomic_json(self.run/'estado.json',self.state)
        self.progress(self._last_progress,name+(' · parcela '+plot if plot is not None else ''))

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
        self.state['config'] = {k:v for k,v in self.c.items() if k not in ('index','files')}
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
            if self.state.get('phase'):
                message='Fallo en '+self.state['phase']+(' · parcela '+self.state['active_plot'] if self.state.get('active_plot') is not None else '')+': '+message
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
        self.phase('Comprobación de FUSION')
        for name in PROGRAMS:
            selected=program(fusion,name)
            if not selected.is_file():raise ValueError('Falta '+str(selected))
            self.progress(0,'FUSION '+name+': '+str(selected))
        if os.name=='nt':
            # Catch the reported startup crash before downloads or expensive conversion.
            self.run_command([str(program(fusion,'ClipData')),'/version'])
        automatic_mode = not self.c.get('files') and not self.c.get('index')
        source_files = self.c.get('files',[])
        if automatic_mode:
            from .cnig import AutomaticSource
            self.state['input_mode'] = 'automatic_cnig'
            self.phase('Consulta y descarga CNIG')
            source = AutomaticSource(root,self.run,self.check,self.progress,self.retry_authorization,download_directory=self.c.get('download_directory'))
            source_files = source.acquire(self.plots,epsg,self.c['radius'],self.c['cell'],self.c.get('support_distance',5.))
            self.state['input_mode'] = 'automatic_cnig'
        local_mode = bool(source_files)
        if local_mode:
            from .local import discover, select_local
            self.phase('Metadatos de las teselas')
            candidates, inventory = discover(source_files,epsg,self.c.get('assume_missing_crs',False),self.check,self.progress)
            atomic_json(self.run/'archivos_locales.json',inventory)
            tiles, mapping = select_local(self.plots,self.c['radius']+2*self.c['cell']+self.c.get('support_distance',5.),candidates)
            self.log('ARCHIVOS LOCALES: metadatos automáticos; procedencia LIDA3 y huellas oficiales no verificadas por cabecera')
            if not automatic_mode:
                self.state['input_mode'] = 'local_files'
        elif self.c.get('index'):
            tiles, mapping = select_tiles(self.plots,self.c['radius']+2*self.c['cell'],read_index(self.c['index'],epsg))
            self.state['input_mode'] = 'legacy_index'
        else:
            raise ValueError('CNIG no proporcionó archivos descargables para las parcelas')
        # Snapshot deliberately excludes temporary or signed download URLs.
        atomic_json(self.run/'teselas.json',[{'key':t.sec,'name':t.name,'bbox':t.bbox,'epsg':t.epsg,'bounds_kind':'point_envelope' if local_mode else 'declared_official_footprint'} for t in tiles])
        laz, las = root/'originales', root/'LAS'
        if not local_mode:
            laz.mkdir(exist_ok=True)
        las.mkdir(exist_ok=True)
        self.phase('Conversión LAZ a LAS')
        paths = {}
        pending = []
        for i,t in enumerate(tiles):
            self.check()
            self.progress(5+30*i/max(1,len(tiles)), 'Descarga/conversión '+t.name)
            if local_mode:
                src = Path(t.source)
                las_header(src,True)
                self.log('ORIGINAL LOCAL (sólo lectura) '+str(src))
            else:
                srcdir = laz/t.sec
                srcdir.mkdir(exist_ok=True)
                src = srcdir/t.name
                flat = laz/t.name
                if not src.exists() and flat.exists():
                    src = flat
                try:
                    self.download(t,src)
                except AuthorizationRequired:
                    pending.append({'sec':t.sec,'name':t.name,'official_page':DETAIL+t.sec,'destination':str(src)})
                    continue
            source_count = las_header(src, True)
            fingerprint = digest(src,self.check)
            if local_mode and fingerprint != t.sha256:
                raise ValueError('El original cambió durante la ejecución: '+t.name)
            out = las/(t.sec+'.las') if local_mode else las/(t.sec+'_'+Path(t.name).stem+'.las')
            receipt = out.with_suffix('.json')
            reusable = False
            if out.exists() and receipt.exists():
                previous = json.loads(receipt.read_text(encoding='utf-8'))
                reusable = previous.get('source_sha256') == fingerprint and previous.get('las_sha256') == digest(out,self.check)
                if reusable:
                    if las_header(out) != source_count:
                        reusable = False
            if not reusable:
                # Work in this run, then atomically replace our derived cache.
                temporary = self.run/(t.sec+'_conversion.las')
                self.run_command([str(program(fusion,'LDA2LAS')),str(src),str(temporary)])
                if las_header(temporary) != source_count:
                    raise ValueError('La conversión perdió puntos: '+t.name)
                temporary.replace(out)
                atomic_json(receipt,{'source_sha256':fingerprint,'las_sha256':digest(out,self.check),'version':VERSION})
            self.progress(5+30*(i+1)/max(1,len(tiles)),
                          ('LAS reutilizado y verificado: ' if reusable else 'LAS convertido y verificado: ')+str(out)+' · '+str(source_count)+' puntos')
            paths[t.sec] = out
            self.state['tiles'].append({'sec':t.sec,'source':str(src),'name':t.name,'source_sha256':fingerprint,'las':str(out),'points':source_count,'status':'verified','reused':reusable})
            atomic_json(self.run/'estado.json',self.state)
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
            self.phase('Comprobación de cobertura',p.id)
            if local_mode:
                from .local import verify_point_support
                report = verify_point_support([paths[t.sec] for t in mapping[p.id]],p,
                    self.c['radius']+2*self.c['cell'],self.c.get('support_distance',5.),self.check)
                atomic_json(work/'cobertura.json',report)
                self.log('COBERTURA MUESTREADA ID='+p.id+' muestras='+str(report['sample_count']))
            listing = work/'teselas.txt'
            listing.write_text('\n'.join(str(paths[t.sec]) for t in mapping[p.id])+'\n',encoding='utf-8')
            terrain, raw, normalized, metrics = [work/n for n in ('mdt.dtm','original.las','normalizada.las','cloudmetrics.csv')]
            cmd = commands(fusion,'','',listing,terrain,raw,normalized,metrics,p,self.c['radius'],zone,self.c['cell'])
            self.phase('MDT clase 2',p.id)
            self.run_command(cmd['terrain'])
            if not terrain.is_file() or not terrain.stat().st_size:
                raise ValueError('FUSION no generó MDT')
            ascii_file = work/'mdt.asc'
            self.phase('Validación del MDT',p.id)
            self.run_command([str(program(fusion,'DTM2ASCII')),'/raster',str(terrain),str(ascii_file)])
            verify_terrain(ascii_file,p,self.c['radius'],self.check)
            self.phase('ClipData: recorte circular',p.id)
            self.run_command(cmd['raw'])
            raw_count = las_header(raw)
            self.phase('ClipData: normalización de alturas',p.id)
            self.run_command(cmd['normalize'])
            count = las_header(normalized)
            if count != raw_count:
                raise ValueError('La normalización perdió puntos para ID '+p.id)
            self.phase('CloudMetrics',p.id)
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
        self.phase('Exportación CSV y GeoPackage')
        export_results(self.run,rows,epsg,self.check)
        self.state['outputs']={'csv':str(self.run/'metricas.csv'),'gpkg':str(self.run/'metricas.gpkg')}
        self.progress(99,'Métricas exportadas: '+str(self.run/'metricas.gpkg'))
