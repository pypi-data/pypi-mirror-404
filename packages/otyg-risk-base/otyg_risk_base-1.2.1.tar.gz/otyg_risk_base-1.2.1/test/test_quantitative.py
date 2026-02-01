import unittest

from src.otyg_risk_base.quantitative_risk import QuantitativeRisk



class TestQuantitativeRisk(unittest.TestCase):
    def test_no_arg(self):
        risk = QuantitativeRisk()
        self.assertIsInstance(risk, QuantitativeRisk)
        for s in ["threat_event_frequency","vulnerability","loss_event_frequency","loss_magnitude","annual_loss_expectancy","budget","currency"]:
            self.assertIn(s, risk.to_dict())

    def test_equality(self):
        risk = QuantitativeRisk()
        self.assertTrue(risk == risk)
    
    def test_serialization_deserialization(self):
        risk = QuantitativeRisk()
        new_risk = QuantitativeRisk.from_dict(risk.to_dict())
        self.assertTrue(risk == new_risk)
        risk = QuantitativeRisk({'threat_event_frequency': {'min':0,'probable':1,'max':2}, 'vulnerability': {'min':1,'probable':2,'max':3}, 'loss_magnitude':{'min':3,'probable':4,'max':5}, 'budget': 10000, 'currency':"SEK"})
        new_risk_2 = QuantitativeRisk.from_dict(risk.to_dict())
        self.assertTrue(risk == new_risk_2)
        self.assertFalse(risk == new_risk)

if __name__ == '__main__':
    unittest.main()