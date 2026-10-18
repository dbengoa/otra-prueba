"""Small stdlib CDP client over loopback, with cancellation and bounded messages.

No browser credentials are read. Used only with a new dedicated browser profile.
"""
from collections import deque
import base64
import hashlib
import json
import os
import socket
import struct
import time
from urllib.parse import urlparse


class WebSocket:
    def __init__(self,url,check=lambda:None):
        p=urlparse(url)
        if p.scheme!='ws' or p.hostname not in ('127.0.0.1','localhost'):
            raise ValueError('CDP sólo admite loopback local')
        self.check=check
        self.sock=socket.create_connection((p.hostname,p.port),timeout=5)
        self.sock.settimeout(.25)
        self.buffer=bytearray()
        self.fragment=bytearray()
        key=base64.b64encode(os.urandom(16)).decode('ascii')
        path=p.path+('?' + p.query if p.query else '')
        request=(f'GET {path} HTTP/1.1\r\nHost: {p.hostname}:{p.port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n')
        self.sock.sendall(request.encode('ascii'))
        deadline=time.monotonic()+5
        while b'\r\n\r\n' not in self.buffer:
            self.check()
            if time.monotonic()>deadline:
                self.close();raise TimeoutError('El navegador no respondió al handshake CDP')
            try:self.buffer.extend(self.sock.recv(4096))
            except socket.timeout:continue
            if len(self.buffer)>65536:raise ValueError('Handshake CDP demasiado grande')
        head,tail=bytes(self.buffer).split(b'\r\n\r\n',1)
        self.buffer=bytearray(tail)
        headers={}
        for line in head.decode('latin-1').split('\r\n')[1:]:
            if ':' in line:
                k,v=line.split(':',1);headers[k.lower()]=v.strip()
        expected=base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode('ascii')).digest()).decode('ascii')
        if b' 101 ' not in head.split(b'\r\n')[0] or headers.get('sec-websocket-accept')!=expected:
            self.close();raise ValueError('Handshake CDP no válido')

    def close(self):
        self.sock.close()

    def send(self,payload,opcode=1):
        data=payload.encode('utf-8') if isinstance(payload,str) else payload
        length=len(data)
        header=bytes((128|opcode,128|(length if length<126 else 126 if length<65536 else 127)))
        if length>=126:header+=struct.pack('!H' if length<65536 else '!Q',length)
        mask=os.urandom(4)
        self.sock.sendall(header+mask+bytes(v^mask[i%4] for i,v in enumerate(data)))

    def _fill(self,length):
        while len(self.buffer)<length:
            self.check()
            b=self.sock.recv(max(4096,min(1024*1024,length-len(self.buffer))))
            if not b:raise ConnectionError('Se cerró la conexión con el navegador CNIG')
            self.buffer.extend(b)

    def receive(self):
        while True:
            self._fill(2)
            first,second=self.buffer[:2]
            length=second&127
            header=2
            if length in (126,127):
                width=2 if length==126 else 8
                self._fill(2+width)
                length=struct.unpack('!H' if width==2 else '!Q',self.buffer[2:2+width])[0]
                header+=width
            if length>20*1024*1024:raise ValueError('Mensaje CDP demasiado grande')
            masked=bool(second&128)
            if masked:header+=4
            self._fill(header+length)
            payload=bytes(self.buffer[header:header+length])
            if masked:
                mask=self.buffer[header-4:header]
                payload=bytes(v^mask[i%4] for i,v in enumerate(payload))
            del self.buffer[:header+length]
            opcode=first&15
            if opcode==8:raise ConnectionError('El navegador cerró la sesión CNIG')
            if opcode==9:
                self.send(payload,10);continue
            if opcode==10:continue
            if opcode not in (0,1):raise ValueError('Trama CDP no compatible')
            self.fragment.extend(payload)
            if len(self.fragment)>20*1024*1024:raise ValueError('Mensaje CDP fragmentado demasiado grande')
            if first&128:
                result=self.fragment.decode('utf-8');self.fragment.clear();return result


class CDP:
    def __init__(self,url,check=lambda:None):
        self.ws=WebSocket(url,check)
        self.check=check
        self.counter=0
        self.events=deque()

    def close(self):self.ws.close()

    def _message(self):return json.loads(self.ws.receive())

    def call(self,method,params=None,session=None,timeout=15):
        self.check();self.counter+=1
        message={'id':self.counter,'method':method,'params':params or {}}
        if session:message['sessionId']=session
        self.ws.send(json.dumps(message))
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            self.check()
            try:result=self._message()
            except socket.timeout:continue
            if result.get('id')==message['id']:
                if 'error' in result:
                    raise RuntimeError('El navegador rechazó '+method+': '+str(result['error'].get('message','error')))
                return result.get('result',{})
            if 'method' in result:
                self.events.append(result)
                if len(self.events)>10000:raise RuntimeError('Cola CDP excesiva')
        raise TimeoutError('Sin respuesta del navegador a '+method)

    def event(self):
        self.check()
        if self.events:return self.events.popleft()
        try:message=self._message()
        except socket.timeout:return None
        return message if 'method' in message else None

    def evaluate(self,expression,session):
        result=self.call('Runtime.evaluate',{'expression':expression,'returnByValue':True},session)
        if result.get('exceptionDetails'):raise RuntimeError('La página CNIG no pudo ejecutar su acción')
        return result.get('result',{}).get('value')
