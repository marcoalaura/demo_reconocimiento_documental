"""APP: streamlit run app.py — muestra documental didáctica, con S3 solo lectura."""
from __future__ import annotations
import os
from pathlib import Path
import pandas as pd
import streamlit as st

from demo.agent import LimitedVisionAgent, get_skill_text, build_system_prompt, prompt_fingerprint
from demo.classifier import DocumentResult, PrototypeModel, classify_pdf
from demo.vision import SyntheticVisionModel
from demo.sources import MAX_PDF_BYTES, local_pdfs, s3_pdfs
from demo.simulation import Scenario

ROOT=Path(__file__).parent
st.set_page_config(page_title='Visión artificial + agentes · V4', page_icon='🔎',layout='wide')
st.markdown('''<style>
.block-container{padding-top:1.6rem;max-width:1310px}
[data-testid="stMetricValue"]{font-size:1.55rem}
</style>''', unsafe_allow_html=True)
st.title('🔎 Reconocimiento y clasificación automatizada de documentos')
st.caption('V4 · OCR + reglas → modelos Python (HOG + SVM / TF-IDF) → agente con Skill versionada · S3 solo lectura')
st.info('**Pregunta central:** ¿Cuándo nuestro conocimiento y los modelos locales bastan, y cuándo un agente realmente añade valor?')

@st.cache_resource
def get_text_model():return PrototypeModel()

@st.cache_resource
def get_vision_model():return SyntheticVisionModel()

