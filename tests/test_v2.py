from pathlib import Path
import fitz
from PIL import Image
from demo.agent import SCHEMA, build_system_prompt, get_skill_text, prompt_fingerprint
from demo.classifier import PrototypeModel,classify_pdf
from demo.vision import SyntheticVisionModel
from demo.simulation import Scenario

ROOT=Path(__file__).parents[1]

def test_vision_is_real_image_model_and_has_two_classes():
    model=SyntheticVisionModel(n_per_class=24)
    positive=model.score(model.render_training_example(1,seed=22))
    negative=model.score(model.render_training_example(0,seed=22))
    assert positive.margin>negative.margin
    assert positive.candidate
    assert not negative.candidate

def test_vision_does_not_auto_certify_document_without_text():
    model=SyntheticVisionModel(n_per_class=24)
    text=PrototypeModel()
    file=ROOT/'samples'/'08_tarjeta_didactica_nitida.pdf'
    result=classify_pdf(file.read_bytes(),file.name,text,vision_model=model,enable_ocr=False)
    assert result.code=='REVISAR'  # imagen únicamente = candidato, nunca identidad verificada
    assert result.vision_margin is not None
    assert result.tokens_input==0

def test_skill_is_loaded_as_versioned_text_and_json_contract():
    assert 'Ignora' in get_skill_text()
    assert 'SKILL VERSIONADA' in build_system_prompt()
    assert len(prompt_fingerprint())==12
    assert set(SCHEMA['required'])==set(SCHEMA['properties'])

def test_fifty_thousand_are_hypothesis_not_benchmark():
    example=Scenario().summary()
    assert example['total']==50000
    assert sum(example[k] for k in ('deterministic','vision','agent','manual'))==50000
    assert example['percent_agent_calls_avoided']==94
    assert example['tokens_agent_estimate']==6060000
    assert 'NO MEDIDO' in example['scenario_type']
