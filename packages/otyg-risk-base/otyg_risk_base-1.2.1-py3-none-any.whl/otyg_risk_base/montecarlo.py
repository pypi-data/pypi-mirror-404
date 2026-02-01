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

import numpy as np
from decimal import *


class MonteCarloRange():
    def __init__(self, min: Decimal = Decimal(0.00), probable: Decimal = Decimal(0.00), max: Decimal = Decimal(0.00)):
        if not (max == min) and ((probable < min) or (probable > max) or (min > max)):
            raise ValueError
        self.max = Decimal(max)
        self.min = Decimal(min)
        self.probable = Decimal(probable)
        if not self.probable.is_zero() and (self.max == self.min):
            self.max = Decimal(self.probable*2)
            self.min = Decimal(self.probable/2)
        elif self.probable.is_zero and not self.max.is_zero():
            self.probable = (self.min + self.max)/2

    def to_dict(self):
        return {
            "min": float(self.min),
            "probable": float(self.probable),
            "max": float(self.max)
        }
    
    def add(self, other = None):
        if isinstance(other, MonteCarloRange):
            max = self.max + other.max
            min = self.min + other.min
            probable = self.probable + other.probable
        else:
            max = self.max + other
            min = self.min + other
            probable = self.probable + other
        result = MonteCarloRange(min=Decimal(min), probable=Decimal(probable), max=Decimal(max))
        return result

    def sub(self, other = None):
        if isinstance(other, MonteCarloRange):
            max = self.max - other.max
            min = self.min - other.min
            probable = self.probable - other.probable
        else:
            max = self.max - other
            min = self.min - other
            probable = self.probable - other
        if max < min:
            tmp = max
            max = min
            min = tmp
        result = MonteCarloRange(min=Decimal(min), probable=Decimal(probable), max=Decimal(max))
        return result
    
    def multiply(self, other = None):
        if isinstance(other, MonteCarloRange):
            max = self.max * other.max
            min = self.min * other.min
            probable = self.probable * other.probable
        else:
            max = Decimal(self.max) * Decimal(other)
            min = Decimal(self.min) * Decimal(other)
            probable = Decimal(self.probable) * Decimal(other)
        result = MonteCarloRange(min=Decimal(min), probable=Decimal(probable), max=Decimal(max))
        return result

    @classmethod
    def from_dict(cls, values:dict=None):
        if isinstance(values, dict):
            return MonteCarloRange(min=values['min'], probable=values['probable'], max=values['max'])
        else:
            raise TypeError()

    def __repr__(self):
        return str(self.to_dict())
    
    def __hash__(self):
        return hash((self.min, self.max, self.probable))
    
    def __eq__(self, other):
        if isinstance(other, MonteCarloRange) and self.__hash__() == other.__hash__():
            return True
        return False
    
    def __gt__(self, other):
        if self == other:
            return False
        if self.min >= other.min and self.max > other.max:
            return True
        return False

class PertDistribution():
    def __init__(self,range: MonteCarloRange):
        rng = np.random.default_rng()
        delta_min_max = range.max - range.min
        alpha = 1 + ((range.probable - range.min) * 4) / delta_min_max
        beta = 1 + ((range.max - range.probable) * 4) / delta_min_max
        self.__samples = float(range.min) + rng.beta(alpha, beta, 100000) * float(delta_min_max)

    def get(self):
        return self.__samples.copy()


class MonteCarloSimulation():
    def __init__(self, range: MonteCarloRange=None):
        if not range:
            range = MonteCarloRange(probable=Decimal(1))
        if (range.min == range.max == range.probable):
            self.probable = Decimal(range.probable)
            range.max = Decimal(Decimal(range.probable)+Decimal(0.000000000001))
            range.min = Decimal(Decimal(range.probable)-Decimal(0.000000000001))
        
        pd = PertDistribution(range=range)
        self.__samples = pd.get()
        self.probable = Decimal(np.mean(self.__samples))
        self.p90 = Decimal(np.percentile(self.__samples, 90))
        self.max = Decimal(np.max(self.__samples))
        self.min = Decimal(np.min(self.__samples))

    def to_dict(self):
        return {
            "min": float(self.min),
            "probable": float(self.probable),
            "max": float(self.max),
            "p90": float(self.p90),
            "__samples": self.__samples
        }
    
    @classmethod
    def from_dict(cls, dict:dict={}):
        if 'p90' in dict:
            mcs = MonteCarloSimulation()
            mcs.min = Decimal(dict['min'])
            mcs.probable = Decimal(dict['probable'])
            mcs.max = Decimal(dict['max'])
            mcs.p90 = Decimal(dict['p90'])
            mcs.__samples = np.array(dict.get('__samples', []))
            return mcs
        else:
            range = MonteCarloRange.from_dict(dict)
            return MonteCarloSimulation(range=range)
    
    def get_montecarlo_range(self):
        return MonteCarloRange(min=self.min, probable=self.probable, max=self.max)
        
    def multiply(self, other):
        if isinstance(other, MonteCarloSimulation):
            range = self.get_montecarlo_range().multiply(other=other.get_montecarlo_range())
        else:
            range = self.get_montecarlo_range().multiply(other=other)
        return MonteCarloSimulation(range=range)
    
    def add(self, other):
        if isinstance(other, MonteCarloSimulation):
            range = self.get_montecarlo_range().add(other=other.get_montecarlo_range())
        else:
            range = self.get_montecarlo_range().add(other=other)
        return MonteCarloSimulation(range=range)
    
    def delta(self, other):
        if isinstance(other, MonteCarloSimulation):
            range = self.get_montecarlo_range().sub(other=other.get_montecarlo_range())
        else:
            range = self.get_montecarlo_range().sub(other=other)
        return MonteCarloSimulation(range=range)
    
    def __add__(self, other):
        return self.add(other)
    def __radd__(self, other):
        return self.add(other)
    def __mul__(self, other):
        return self.multiply(other)
    def __rmul__(self, other):
        return self.multiply(other)
    def __repr__(self):
        return str(self.to_dict())
    
    def __str__(self):
        return f"min: {str(self.min)} mode: {str(self.probable)} p90: {str(self.p90)} max: {str(self.max)}"
    
    def __hash__(self):
        return hash((self.min, self.probable, self.p90, self.max))
    
    def __eq__(self, value):
        if isinstance(value, MonteCarloSimulation) and self.__hash__() == value.__hash__():
            return True
        return False
    
    def __gt__(self, other):
        if self == other:
            return False
        if self.min >= other.min and self.max > other.max:
            return True
        return False