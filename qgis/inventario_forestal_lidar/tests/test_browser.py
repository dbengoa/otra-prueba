"""Opt-in real Chromium/CDP test against a loopback fixture, never CNIG CAPTCHA.

Set LIDAR_BROWSER_TEST_EXE to Edge/Chrome/Chromium to run. The local server serves
synthetic LAS bytes and an approval flag; this does NOT test official authorization.
"""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
import os
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from fixtures import write_cloud
from inventario_forestal_lidar.browser import OfficialBrowser
from inventario_forestal_lidar.core import Cancelled,las_header

EXE=os.environ.get('LIDAR_BROWSER_TEST_EXE')


@unittest.skipUnless(EXE,'Navegador real: active LIDAR_BROWSER_TEST_EXE para test local CDP')
class BrowserTests(unittest.TestCase):
    def scenario(self,wrong_name=False,cancel=False):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/'source.las';write_cloud(src)
            body=src.read_bytes()
            posts=[]
            class Handler(BaseHTTPRequestHandler):
                def log_message(self,*args):pass
                def do_GET(self):
                    if self.path!='/detail':self.send_error(404);return
                    page=b'''<!doctype html><meta charset="utf-8"><input id="secuencial" value="1"><input id="codSerie" value="LIDA3">
                    <form id="download" method="POST" action="/download"></form>
                    <button id="bDescDir" onclick="if(window.approved){document.getElementById('download').submit();}else{document.title='Approval required';}">Download</button>
                    <script>window.approved=false;</script>'''
                    self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(page)));self.end_headers();self.wfile.write(page)
                def do_POST(self):
                    posts.append(self.path)
                    filename='wrong.laz' if wrong_name else 'PNOA_2024_TEST_400-4601_H30_NPC01.LAZ'
                    self.send_response(200);self.send_header('Content-Type','application/octet-stream')
                    self.send_header('Content-Disposition','attachment; filename="'+filename+'"')
                    self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
            server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            started=time.monotonic();cancelled=False;approval_seen=[]
            def check():
                if cancelled:raise Cancelled('test cancellation')
                if time.monotonic()-started>60:raise TimeoutError('Browser fixture test exceeded 60 seconds')
            class LocalBrowser(OfficialBrowser):
                def navigate(self,url):
                    result=self.cdp.call('Page.navigate',{'url':f'http://127.0.0.1:{server.server_port}/detail'},self.session)
                    self.frame=result['frameId']
                def ready(self,sec):
                    try:return self.cdp.evaluate("document.readyState==='complete' && !!document.getElementById('bDescDir')",self.session)
                    except RuntimeError:return False
            retry=threading.Event()
            browser=LocalBrowser(root,check=check,retry=retry,headless=True)
            def progress(text):
                nonlocal cancelled
                if text.startswith('CNIG autorización:'):
                    # The first click MUST NOT have caused a binary request.
                    self.assertEqual(posts,[])
                    approval_seen.append(True)
                    if cancel:cancelled=True
                    else:
                        browser.cdp.evaluate('window.approved=true',browser.session)
                        retry.set()
            browser.progress=progress
            try:
                with patch('inventario_forestal_lidar.browser.executable',return_value=EXE):
                    with browser:
                        dest=root/'output'/'tile.laz'
                        if cancel:
                            with self.assertRaises(Cancelled):browser.download(dict(sec='1',name='PNOA-2024-TEST-400-4601-H30-NPC01.LAZ'),dest)
                        elif wrong_name:
                            with self.assertRaisesRegex(ValueError,'distinto'):browser.download(dict(sec='1',name='PNOA-2024-TEST-400-4601-H30-NPC01.LAZ'),dest)
                        else:
                            browser.download(dict(sec='1',name='PNOA-2024-TEST-400-4601-H30-NPC01.LAZ'),dest)
                            self.assertEqual(dest.read_bytes(),body)
                            self.assertEqual(las_header(dest,True),2)
                self.assertTrue(approval_seen)
                self.assertIsNotNone(browser.proc.poll())
                self.assertEqual(posts,[] if cancel else ['/download'])
            finally:
                server.shutdown();server.server_close();thread.join(timeout=3)

    def test_browser_waits_for_approval_then_downloads(self):self.scenario()
    def test_browser_rejects_unexpected_filename(self):self.scenario(wrong_name=True)
    def test_browser_cancellation_closes_dedicated_instance(self):self.scenario(cancel=True)

if __name__=='__main__':unittest.main()
