"""Download through the official CNIG page in an isolated Google Chrome profile.

The plugin clicks the page's real download control. It never constructs CAPTCHA
responses, accepts licences, reads cookies, or calls the binary endpoint directly.
"""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from .cdp import CDP
from .core import AuthorizationRequired, las_header

BASE='https://centrodedescargas.cnig.es/CentroDescargas/'


def chrome_candidates(windows=None,environ=None,which=None):
    windows=os.name=='nt' if windows is None else windows
    environ=os.environ if environ is None else environ
    which=shutil.which if which is None else which
    candidates=[]
    if windows:
        for name in ('PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA'):
            root=environ.get(name)
            if root:candidates.append(Path(root)/'Google/Chrome/Application/chrome.exe')
    names=('chrome','google-chrome','google-chrome-stable')
    if not windows:names+=('chromium','chromium-browser')
    for name in names:
        found=which(name)
        if found:candidates.append(Path(found))
    return list(dict.fromkeys(candidates))


def executable():
    for path in chrome_candidates():
        if path.is_file():return str(path)
    raise RuntimeError('No se encontró Google Chrome. Instale Chrome y vuelva a ejecutar; esta versión no cambia automáticamente a Microsoft Edge.')


class OfficialBrowser:
    def __init__(self,work,check=lambda:None,progress=lambda s:None,retry=None,*,headless=False):
        self.work=Path(work)
        self.check=check;self.progress=progress
        self.retry=retry or threading.Event()
        self.headless=headless
        self.proc=None;self.cdp=None;self.temp=None

    def __enter__(self):
        try:
            self.temp=tempfile.TemporaryDirectory(prefix='inventario_cnig_browser_')
            self.profile=Path(self.temp.name)
            self.staging=self.profile/'downloads';self.staging.mkdir()
            self.launch()
            return self
        except BaseException:
            self.__exit__(None,None,None);raise

    def launch(self):
        program=executable()
        self.progress('CNIG navegador: Google Chrome ('+Path(program).name+')')
        args=[program,'--remote-debugging-port=0','--remote-debugging-address=127.0.0.1',
              '--user-data-dir='+str(self.profile),'--no-first-run','--no-default-browser-check',
              '--disable-background-mode','--new-window','about:blank']
        if self.headless:args.insert(1,'--headless=new')
        self.proc=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        active=self.profile/'DevToolsActivePort'
        deadline=time.monotonic()+30
        while not active.is_file():
            self.check()
            if self.proc.poll() is not None:raise RuntimeError('El navegador CNIG terminó durante el arranque')
            if time.monotonic()>deadline:raise TimeoutError('No se pudo iniciar la sesión privada de navegador CNIG')
            time.sleep(.1)
        lines=active.read_text().splitlines()
        if len(lines)<2 or not lines[0].isdigit() or not lines[1].startswith('/devtools/browser/'):
            raise ValueError('Puerto de navegador CNIG no válido')
        self.cdp=CDP('ws://127.0.0.1:'+lines[0]+lines[1],self.check)
        self.target=self.cdp.call('Target.createTarget',{'url':'about:blank'})['targetId']
        self.session=self.cdp.call('Target.attachToTarget',{'targetId':self.target,'flatten':True})['sessionId']
        self.cdp.call('Page.enable',session=self.session)
        self.cdp.call('Browser.setDownloadBehavior',{'behavior':'allowAndName','downloadPath':str(self.staging),'eventsEnabled':True})

    def navigate(self,url):
        if not url.startswith(BASE):raise ValueError('La navegación de descarga debe ser oficial CNIG')
        result=self.cdp.call('Page.navigate',{'url':url},self.session)
        if result.get('errorText'):raise RuntimeError('No se pudo cargar la ficha CNIG: '+result['errorText'])
        self.frame=result.get('frameId')

    def ready(self,sec):
        # Return only status, never a cookie, token, password or page contents.
        expression='''(()=>{const s=document.getElementById('secuencial');
          const series=document.getElementById('codSerie');
          const b=document.getElementById('bDescDir');
          return {ready:document.readyState==='complete'&&!!b&&!!s&&!!series,
                  sec:s?s.value:'',series:series?series.value:'',origin:location.origin};})()'''
        try:status=self.cdp.evaluate(expression,self.session)
        except RuntimeError:return False
        if not status or not status['ready']:return False
        if status['origin']!='https://centrodedescargas.cnig.es' or str(status['sec'])!=sec or status['series']!='LIDA3':
            raise ValueError('La ficha del navegador no corresponde a la tesela PNOA3 solicitada')
        return True

    def click(self):
        # Ordinary DOM activation of the OFFICIAL handler runs its reCAPTCHA,
        # preAutorizarDescarga, licence UI, and form submission unchanged.
        self.cdp.evaluate("document.getElementById('bDescDir').click(); true",self.session)

    def download(self,record,destination):
        sec=str(record['sec'])
        if not sec.isdigit():raise ValueError('Identificador CNIG inválido')
        destination=Path(destination)
        destination.parent.mkdir(parents=True,exist_ok=True)
        if destination.exists():
            las_header(destination,True)
            self.progress('CNIG reutiliza '+destination.name)
            return destination
        self.retry.clear()
        self.progress('CNIG abre autorización oficial para '+record['name'])
        self.navigate(BASE+'detalleArchivo?sec='+sec)
        deadline=time.monotonic()+120
        while not self.ready(sec):
            self.check()
            if time.monotonic()>deadline:
                raise AuthorizationRequired('La ficha CNIG no cargó. Compruebe la conexión en la ventana del navegador y vuelva a ejecutar.')
            time.sleep(.2)
        self.click()
        guid=None;started=time.monotonic();last=started;received_last=-1;last_report=0
        self.progress('CNIG autorización: si el portal lo solicita, complete CAPTCHA/licencia en el navegador. Después pulse «Continuar autorización» en QGIS.')
        while True:
            self.check()
            if self.proc.poll() is not None:raise AuthorizationRequired('Se cerró el navegador de autorización CNIG; vuelva a ejecutar para continuar.')
            if not guid and time.monotonic()-started>900:
                raise AuthorizationRequired('Expiró la espera de autorización CNIG (15 minutos). Vuelva a ejecutar; se conservan las teselas descargadas.')
            if time.monotonic()-last>600:
                raise TimeoutError('La descarga CNIG no avanzó en diez minutos. Se conservan los originales completos.')
            if self.retry.is_set() and not guid:
                self.retry.clear()
                if self.ready(sec):self.click()
            event=self.cdp.event()
            if not event:continue
            params=event.get('params',{})
            if event['method']=='Browser.downloadWillBegin':
                if guid:raise RuntimeError('Descarga adicional inesperada en el navegador CNIG')
                if params.get('frameId')!=self.frame:
                    self.cdp.call('Browser.cancelDownload',{'guid':params['guid']})
                    raise ValueError('La descarga no procede de la ficha CNIG activa')
                candidate=params.get('guid','')
                if not re.fullmatch(r'[A-Za-z0-9-]+',candidate):raise ValueError('Identificador de descarga inválido')
                # Catalog uses hyphens while Content-Disposition may use underscores.
                normalize=lambda n:n.replace('_','-').upper()
                if normalize(params.get('suggestedFilename',''))!=normalize(record['name']):
                    self.cdp.call('Browser.cancelDownload',{'guid':candidate})
                    raise ValueError('CNIG ofreció un archivo distinto de la tesela solicitada')
                guid=candidate;last=time.monotonic()
                self.progress('CNIG descargando '+record['name'])
            elif event['method']=='Browser.downloadProgress' and params.get('guid')==guid:
                received=int(params.get('receivedBytes',0))
                if received>received_last:
                    received_last=received;last=time.monotonic()
                if time.monotonic()-last_report>2:
                    total=int(params.get('totalBytes',0))
                    self.progress('CNIG descargando '+record['name']+': '+format(received/1048576,'.1f')+' MiB'+(' / '+format(total/1048576,'.1f')+' MiB' if total else ''))
                    last_report=time.monotonic()
                if params.get('state')=='canceled':raise RuntimeError('CNIG o el navegador cancelaron la descarga de '+record['name'])
                if params.get('state')=='completed':
                    part=self.staging/guid
                    # Browser reports completion only after closing/renaming the file.
                    las_header(part,True)
                    # Browser profile is in private local TEMP; output may be Q:/NAS.
                    # Copy in cancellable blocks, then commit on the destination volume.
                    staging=destination.with_suffix(destination.suffix+'.part')
                    written=0
                    with part.open('rb') as source,staging.open('wb') as target:
                        while True:
                            self.check();block=source.read(1024*1024)
                            if not block:break
                            target.write(block);written+=len(block)
                    if written!=part.stat().st_size:raise ValueError('Copia de descarga incompleta')
                    las_header(staging,True)
                    if destination.exists():raise ValueError('El original apareció durante la descarga; se conserva y no se sobrescribe')
                    staging.replace(destination)
                    self.progress('CNIG descargado '+record['name'])
                    return destination

    def __exit__(self,*args):
        # Close only the browser instance launched with our disposable profile.
        if self.cdp:
            self.cdp.check=lambda:None
            self.cdp.ws.check=lambda:None
            try:self.cdp.call('Browser.close',timeout=3)
            except Exception:pass
            self.cdp.close()
        if self.proc:
            try:self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                if os.name=='nt':
                    subprocess.run(['taskkill','/PID',str(self.proc.pid),'/T','/F'],capture_output=True,check=False)
                else:self.proc.terminate()
                try:self.proc.wait(timeout=3)
                except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait()
        if self.temp:
            try:self.temp.cleanup()
            except OSError:
                # Windows may briefly retain a browser file lock. Never touch originals.
                pass
