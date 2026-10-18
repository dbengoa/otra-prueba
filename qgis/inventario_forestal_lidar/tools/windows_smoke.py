"""Run using QGIS Python on Windows with FUSION 4.61 installed.

Creates four artificial LAS tiles on a flat ground with 10 m canopy returns.
Does not query CNIG; this is an independent executable integration check.
"""
import csv
import json
import os
from pathlib import Path
import struct
import sys
from qgis.core import QgsApplication
from inventario_forestal_lidar.core import Plot
from inventario_forestal_lidar.engine import Engine


def write_las(path,x0,y0):
    records=[]
    xs=[];ys=[];zs=[]
    for i in range(50):
        for j in range(50):
            for z,classification in ((100,2),(110,5)):
                x,y=x0+i+.5,y0+j+.5
                xs.append(x);ys.append(y);zs.append(z)
                records.append(struct.pack('<iiiHBBbBH',round(x*100),round(y*100),round(z*100),50,9,classification,0,0,1))
    h=bytearray(227)
    h[:4]=b'LASF';h[24:26]=bytes((1,2))
    struct.pack_into('<H',h,94,227)
    struct.pack_into('<I',h,96,227)
    h[104]=0
    struct.pack_into('<H',h,105,20)
    struct.pack_into('<I',h,107,len(records))
    struct.pack_into('<I',h,111,len(records))
    struct.pack_into('<ddd',h,131,.01,.01,.01)
    struct.pack_into('<dddddd',h,179,max(xs),min(xs),max(ys),min(ys),max(zs),min(zs))
    path.write_bytes(h+b''.join(records))


def main():
    if os.name!='nt':raise SystemExit('Este smoke test necesita Windows y los ejecutables FUSION')
    root=Path(sys.argv[1] if len(sys.argv)>1 else 'C:/lidar_smoke').resolve()
    if root.exists() and any(root.iterdir()):raise SystemExit('Use una carpeta vacía para conservar pruebas anteriores')
    root.mkdir(parents=True,exist_ok=True)
    originals=root/'originales';originals.mkdir()
    index=root/'index.csv'
    with index.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['series','sec','name','epsg','xmin','ymin','xmax','ymax'])
        for i,(x,y) in enumerate(((399950,4599950),(400000,4599950),(399950,4600000),(400000,4600000)),1):
            name=f'synthetic_{i}.las'
            write_las(originals/name,x,y)
            w.writerow(['LIDA3',i,name,25830,x,y,x+50,y+50])
    app=QgsApplication.instance() or QgsApplication([],False)
    app.initQgis()
    config=dict(output=str(root),index=str(index),fusion='C:/FUSION',epsg=25830,radius=15,cell=1)
    run=Path(Engine(config,[Plot('001',400000,4600000)],progress=lambda n,s:print(round(n),s)).execute())
    state=json.loads((run/'estado.json').read_text())
    assert state['status']=='completed' and len(state['tiles'])==4
    normalized=next(run.glob('*/normalizada.las'))
    data=normalized.read_bytes()
    offset=struct.unpack_from('<I',data,96)[0]
    record_size=struct.unpack_from('<H',data,105)[0]
    count=struct.unpack_from('<I',data,107)[0]
    scale=struct.unpack_from('<d',data,147)[0]
    bias=struct.unpack_from('<d',data,171)[0]
    heights=[struct.unpack_from('<i',data,offset+i*record_size+8)[0]*scale+bias for i in range(count)]
    expected=2*sum((i+.5)**2+(j+.5)**2<=225 for i in range(-15,15) for j in range(-15,15))
    assert len(heights)==expected,(len(heights),expected)
    assert abs(min(heights))<.05 and abs(max(heights)-10)<.05
    assert (run/'metricas.gpkg').is_file()
    print('PASS: círculo de cuatro teselas, terreno 100 m, alturas 0 y 10 m, CSV/GPKG',run)

if __name__=='__main__':main()
