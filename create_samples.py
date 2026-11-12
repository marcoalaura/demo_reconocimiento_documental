"""Genera PDFs ficticios sin datos personales. Ejecutar desde la raíz del demo."""
from pathlib import Path
import fitz
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO

BASE = Path(__file__).parent / 'samples'
BASE.mkdir(exist_ok=True)


def pdf_text(name, title, lines):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((55, 80), title, fontsize=17, fontname='helv')
    y = 133
    for line in lines:
        page.insert_text((55, y), line, fontsize=12)
        y += 32
    doc.save(BASE / name)
    doc.close()


def pdf_scan(name, title, lines, blurry=False):
    im = Image.new('RGB', (1000, 620), color=(251, 252, 255))
    d = ImageDraw.Draw(im)
    font_file = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    try:
        font = ImageFont.truetype(font_file, 34)
    except OSError:
        font = ImageFont.truetype('DejaVuSans.ttf', 34) if Path('DejaVuSans.ttf').exists() else ImageFont.load_default()
    d.rectangle((35, 40, 960, 580), outline=(65, 80, 108), width=4)
    d.text((70, 65), title, font=font, fill=(20, 32, 53))
    y = 140
    for line in lines:
        d.text((70, y), line, font=font, fill=(35, 43, 56))
        y += 67
    if blurry:
        im = im.filter(ImageFilter.GaussianBlur(radius=10))
    bio = BytesIO()
    im.save(bio, 'JPEG', quality=85)
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(fitz.Rect(30, 145, 565, 485), stream=bio.getvalue())
    doc.save(BASE / name)
    doc.close()


pdf_text('01_certificado_electrico.pdf', 'CERTIFICADO DE INSTALACION ELECTRICA', [
    'NUMERO DE CERTIFICACION: DEMO-000', 'FECHA: 2026-01-01', 'Archivo sintetico para ponencia'])
pdf_text('02_contrato_arrendamiento.pdf', 'CONTRATO DE ARRENDAMIENTO', [
    'Parte A / Parte B (ficticias)', 'Objeto: material de demostracion', 'No tiene valor legal'])
pdf_text('03_pr_id_textual.pdf', 'PUERTO RICO - DTOP', [
    'LICENCIA DE CONDUCIR   (EJEMPLO FICTICIO)', 'DOB/NAC: -- / EYES: -- / HT: --',
    'CLASS: --  REST: --  EXP: --', 'SIN PERSONAS, NUMEROS NI FOTOS REALES'])
pdf_text('04_factura_electrica.pdf', 'FACTURA DE ELECTRICIDAD', [
    'PUERTO RICO', 'CONSUMO DE KWH - EJEMPLO', 'No es un documento de identidad'])
pdf_scan('05_escaneo_dificil.pdf', 'TEXTO DIFICIL', ['IMAGEN BORROSA', 'NO SE PUEDE VERIFICAR'], blurry=True)
pdf_scan('06_idpr_escaneado.pdf', 'PUERTO RICO DTOP',
         ['LICENCIA DE CONDUCIR', 'DOB  EYES  HT  CLASS', 'REST  EXP  OPERATOR'], blurry=False)
pdf_text('07_escritura_no_id.pdf', 'ESCRITURA PUBLICA', [
    'NOTARIO PUBLICO - PUERTO RICO', 'Identificacion de las partes - DTOP',
    'No se reproduce ninguna tarjeta de identidad'])
print('Creados 7 PDFs ficticios en', BASE)

# V2: imágenes adicionales con mala resolución, rotación y texto visual.
from create_visuals import create_visual_examples
create_visual_examples()
