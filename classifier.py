"""Clasificación escalonada: OCR+reglas, señales IDPR, TF-IDF, visión HOG+SVM, IA opcional.

No se reclaman métricas de precisión: las plantillas ML son sintéticas, no datos reales.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from io import BytesIO
import re
import time
import unicodedata

import fitz


DOCUMENT_NAMES = {
    'CA': 'Contrato de venta a plazos (CA)' ,
    'CE': 'Certificación de instalación eléctrica',
    'IDPR': 'Identificación de Puerto Rico',
}

# Inspiradas en 06_identify_documents_process.py del repositorio original.
REGULAR_PATTERNS = {
    'CA': ('CONTRATO', 'ARRENDAMIENTO'),
    'CE': ('NUMERO DE CERTIFICACION',),
}

# Grupos simplificados/adaptados de 07_identity_id_document_process.py.
POSITIVE_GROUPS = [
    ('Título de identificación', True, ('LICENCIA DE CONDUCIR', 'LICENCIA PARA CONDUCIR',
                                       'DRIVER LICENSE', 'DRIVERS LICENSE', 'IDENTIFICATION CARD',
                                       'TARJETA DE IDENTIFICACION')),
    ('DTOP', True, ('DTOP', 'DEPARTAMENTO DE TRANSPORTACION')),
    ('Ojos', True, ('EYES', 'OJOS', 'EYE COLOR', 'COLOR DE OJOS')),
    ('Estatura', True, ('HEIGHT', 'ALTURA', 'HT')),
    ('Clase', True, ('CLASS', 'CLASE')),
    ('Restricciones', True, ('REST', 'RESTRICTION', 'ENDORSEMENTS')),
    ('Nacimiento', True, ('DOB', 'DOB/NAC', 'FECHA DE NACIMIENTO', 'DATE OF BIRTH')),
    ('Emisión', True, ('ISS/EMI',)),
    ('Operador', True, ('OPERATOR',)),
    ('Puerto Rico', False, ('PUERTO RICO',)),
    ('Vencimiento', False, ('EXP', 'EXPIRATION', 'FECHA DE VENCIMIENTO')),
]
NEGATIVE_SIGNALS = (
    'ESCRITURA PUBLICA', 'NOTARIO PUBLICO', 'REGISTRO DE LA PROPIEDAD',
    'ESTADO BANCARIO', 'ESTADO DE CUENTA', 'DEPARTAMENTO DE HACIENDA',
    'COLEGIO DE INGENIEROS', 'ESTAMPILLA DIGITAL', 'INSTALACION ELECTRICA',
    'SERVICIO ELECTRICO', 'FACTURA DE ELECTRICIDAD', 'NUMERO DE CERTIFICACION',
    'CONTRATO DE ARRENDAMIENTO', 'CONTRATO DE COMPRAVENTA',
    'CONSULTA DE CREDITO', 'TARJETA BANCARIA', 'SENTENCIA DEL TRIBUNAL',
)

# El modelo clásico del demo no procede del proyecto; textos ficticios SIN PII.
ML_TEMPLATES = {
    'IDPR': [
        'PUERTO RICO DTOP LICENCIA DE CONDUCIR DOB/NAC EYES HT CLASS REST EXP',
        'TARJETA DE IDENTIFICACION PUERTO RICO FECHA DE NACIMIENTO OJOS ALTURA',
        'DRIVERS LICENSE PUERTO RICO DTOP HEIGHT EYES OPERATOR DOB EXPIRATION',
        'IDENTIFICATION CARD PUERTO RICO DTOP DOB EXP ISS/EMI',
    ],
    'OTHER': [
        'CONTRATO DE ARRENDAMIENTO PARTES FIRMAN CONDICIONES Y OBLIGACIONES',
        'NUMERO DE CERTIFICACION INSTALACION ELECTRICA SERVICIO ELECTRICO',
        'FACTURA DE ELECTRICIDAD CONSUMO KWH PRECIO Y FECHA',
        'ESCRITURA PUBLICA NOTARIO PUBLICO PROPIEDAD REGISTRO',
        'ESTADO BANCARIO CUENTA MOVIMIENTOS FINANCIEROS',
        'CARTA AUTORIZACION SOLICITUD DE SERVICIO',
    ],
}


def normalize(text: str) -> str:
    base = unicodedata.normalize('NFKD', text.upper())
    return ' '.join(''.join(c for c in base if not unicodedata.combining(c)).split())


def contains_term(haystack: str, needle: str) -> bool:
    term = normalize(needle)
    # Controla abreviaturas cortas para evitar que HT coincida con HEIGHT.
    if len(term) <= 5 and ' ' not in term and '/' not in term:
        return re.search(r'\b' + re.escape(term) + r'\b', haystack) is not None
    return term in haystack


def tokens_near(text: str, first: str, second: str, max_gap: int = 10) -> bool:
    a, b = normalize(first), normalize(second)
    return any(re.search(re.escape(x) + r'.{0,' + str(max_gap) + r'}' + re.escape(y), text)
               for x, y in ((a, b), (b, a)))


def match_regular(text: str):
    norm = normalize(text)
    if not norm:
        return None
    # CA real adjunto: 'Contrato de venta al por menor a plazos' (no arrendamiento).
    if 'CONTRATO DE VENTA AL POR MENOR A PLAZOS' in norm or 'CONTRATO DE VENTA A PLAZOS' in norm:
        return 'CA', ['CONTRATO DE VENTA AL POR MENOR A PLAZOS']
    if 'CERTIFICACION DE INSTALACION ELECTRICA' in norm:
        return 'CE', ['CERTIFICACION DE INSTALACION ELECTRICA']
    for code, terms in REGULAR_PATTERNS.items():
        if (tokens_near(norm, *terms) if len(terms) == 2 else contains_term(norm, terms[0])):
            return code, list(terms)
    return None


def idpr_signals(text: str) -> dict:
    norm = normalize(text)
    negatives = [term for term in NEGATIVE_SIGNALS if contains_term(norm, term)]
    groups = [label for label, _, terms in POSITIVE_GROUPS if any(contains_term(norm, t) for t in terms)]
    strong = [label for label, strong, terms in POSITIVE_GROUPS if strong and any(contains_term(norm, t) for t in terms)]
    return {'groups': groups, 'strong': strong, 'negatives': negatives,
            'rule_pass': len(groups) >= 2 and len(strong) >= 1 and not negatives}


class PrototypeModel:
    """TF-IDF char n-gram + similitud coseno: prototipos sintéticos, no modelo validado."""
    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.samples = [normalize(t) for sample in ML_TEMPLATES.values() for t in sample]
        self.labels = [label for label, sample in ML_TEMPLATES.items() for _ in sample]
        self.vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform(self.samples)

    def score(self, text: str) -> dict:
        from sklearn.metrics.pairwise import cosine_similarity
        matrix = self.vectorizer.transform([normalize(text)[:5000]])
        sims = cosine_similarity(matrix, self.matrix)[0]
        best = {label: max(float(sims[i]) for i, key in enumerate(self.labels) if key == label)
                for label in ML_TEMPLATES}
        return {'idpr': round(best['IDPR'], 3), 'other': round(best['OTHER'], 3),
                'margin': round(best['IDPR'] - best['OTHER'], 3)}


@dataclass
class DocumentResult:
    file: str
    code: str = 'REVISAR'
    status: str = 'REVISIÓN PENDIENTE'
    stage: str = 'SIN CLASIFICAR'
    extraction: str = 'NONE'
    page: int = 0
    evidence: list[str] = field(default_factory=list)
    ml_idpr_similarity: float | None = None
    vision_margin: float | None = None
    vision_candidate: bool = False
    reason: str = ''
    elapsed_ms: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    agent_called: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


def _page_text(page, ocr: bool, ocr_lang: str) -> tuple[str, str]:
    txt = page.get_text('text').strip()
    if len(txt) >= 30 or not ocr:
        return txt, 'PDF_TEXT' if txt else 'NONE'
    try:
        import pytesseract
        from PIL import Image
        pix = page.get_pixmap(matrix=fitz.Matrix(1.7, 1.7), alpha=False)
        img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        recognized = pytesseract.image_to_string(img, lang=ocr_lang).strip()
        if len(recognized) > len(txt):
            return recognized, 'OCR_TESSERACT'
    except Exception as exc:
        raise RuntimeError('OCR no disponible; instala Tesseract y verifica OCR_LANG. ' + str(exc)) from exc
    return txt, 'PDF_TEXT' if txt else 'NONE'


def classify_pdf(contents: bytes, filename: str, model: PrototypeModel,
                 enable_ocr: bool = False, ocr_lang: str = 'spa+eng',
                 max_pages: int = 3, ml_threshold: float = 0.24,
                 agent=None, vision_model=None) -> DocumentResult:
    """Pipeline secuencial. No modifica archivos ni S3; agente opcional y acotado."""
    start = time.perf_counter()
    result = DocumentResult(file=filename)
    texts = []
    try:
        with fitz.open(stream=contents, filetype='pdf') as pdf:
            if pdf.page_count == 0:
                raise ValueError('PDF sin páginas')
            for index in range(min(pdf.page_count, max_pages)):
                txt, extraction = _page_text(pdf.load_page(index), enable_ocr, ocr_lang)
                texts.append((txt, extraction, index + 1))
                if index == 0:
                    # CA y CE solo en portada, como en el paso 06 del original.
                    regular = match_regular(txt)
                    if regular:
                        result.code, result.evidence = regular
                        result.status, result.stage = 'IDENTIFICADO', '1 · TEXTO / OCR + REGLAS'
                        result.extraction, result.page = extraction, 1
                        result.reason = 'Coincidencia de patrón específico (sin tokens)'
                        return result

            # Etapa 2: grupos de señales + similitud TF-IDF, por página.
            negative_pages = []
            for txt, extraction, page in texts:
                if not txt.strip():
                    continue
                signals = idpr_signals(txt)
                if signals['negatives']:
                    negative_pages.append((page, signals['negatives'][0]))
                score = model.score(txt)
                if signals['rule_pass'] and score['idpr'] >= ml_threshold and score['margin'] > 0:
                    result.code, result.status = 'IDPR', 'IDENTIFICADO (DEMO)'
                    result.stage, result.extraction, result.page = '2 · REGLAS IDPR + TF-IDF', extraction, page
                    result.evidence = signals['groups']
                    result.ml_idpr_similarity = score['idpr']
                    result.reason = f"{len(signals['groups'])} grupos; {len(signals['strong'])} fuertes; margen TF-IDF {score['margin']:.3f}. Requiere validación real"
                    return result
                if score['idpr'] > (result.ml_idpr_similarity or -1):
                    result.ml_idpr_similarity = score['idpr']
                    result.evidence = signals['groups'][:5]
                    result.extraction, result.page = extraction, page
                    if signals['negatives']:
                        result.reason = 'Descartado por señal negativa: ' + signals['negatives'][0]
                    elif signals['rule_pass']:
                        result.reason = 'Candidato IDPR no concluyente para el modelo clásico'

            # Casos descaradamente ajenos (facturas/escrituras) NO gastan tokens.
            if negative_pages and not any(idpr_signals(t)['rule_pass'] for t, _, _ in texts):
                result.code = 'OTRO'
                result.status = 'DESCARTADO POR REGLA'
                result.stage = '2 · FILTRO NEGATIVO'
                result.reason = 'Documento incompatible con IDPR: ' + negative_pages[0][1]
                return result

            # Etapa 2b: visión de imagen real. HOG+SVM es un DEMO ENTRENADO
            # con formas sintéticas; su margen es distancia firmada, NO confianza.
            # Una coincidencia VISUAL por sí sola NUNCA valida una IDPR real.
            if vision_model is not None:
                from PIL import Image
                first = pdf.load_page(0)
                pix = first.get_pixmap(matrix=fitz.Matrix(1.1, 1.1), alpha=False)
                image = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
                visual = vision_model.score(image)
                result.vision_margin = visual.margin
                result.vision_candidate = visual.candidate
                if visual.candidate:
                    result.stage = '2 · VISIÓN HOG + SVM · CANDIDATO'
                    result.page = 1
                    result.reason = ('Patrón de tarjeta detectado por un SVM sintético; '
                                     'sin señales de texto verificables, requiere revisión.')
                elif not result.reason:
                    result.stage = '2 · VISIÓN HOG + SVM · NO CONCLUYENTE'
                    result.reason = ('Sin señales textuales suficientes y sin evidencia visual '
                                     'concluyente; revisión o agente opcional.')

            # Etapa 3: solo los casos difíciles, con aprobación explícita en la interfaz.
            if agent is not None:
                text = '\n'.join(t for t, _, _ in texts)[:2500]
                agent_data = agent.analyze(contents, text)
                result.agent_called = bool(agent_data.get('called'))
                result.tokens_input = int(agent_data.get('tokens_input', 0))
                result.tokens_output = int(agent_data.get('tokens_output', 0))
                if agent_data.get('called'):
                    result.stage = '3 · AGENTE MULTIMODAL'
                    if (agent_data.get('code') in DOCUMENT_NAMES and
                        agent_data.get('confidence', 0) >= 0.85 and
                        not agent_data.get('requires_review', True)):
                        result.code = agent_data['code']
                        result.status = 'PROPUESTA IA · REVISAR'
                        result.evidence = agent_data.get('signals', [])[:5]
                        result.reason = agent_data.get('reason', '')[:180]
                    else:
                        result.status = 'REVISIÓN PENDIENTE'
                        result.reason = 'Agente sin evidencia suficiente (o confianza inferior a 0.85)'
                else:
                    result.reason = agent_data.get('reason', 'Presupuesto de agente agotado')
            elif not result.reason:
                result.reason = 'Sin coincidencia sólida. Puede enviarse a revisión o a IA bajo presupuesto.'
    except Exception as exc:
        result.status = 'ERROR'
        result.reason = f'{type(exc).__name__}: {str(exc)[:180]}'
    finally:
        result.elapsed_ms = round((time.perf_counter() - start) * 1000)
    return result
