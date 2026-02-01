#
# BSD 3-Clause License
#
# Copyright (c) 2026, Martin Vesterlund
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from .qualitative_scale import QualitativeScale
from .montecarlo import MonteCarloRange
from .qualitative_risk import QualitativeRisk
from .utils import *
from .quantitative_risk import QuantitativeRisk

class HybridRisk():
    def __init__(self, values:dict = None):
        # TODO: Markörer för vad som finns i dicten
        if values:
            if "mappings" in values:
                qs = QualitativeScale(scales=values.get('mappings'))
            else:
                qs = QualitativeScale()
            self.quantitative = QuantitativeRisk(values=values)
            self.qualitative = QualitativeRisk(
            likelihood_init=qs.get(raw=self.quantitative.threat_event_frequency.probable, mapping='likelihood_initiation_or_occurence').get('numeric'),
            likelihood_impact=qs.get(raw=self.quantitative.vuln_score.probable, mapping='likelihood_adverse_impact').get('numeric'),
                impact=qs.get(raw=self.quantitative.loss_magnitude.probable, mapping='impact').get('numeric'),
                mappings=qs)
        else:
            self.quantitative = QuantitativeRisk()
            qs = QualitativeScale()
            self.qualitative = QualitativeRisk(
                likelihood_init=qs.get(raw=self.quantitative.threat_event_frequency.probable, mapping='likelihood_initiation_or_occurence').get('numeric'),
                likelihood_impact=qs.get(raw=self.quantitative.vuln_score.probable, mapping='likelihood_adverse_impact').get('numeric'),
                impact=qs.get(raw=self.quantitative.loss_magnitude.probable, mapping='impact').get('numeric'),
                mappings=qs)
    def to_dict(self):
        me = {
            "quantitative": self.quantitative.to_dict(),
            "qualitative": self.qualitative.to_dict()
        }
        return me
    @classmethod
    def from_dict(cls, values:dict):
        me = HybridRisk(values=None)
        me.qualitative = QualitativeRisk.from_dict(values=values.get('qualitative'))
        me.quantitative = QuantitativeRisk.from_dict(values=values.get('quantitative'))
        return me

    def get(self):
        return self.risk.copy()
    
    def __hash__(self):
        return hash((self.qualitative, self.quantitative))
    
    def __eq__(self, value):
        return self.__hash__() == value.__hash__()