import unittest

from src.otyg_risk_base.qualitative_scale import QualitativeScale



class TestQualitativeScale(unittest.TestCase):
    def test_get(self):
        scale = QualitativeScale()
        self.assertEqual(scale.get(raw=0.0001, mapping="likelihood_initiation_or_occurence").get('numeric'), 1)
        self.assertEqual(scale.get(raw=0.1, mapping="likelihood_initiation_or_occurence").get('numeric'), 2)
        self.assertEqual(scale.get(raw=0.1, mapping="likelihood_initiation_or_occurence").get('text'), "Low")
        self.assertEqual(scale.get(raw=0.06, mapping="impact").get('text'), "Very High")
        self.assertEqual(scale.get(raw=0.74, mapping="likelihood_adverse_impact").get('text'), "High")
        self.assertEqual(scale.get(raw=16, mapping="risk").get('text'), "High")
    
    
if __name__ == '__main__':
    unittest.main()