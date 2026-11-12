"""Escenario HIPOTÉTICO de 50.000 documentos: no es un benchmark observado."""
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Scenario:
    total: int = 50000
    deterministic: int = 32500
    vision: int = 13000
    agent: int = 3000
    manual: int = 1500
    seconds_deterministic: float = 0.12
    seconds_vision: float = 0.9
    seconds_agent: float = 4.5
    seconds_manual: float = 90.0
    estimated_input_tokens: int = 1800
    estimated_output_tokens: int = 220

    def __post_init__(self):
        if min(self.total, self.deterministic, self.vision, self.agent, self.manual) < 0:
            raise ValueError('Cantidades no negativas')
        if self.deterministic + self.vision + self.agent + self.manual != self.total:
            raise ValueError('Las categorías deben sumar el total')

    def summary(self) -> dict:
        return {
            **asdict(self),
            'pct_deterministic': self.deterministic / self.total * 100,
            'pct_vision': self.vision / self.total * 100,
            'pct_agent': self.agent / self.total * 100,
            'pct_manual': self.manual / self.total * 100,
            'seconds_automated_serial': (self.deterministic * self.seconds_deterministic +
                                         self.vision * self.seconds_vision + self.agent * self.seconds_agent),
            'hours_manual_person': self.manual * self.seconds_manual / 3600,
            'tokens_agent_estimate': self.agent * (self.estimated_input_tokens + self.estimated_output_tokens),
            'tokens_all_agent_counterfactual': self.total * (self.estimated_input_tokens + self.estimated_output_tokens),
            'percent_agent_calls_avoided': (1 - self.agent / self.total) * 100,
            'scenario_type': 'HIPOTÉTICO / NO MEDIDO / NO ES PRECISIÓN',
        }
