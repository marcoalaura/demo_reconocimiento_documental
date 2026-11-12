from pathlib import Path
from demo.classifier import PrototypeModel, classify_pdf, match_regular
ROOT = Path(__file__).parents[1]

def test_uploaded_format_contract_and_certification_are_distinct():
    assert match_regular('CONTRATO DE VENTA AL POR MENOR A PLAZOS')[0] == 'CA'
    assert match_regular('CERTIFICACIÓN DE INSTALACIÓN ELÉCTRICA')[0] == 'CE'

def test_recreated_documents_only_with_local_ocr():
    model=PrototypeModel()
    expect={'12_CE_recreado_anonimizado.pdf':'CE',
            '13_CA_venta_plazos_recreado_anonimizado.pdf':'CA',
            '14_IDPR_recreado_anonimizado.pdf':'IDPR',
            '15_IDPR_mala_calidad_recreado.pdf':'REVISAR'}
    for f,c in expect.items():
        result=classify_pdf((ROOT/'samples'/f).read_bytes(),f,model,enable_ocr=True,ocr_lang='eng')
        assert result.code==c, (f, result)
        assert not result.agent_called