tab_demo, tab_scenario, tab_skill=st.tabs(['🧪 Flujo real con ejemplos', '📊 Escenario hipotético: 50.000', '🧠 Prompt + Skill'])
with tab_demo:
  with st.sidebar:
    st.subheader('01 · Opciones de procesamiento')
    max_docs=st.slider('PDF máximos',1,50,15)
    max_pages=st.slider('Páginas por PDF',1,5,3)
    use_ocr=st.checkbox('OCR local (Tesseract)',value=False)
    ocr_lang=st.text_input('Idiomas Tesseract', 'eng',disabled=not use_ocr)
    use_vision=st.checkbox('Modelo visual HOG + SVM (sintético)',value=True)
    st.caption('El SVM identifica patrones geométricos y propone candidatos: **no autentica ID** ni ofrece precisión validada.')
    st.divider()
    st.subheader('02 · Agente (opt-in)')
    run_ai=st.checkbox('Autorizo el envío de muestras a OpenAI',value=False)
    max_ai=st.slider('Máximo de llamadas API',0,5,2,disabled=not run_ai)
    token_cap=st.slider('Reserva preventiva de tokens',3000,30000,9000,step=3000,disabled=not run_ai)
    st.caption('Una página comprimida por documento; sin reintentos. El máximo es una reserva estimada, NO un límite exacto de facturación.')

  a,b,c=st.columns(3)
  with a:st.metric('Método local 1','OCR + reglas','Tokens API: 0')
  with b:st.metric('Método local 2','HOG + SVM','Tokens API: 0')
  with c:st.metric('Escalamiento','Agente + Skill','Solo por permiso')
  st.caption('Todas las muestras son sintéticas o recreaciones totalmente ficticias de la estructura de los adjuntos. Los resultados ML y IA son candidatos, no identificaciones personales.')
  source=st.radio('Fuente', ['Muestras incluidas','Prefijo S3','Subir archivos'],horizontal=True)
  files=None
  if source=='Muestras incluidas':
    folder=str(ROOT/'samples')
  elif source=='Prefijo S3':
    x1,x2=st.columns(2)
    bucket=x1.text_input('Bucket S3',placeholder='bucket-demo')
    prefix=x2.text_input('Prefijo S3 (obligatorio)',placeholder='demo/documentos/')
    x3,x4=st.columns(2)
    region=x3.text_input('Región AWS',value=os.getenv('AWS_REGION',''))
    profile=x4.text_input('AWS_PROFILE local',value=os.getenv('AWS_PROFILE',''))
    st.warning('Conecta solo un prefijo autorizado, preferentemente de documentos ficticios. La aplicación nunca escribe o elimina objetos.')
  else:
    files=st.file_uploader('Subir PDFs de prueba',type=['pdf'],accept_multiple_files=True)
  with st.expander('Ver 3 niveles visuales de calidad de escaneo'):
    cols=st.columns(3)
    for c,path,caption in zip(cols,[
        '08_tarjeta_didactica_nitida.png','09_tarjeta_didactica_mala_calidad.png','10_certificado_inclinado_baja_res.png'],
        ['Tarjeta didáctica nítida','Desenfoque y compresión JPEG','Certificado girado y baja resolución']):
      c.image(str(ROOT/'assets'/'visuales'/path), caption=caption, use_container_width=True)
  if st.button('▶ Ejecutar pipeline V4',type='primary',use_container_width=True):
    if run_ai and not os.getenv('OPENAI_API_KEY'):
      st.error('No hay OPENAI_API_KEY. Desactiva IA o configura la clave de manera segura.'); st.stop()
    if source=='Prefijo S3' and (not bucket.strip() or not prefix.strip().strip('/')):
      st.error('S3 requiere bucket y prefijo específico.');st.stop()
    agent=LimitedVisionAgent(os.getenv('OPENAI_API_KEY',''),os.getenv('OPENAI_MODEL','gpt-4o-mini'),
                            max_ai,token_cap) if run_ai else None
    vision=get_vision_model() if use_vision else None
    if source=='Muestras incluidas':iterable=local_pdfs(folder,max_docs)
    elif source=='Prefijo S3':iterable=s3_pdfs(bucket,prefix,max_docs,region,profile)
    else:
      iterable=((f.name,f.getvalue() if f.size<=MAX_PDF_BYTES else None,
                 None if f.size<=MAX_PDF_BYTES else 'Archivo >12 MB') for f in (files or [])[:max_docs])
    rows=[]
    try:
      with st.spinner('Evaluando evidencia textual, visual y excepciones...'):
        for filename,content,error in iterable:
          if error:rows.append(DocumentResult(file=filename,status='ERROR',code='ERROR',stage='FUENTE',reason=error).as_dict())
          else:rows.append(classify_pdf(content,filename,get_text_model(),enable_ocr=use_ocr,
                                         ocr_lang=ocr_lang,max_pages=max_pages,
                                         agent=agent,vision_model=vision).as_dict())
    except Exception as exc:
      st.error(f'No se pudo procesar la fuente ({type(exc).__name__}): {str(exc)[:120]}');st.stop()
    st.session_state.v3_rows=rows
    st.session_state.v3_agent=(agent.calls,agent.used_tokens) if agent else (0,0)
  if 'v3_rows' in st.session_state:
    rows=st.session_state.v3_rows
    if not rows:st.warning('No hay documentos PDF.')
    else:
      df=pd.DataFrame(rows); api_calls,api_tokens=st.session_state.get('v3_agent',(0,0))
      m=st.columns(4)
      m[0].metric('Documentos',len(rows))
      m[1].metric('CE / CA / IDPR (demo)',sum(r['code'] in ('CE','CA','IDPR') for r in rows))
      m[2].metric('Revisión / error',sum(r['code'] in ('REVISAR','ERROR') for r in rows))
      m[3].metric('Llamadas API reales',api_calls)
      st.caption(f'Tokens API informados: **{api_tokens}**. El margen HOG/SVM NO es una probabilidad. OCR y cómputo local también implican recursos.')
      rename={'file':'Archivo','code':'Clase','status':'Estado','stage':'Etapa','extraction':'Extracción',
              'vision_margin':'Margen SVM (no prob.)','vision_candidate':'Candidato visual',
              'ml_idpr_similarity':'Similitud TF-IDF','elapsed_ms':'ms locales','reason':'Motivo'}
      display=df.rename(columns=rename)
      st.dataframe(display[['Archivo','Clase','Estado','Etapa','Extracción','Similitud TF-IDF',
                            'Margen SVM (no prob.)','Candidato visual','ms locales','Motivo']],
                   use_container_width=True,hide_index=True)
      st.bar_chart(df['stage'].value_counts())
      st.download_button('⬇ CSV de resultados del demo',display.to_csv(index=False).encode('utf-8-sig'),
                         file_name='resultados_v4.csv',mime='text/csv')
      with st.expander('Rastro de evidencias (sin datos personales)'):
        for item in rows:st.write(f"**{item['file']}** — {', '.join(item['evidence']) if item['evidence'] else 'sin señales'}")

