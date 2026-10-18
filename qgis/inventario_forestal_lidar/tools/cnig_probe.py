"""Read-only live CNIG discovery/coverage probe. Does not authorize/download files."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from inventario_forestal_lidar.core import Plot
from inventario_forestal_lidar.cnig import AutomaticSource

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--x',type=float,required=True)
parser.add_argument('--y',type=float,required=True)
parser.add_argument('--epsg',type=int,required=True)
parser.add_argument('--radius',type=float,default=15)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
args.output.mkdir(parents=True,exist_ok=True)
source=AutomaticSource(args.output,args.output,progress=lambda n,s:print(round(n,1),s,flush=True))
rows=source.plan([Plot('probe',args.x,args.y)],args.epsg,args.radius,1)
print('CNIG real: consulta y cobertura oficial verificadas;',len(rows),'teselas. No se ha descargado LAZ ni ejecutado FUSION.')
