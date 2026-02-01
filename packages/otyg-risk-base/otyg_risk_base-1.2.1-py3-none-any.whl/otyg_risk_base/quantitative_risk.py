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

from decimal import *

from .montecarlo import MonteCarloRange, MonteCarloSimulation


class QuantitativeRisk():
    def __init__(self, values: dict = None):
        if not values:
            self.threat_event_frequency = MonteCarloRange()
            self.vuln_score = MonteCarloRange()
            self.loss_magnitude = MonteCarloSimulation()
            self.budget = Decimal(1000000)
            self.currency = "SEK"
        else:
            self.threat_event_frequency = MonteCarloRange.from_dict(values['threat_event_frequency'])
            self.vuln_score = MonteCarloRange.from_dict(values['vulnerability'])
            self.loss_magnitude = MonteCarloSimulation.from_dict(values.get('loss_magnitude'))
            self.budget = Decimal(values['budget'])
            self.currency = values['currency']
        if values and 'loss_event_frequency' in values:
            self.loss_event_frequency = MonteCarloSimulation.from_dict(values.get('loss_event_frequency'))
            if 'ale' in values and 'annual_loss_expectancy' in values:
                self.ale = MonteCarloSimulation.from_dict(values.get('ale'))
                self.annual_loss_expectancy = MonteCarloSimulation.from_dict(values.get('annual_loss_expectancy'))
            else:
                self.update_ale()
        else:
            self.loss_event_frequency = MonteCarloSimulation(self.threat_event_frequency.multiply(self.vuln_score))
            self.update_ale()
    
    def update_ale(self):
        self.ale = self.loss_event_frequency.multiply(self.loss_magnitude).multiply(self.budget)
        self.annual_loss_expectancy = MonteCarloSimulation(self.ale)

    def to_dict(self):
        return {
            "threat_event_frequency": self.threat_event_frequency.to_dict(),
            "vulnerability": self.vuln_score.to_dict(),
            "loss_event_frequency": self.loss_event_frequency.to_dict(),
            "loss_magnitude": self.loss_magnitude.to_dict(),
            "ale": self.ale.to_dict(),
            "annual_loss_expectancy": self.annual_loss_expectancy.to_dict(),
            "budget": float(self.budget),
            "currency": self.currency
        }
    @classmethod
    def from_dict(cls, values):
        risk = QuantitativeRisk()
        risk.threat_event_frequency = MonteCarloRange.from_dict(values['threat_event_frequency'])
        risk.vuln_score = MonteCarloRange.from_dict(values['vulnerability'])
        risk.loss_magnitude = MonteCarloSimulation.from_dict(values.get('loss_magnitude'))
        risk.budget = Decimal(values['budget'])
        risk.currency = values['currency']
        risk.loss_event_frequency = MonteCarloSimulation.from_dict(values.get('loss_event_frequency'))
        risk.ale = MonteCarloSimulation.from_dict(values.get('ale'))
        risk.annual_loss_expectancy = MonteCarloSimulation.from_dict(values.get('annual_loss_expectancy'))
        return risk
    
    def __repr__(self):
        return str(self.to_dict())
    
    def __eq__(self, other):
        if isinstance(other, QuantitativeRisk):
            return self.__hash__() == other.__hash__()
        return False
    
    def __gt__(self, other):
        if self == other:
            return False
        res = False
        
    def __hash__(self):
        return hash((self.threat_event_frequency, self.vuln_score, self.loss_event_frequency, self.loss_magnitude, self.ale, self.annual_loss_expectancy, self.budget, self.currency))
    def __str__(self):
        return str("ALE (p90): " + str(round(self.annual_loss_expectancy.p90, 2)) + f" {self.currency}/år\nALE (p50): " + str(round(self.annual_loss_expectancy.probable, 2)) + f" {self.currency}/år\n")