with tab_scenario:
  st.warning('**SIMULACIÓN ILUSTRATIVA — NO MEDICIÓN REAL**. Todos los números, tiempos y tokens son SUPUESTOS editables. No representan precisión ni un benchmark.')
  s=Scenario()
  st.subheader('¿Qué podría ocurrir con 50.000 documentos?')
  d=st.slider('Resueltos por reglas/OCR',0,50000,s.deterministic,step=500)
  v=st.slider('Resueltos por visión + evidencia',0,50000-d,min(s.vision,50000-d),step=500)
  a=st.slider('Enviados a agente',0,50000-d-v,min(s.agent,50000-d-v),step=500)
  manual=50000-d-v-a
  t=st.number_input('Tokens supuestos por llamada agente (entrada + salida)',min_value=100,max_value=12000,value=2020,step=100)
  c=st.columns(4)
  for col,name,num in zip(c,['Reglas/OCR','Visión + ML','Agente','Revisión humana'],[d,v,a,manual]):
    col.metric(name,f'{num:,}'.replace(',','.'),f'{100*num/50000:.1f}%')
  st.bar_chart(pd.DataFrame({'Método':['Reglas / OCR','Visión + ML','Agente','Humano'],
                             'Documentos':[d,v,a,manual]}).set_index('Método'))
  k1,k2=st.columns(2)
  k1.metric('Llamadas a IA evitadas vs. enviar todos',f'{(1-a/50000)*100:.1f}%')
  k2.metric('Tokens supuestos con IA solo en excepciones',f'{a*t:,}'.replace(',','.'))
  st.caption(f'Comparador: enviar los 50.000 a un agente serían {(50000*t):,} tokens supuestos. No incluye reintentos ni tokens de imagen reales. El tiempo no equivale a duración de ejecución: concurrencia, red y hardware modifican el resultado.'.replace(',', '.'))
  with st.expander('Suposiciones fijas de tiempo del ejemplo base'):
    st.write('Base hipotética: reglas/OCR 0,12 s por documento resuelto; visión 0,9 s; agente 4,5 s; revisión humana 90 s por documento. No son mediciones ni porcentajes de acierto.')

with tab_skill:
  st.subheader('La Skill no es magia: es una instrucción repetible, controlada y versionada')
  st.caption(f'Archivo: skills/reconocimiento_idpr/SKILL.md · Prompt v3.0-demo · SHA-256 abreviado: {prompt_fingerprint()}')
  st.code(get_skill_text(),language='markdown')
  with st.expander('Mostrar prompt de sistema efectivo'):
    st.code(build_system_prompt(),language='text')
  st.code('''{"code":"OTHER","confidence":0.32,"signals":["texto ilegible"],
"reason":"No se distingue pieza principal","requires_review":true}''',language='json')
  st.info('Salida estructurada + validación + supervisión humana. Confidence declarado por IA no representa una precisión calibrada. Nunca se solicitan nombres, números o datos de identidad.')

st.divider()
st.caption('V4 · Proyecto aislado · S3 solo lectura · dataset sintético y recreaciones sin datos personales · no equivale a motor de identificación/validación oficial.')
