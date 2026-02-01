import unittest

from src.otyg_risk_base.hybrid import HybridRisk

class TestQuantitativeRisk(unittest.TestCase):
    def test_set_qualitative(self):
        risk = HybridRisk({'threat_event_frequency': {'min':0,'probable':1,'max':2}, 'vulnerability': {'min':0,'probable':2,'max':3}, 'loss_magnitude':{'min':1,'probable':2,'max':3}, 'budget': 10000, 'currency':"SEK"})
        self.assertEqual(risk.qualitative.overall_risk, "Very High")
        self.assertEqual(risk.qualitative.overall_likelihood, "High")
        self.assertEqual(risk.qualitative.impact, "Very High")
    
    def test_equality(self):
        risk = HybridRisk({'threat_event_frequency': {'min':0,'probable':1,'max':2}, 'vulnerability': {'min':1,'probable':2,'max':3}, 'loss_magnitude':{'min':3,'probable':4,'max':5}, 'budget': 10000, 'currency':"SEK"})
        self.assertTrue(risk == risk)
        risk_mod = HybridRisk({'threat_event_frequency': {'min':1,'probable':3,'max':5}, 'vulnerability': {'min':1,'probable':2,'max':3}, 'loss_magnitude':{'min':3,'probable':4,'max':5}, 'budget': 10000, 'currency':"SEK"})
        self.assertFalse(risk == risk_mod)
    
    def test_serialization_deserialization(self):
        risk = HybridRisk({'threat_event_frequency': {'min':0,'probable':1,'max':2}, 'vulnerability': {'min':1,'probable':2,'max':3}, 'loss_magnitude':{'min':3,'probable':4,'max':5}, 'budget': 10000, 'currency':"SEK"})
        risk_new = HybridRisk.from_dict(risk.to_dict())
        self.assertTrue(risk == risk_new)
        risk_mod = HybridRisk({'threat_event_frequency': {'min':1,'probable':3,'max':5}, 'vulnerability': {'min':1,'probable':2,'max':3}, 'loss_magnitude':{'min':3,'probable':4,'max':5}, 'budget': 10000, 'currency':"SEK"})
        risk_new = HybridRisk.from_dict(risk_mod.to_dict())
        self.assertFalse(risk == risk_new)
        self.assertTrue(risk_mod == risk_new)