"""Muestras gráficas SINTÉTICAS, sin documentos personales ni datos reales."""
from __future__ import annotations
from pathlib import Path
from io import BytesIO
import random
import fitz
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from demo.vision import _example_layout

ROOT = Path(__file__).parent
ASSETS = ROOT / 'assets' / 'visuales'
SAMPLES = ROOT / 'samples'

def to_pdf(image: Image.Image, name: str):
    output = BytesIO(); image.convert('RGB').save(output, 'JPEG', quality=82)
    doc = fitz.open(); page = doc.new_page(width=595, height=842)
    rect=fitz.Rect(48,80,547,760)
    page.insert_image(rect, stream=output.getvalue(), keep_proportion=True)
    doc.save(SAMPLES/name, garbage=4, deflate=True); doc.close()

def save(name, image):
    image.save(ASSETS/name)

def create_visual_examples():
    ASSETS.mkdir(parents=True, exist_ok=True); SAMPLES.mkdir(exist_ok=True)
    # Referencia: tarjeta DIDÁCTICA; no copia documentos gubernamentales.
    good = _example_layout(1, 137).resize((840,1080),Image.Resampling.LANCZOS)
    dd=ImageDraw.Draw(good)
    dd.text((30,25),'EJEMPLO FICTICIO - SIN VALOR OFICIAL', fill=(73,91,106))
    save('08_tarjeta_didactica_nitida.png',good)
    to_pdf(good, '08_tarjeta_didactica_nitida.pdf')

    # Mala calidad: 70px de ancho de fuente, redimensionado, ruido y compresión.
    bad=good.resize((175,225),Image.Resampling.BILINEAR)
    buff=BytesIO(); bad.save(buff, format='JPEG',quality=16,subsampling=2)
    bad=Image.open(BytesIO(buff.getvalue())).convert('RGB').resize((840,1080),Image.Resampling.BILINEAR)
    bad=bad.rotate(6.5,expand=False,fillcolor=(239,239,239)).filter(ImageFilter.GaussianBlur(1.7))
    d=ImageDraw.Draw(bad)
    d.rectangle((18,150,55,1020),fill=(140,137,131))
    d.line((86,165,814,215),fill=(220,218,209),width=14)
    save('09_tarjeta_didactica_mala_calidad.png',bad)
    to_pdf(bad,'09_tarjeta_didactica_mala_calidad.pdf')

    # Escaneo inclinado de certificado (etiqueta ilustrativa, no OCR garantizado).
    cert=Image.new('RGB',(780,1050),'white'); d=ImageDraw.Draw(cert)
    font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    try: ft=ImageFont.truetype(font,23); ft2=ImageFont.truetype(font,16)
    except OSError: ft=ImageFont.load_default(); ft2=ft
    d.rectangle((45,42,742,996),outline=(84,93,103),width=2)
    d.text((74,100),'CERTIFICADO ELECTRICO - DEMO',font=ft,fill=(28,45,62))
    d.text((74,162),'NUMERO DE CERTIFICACION: FICTICIO',font=ft2,fill=(37,49,68))
    for y in range(240,780,38):
        d.line((80,y,random.Random(y).randint(510,690),y),fill=(167,180,189),width=2)
    cert=cert.resize((265,356),Image.Resampling.BILINEAR).resize((780,1050),Image.Resampling.BILINEAR)
    cert=cert.rotate(-10.5,expand=False,fillcolor=(228,228,227)).filter(ImageFilter.GaussianBlur(1.0))
    save('10_certificado_inclinado_baja_res.png', cert)
    to_pdf(cert,'10_certificado_inclinado_baja_res.pdf')
    # Documento tradicional completo como clase negativa.
    other=_example_layout(0, 48).resize((840,1080),Image.Resampling.LANCZOS)
    save('11_hoja_documental.png',other)
    to_pdf(other,'11_hoja_documental.pdf')
    print('Muestras visuales ficticias listas:', ASSETS)

if __name__=='__main__':
    create_visual_examples()
