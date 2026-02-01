from typing import Dict, List, Tuple

from .utils import freeze

class QualitativeScale():
    DEFAULT_NUM_TO_TEXT:Dict[str, int] = {
        5: 'Very High',
        4: 'High',
        3: 'Moderate',
        2: 'Low',
        1: 'Very Low',
        0: 'Very Low'
    }

    DEFAULT_RANGE_TO_TEXT: List[Dict] = [
        {'value':1, 'low': 1, 'high': 5},
        {'value':2, 'low': 5, 'high': 9},
        {'value':3, 'low': 9, 'high': 13},
        {'value':4, 'low': 13, 'high': 20},
        {'value':5, 'low': 20, 'high': 26},
    ]

    DEFAULT_TEF: List[Dict] = [
        {'value':1, 'low': 0.01, 'high': 0.1},
        {'value':2, 'low': 0.1, 'high': 1},
        {'value':3, 'low': 1, 'high': 10},
        {'value':4, 'low': 10, 'high': 100},
        {'value':5, 'low': 100, 'high': 1000},
    ]

    DEFAULT_VULNERABILITY: List[Dict] = [
        {'value':1, 'low': 0.01, 'high': 0.12},
        {'value':2, 'low': 0.12, 'high': 0.25},
        {'value':3, 'low': 0.25, 'high': 0.5},
        {'value':4, 'low': 0.5, 'high': 0.75},
        {'value':5, 'low': 0.75, 'high': 1},
    ]

    DEFAULT_CONSEQUENCE: List[Dict] = [
        {'value':1, 'low': 0.0001, 'high': 0.005},
        {'value':2, 'low': 0.005, 'high': 0.01},
        {'value':3, 'low': 0.01, 'high': 0.02},
        {'value':4, 'low': 0.02, 'high': 0.05},
        {'value':5, 'low': 0.05, 'high': 1},
    ]
    def __init__(self, scales:dict = None):
        if not scales:
            scales = dict()
        self.likelihood_initiation_or_occurence = scales.get('likelihood_initiation_or_occurence', self.DEFAULT_TEF)
        self.likelihood_adverse_impact = scales.get('likelihood_adverse_impact', self.DEFAULT_VULNERABILITY)
        self.impact = scales.get('impact', self.DEFAULT_CONSEQUENCE)
        self.num_to_text = scales.get('num_to_text', self.DEFAULT_NUM_TO_TEXT)
        self.risk = scales.get('risk', self.DEFAULT_RANGE_TO_TEXT)

    def to_dict(self):
        return {
            'likelihood_initiation_or_occurence': self.likelihood_initiation_or_occurence,
            'likelihood_adverse_impact': self.likelihood_adverse_impact,
            'impact': self.impact,
            'num_to_text': self.num_to_text,
            'risk': self.risk,
        }
    def __hash__(self):
        return hash(freeze(self.to_dict()))
    
    def __eq__(self, other):
        return self.__hash__() == other.__hash__()
    
    @classmethod
    def from_dict(cls, scales: dict):
        tmp = QualitativeScale()
        tmp.likelihood_initiation_or_occurence = scales.get('likelihood_initiation_or_occurence', cls.DEFAULT_TEF)
        tmp.likelihood_adverse_impact = scales.get('likelihood_adverse_impact', cls.DEFAULT_VULNERABILITY)
        tmp.impact = scales.get('impact', cls.DEFAULT_CONSEQUENCE)
        tmp.num_to_text = scales.get('num_to_text', cls.DEFAULT_NUM_TO_TEXT)
        tmp.risk = scales.get('risk', cls.DEFAULT_RANGE_TO_TEXT)
        return tmp
    
    def get(self, raw, mapping):
        scale = getattr(self, mapping, None)
        num = None
        if not scale:
            raise AttributeError(f"{mapping} does not exist")
        if raw < scale[0].get('low'):
            num = scale[0].get('value')
        elif raw > scale[-1].get('low'):
            num = scale[-1].get('value')
        else:
            for range in scale:
                if range.get('low') <= raw < range.get('high'):
                    num = range.get('value')
        return {'numeric': num, 'text': self.num_to_text.get(num)}
