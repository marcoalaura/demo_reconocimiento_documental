"""python run_demo.py --source local --path samples --vision [--ocr]

Escenario inventado: python run_demo.py --simulate
"""
from __future__ import annotations
import os
import argparse
import csv
from pathlib import Path
from demo.agent import LimitedVisionAgent
from demo.classifier import PrototypeModel, classify_pdf
from demo.vision import SyntheticVisionModel
from demo.sources import local_pdfs,s3_pdfs
from demo.simulation import Scenario

def main():
    parser=argparse.ArgumentParser(description='V2: OCR + reglas -> HOG/SVM -> agente Skill opcional')
    parser.add_argument('--source',choices=['local','s3'],default='local')
    parser.add_argument('--path',default=str(Path(__file__).parent/'samples'))
    parser.add_argument('--bucket',default='');parser.add_argument('--prefix',default='')
    parser.add_argument('--region',default='');parser.add_argument('--profile',default='')
    parser.add_argument('--limit',type=int,default=20)
    parser.add_argument('--ocr',action='store_true')
    parser.add_argument('--ocr-lang',default='eng')
    parser.add_argument('--no-vision',action='store_true',help='Deshabilitar SVM de muestras sintéticas')
    parser.add_argument('--agent',action='store_true',help='OPT-IN: envía página al servicio IA')
    parser.add_argument('--agent-limit',type=int,default=2)
    parser.add_argument('--out',default='resultados_v2.csv')
    parser.add_argument('--simulate',action='store_true',help='IMPRIME HIPÓTESIS, no abre documentos')
    args=parser.parse_args()
    if args.simulate:
        example=Scenario().summary()
        print('\n=== ESCENARIO HIPOTÉTICO (NO MEDICIÓN REAL) ===')
        for key in ('total','deterministic','vision','agent','manual','pct_deterministic',
                    'pct_vision','pct_agent','pct_manual','seconds_automated_serial',
                    'hours_manual_person','tokens_agent_estimate','tokens_all_agent_counterfactual',
                    'percent_agent_calls_avoided','scenario_type'):
            print(f'{key}: {example[key]}')
        return
    if not 1<=args.limit<=50:parser.error('--limit de 1 a 50')
    if args.agent and not os.getenv('OPENAI_API_KEY'):parser.error('No hay OPENAI_API_KEY')
    agent=(LimitedVisionAgent(os.getenv('OPENAI_API_KEY',''),
                              model=os.getenv('OPENAI_MODEL','gpt-4o-mini'),
                              max_calls=max(0,min(args.agent_limit,5))) if args.agent else None)
    iterator=local_pdfs(args.path,args.limit) if args.source=='local' else s3_pdfs(args.bucket,args.prefix,args.limit,args.region,args.profile)
    text_model=PrototypeModel()
    vision_model=None if args.no_vision else SyntheticVisionModel()
    rows=[]
    for key,data,error in iterator:
        if error:
            from demo.classifier import DocumentResult
            row=DocumentResult(file=key,status='ERROR',code='ERROR',stage='FUENTE',reason=error).as_dict()
        else:
            row=classify_pdf(data,key,text_model,enable_ocr=args.ocr,ocr_lang=args.ocr_lang,
                             vision_model=vision_model,agent=agent).as_dict()
        rows.append(row)
        print(f"{row['file'][-48:]:48} | {row['code']:<7} | {row['stage']} | HOG={row.get('vision_margin')}")
    if rows:
        fieldnames=list(dict.fromkeys(k for r in rows for k in r))
        with open(args.out,'w',encoding='utf-8-sig',newline='') as out:
            writer=csv.DictWriter(out,fieldnames=fieldnames)
            writer.writeheader();writer.writerows(rows)
    print(f'\n{len(rows)} archivos • {args.out}' if rows else 'No se encontraron PDFs')
    if agent:print(f'Agente REAL: {agent.calls} consultas, {agent.used_tokens} tokens informados por API')

if __name__=='__main__':main()
