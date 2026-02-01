
from typing import Dict, Tuple

from .qualitative_scale import QualitativeScale
from .utils import *


class QualitativeRisk():

    def __init__(self, likelihood_init:int=1, likelihood_impact:int=1, impact:int=1, mappings:QualitativeScale=None):
        if not mappings:
            self.mappings=QualitativeScale()
        else:
            self.mappings = mappings
        raw_likelihood = self.mappings.get(raw=likelihood_impact*likelihood_init, mapping="risk")
        self.overall_likelihood:str = raw_likelihood.get("text")
        self.overall_likelihood_num:int = raw_likelihood.get("numeric")
        self.likelihood_initiation_or_occurence:str = self.mappings.num_to_text[likelihood_init]
        self.likelihood_adverse_impact:str = self.mappings.num_to_text[likelihood_impact]
        self.impact:str = self.mappings.num_to_text[impact]
        self.overall_risk:str = self.mappings.get(raw=self.overall_likelihood_num*impact, mapping="risk").get("text")

    def get(self):
        return {'risk': self.overall_risk, 'likelihood': self.overall_likelihood, 'impact': self.impact}
    
    def to_dict(self):
        risk = {
            "overall_likelihood": self.overall_likelihood,
            "overall_likelihood_num" : self.overall_likelihood_num,
            "likelihood_initiation_or_occurence" : self.likelihood_initiation_or_occurence,
            "likelihood_adverse_impact" : self.likelihood_adverse_impact,
            "impact" : self.impact,
            "overall_risk" : self.overall_risk,
            "mappings": self.mappings.to_dict()
        }
        return risk
    @classmethod
    def from_dict(cls, values:dict):
        risk = QualitativeRisk()
        risk.overall_likelihood = values.get("overall_likelihood")
        risk.overall_likelihood_num = values.get("overall_likelihood_num")
        risk.likelihood_initiation_or_occurence = values.get("likelihood_initiation_or_occurence")
        risk.likelihood_adverse_impact = values.get("likelihood_adverse_impact")
        risk.impact = values.get("impact")
        risk.overall_risk = values.get("overall_risk")
        risk.mappings = QualitativeScale.from_dict(scales=values.get("mappings"))
        return risk

    def __hash__(self):
        return hash(freeze(self.to_dict()))
    
    def __eq__(self, other):
        return self.__hash__() == other.__hash__()