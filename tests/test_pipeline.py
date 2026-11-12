from pathlib import Path

from demo.classifier import (PrototypeModel, classify_pdf, idpr_signals,
                             match_regular, normalize, tokens_near)

SAMPLES = Path(__file__).parents[1] / 'samples'


def test_normalization_and_contract_distance():
    assert normalize('Número de Certificación') == 'NUMERO DE CERTIFICACION'
    assert tokens_near('CONTRATO DE ARRENDAMIENTO', 'CONTRATO', 'ARRENDAMIENTO')
    assert not tokens_near('CONTRATO ' + 'A' * 20 + ' ARRENDAMIENTO', 'CONTRATO', 'ARRENDAMIENTO')
    assert match_regular('NUMERO DE CERTIFICACION 27') == ('CE', ['NUMERO DE CERTIFICACION'])


def test_idpr_negative_guard_and_signal_threshold():
    assert idpr_signals('PUERTO RICO EXP')['rule_pass'] is False
    assert idpr_signals('PUERTO RICO DTOP DOB EYES HT')['rule_pass'] is True
    assert idpr_signals('NUMERO DE CERTIFICACION INSTALACION ELECTRICA PUERTO RICO DTOP DOB')['rule_pass'] is False


def test_sample_flow_without_external_ai():
    model = PrototypeModel()
    expected = {'01_certificado_electrico.pdf': 'CE',
                '02_contrato_arrendamiento.pdf': 'CA',
                '03_pr_id_textual.pdf': 'IDPR',
                '04_factura_electrica.pdf': 'OTRO',
                '05_escaneo_dificil.pdf': 'REVISAR',
                '06_idpr_escaneado.pdf': 'REVISAR',
                '07_escritura_no_id.pdf': 'OTRO'}
    for name, code in expected.items():
        result = classify_pdf((SAMPLES / name).read_bytes(), name, model, enable_ocr=False)
        assert result.code == code, (name, result)
        assert result.agent_called is False
        assert result.tokens_input == 0 and result.tokens_output == 0


def test_scanned_sample_with_local_ocr():
    model = PrototypeModel()
    result = classify_pdf((SAMPLES / '06_idpr_escaneado.pdf').read_bytes(),
                          'scan.pdf', model, enable_ocr=True, ocr_lang='eng')
    assert result.code == 'IDPR', result
    assert result.extraction == 'OCR_TESSERACT', result

class GuardedAgent:
    def analyze(self, pdf_bytes, text):
        raise AssertionError('No debía invocarse al agente')


def test_no_paid_ai_when_rules_or_negative_filter_succeed():
    model = PrototypeModel()
    for name in ('01_certificado_electrico.pdf', '02_contrato_arrendamiento.pdf',
                 '03_pr_id_textual.pdf', '04_factura_electrica.pdf', '07_escritura_no_id.pdf'):
        result = classify_pdf((SAMPLES / name).read_bytes(), name, model,
                              enable_ocr=False, agent=GuardedAgent())
        assert result.status != 'ERROR', result
        assert result.agent_called is False
