from decimal import Decimal
import unittest

from src.otyg_risk_base.montecarlo import MonteCarloRange, MonteCarloSimulation

class TestMonteCarloRange(unittest.TestCase):
    def test_no_arg(self):
        mr = MonteCarloRange()
        self.assertEqual(mr.probable, Decimal(0))
    
    def test_probable_less_than_min(self):
        with self.assertRaises(ValueError):
            mc = MonteCarloRange(min= 1, probable=0, max=2)
    
    def test_equals(self):
        actual = MonteCarloRange(min= 0, probable=1, max=2)
        other = MonteCarloRange(min= 0, probable=1, max=2)
        other_neq = MonteCarloRange(min= 1, probable=2, max=3)
        self.assertTrue(actual == actual)
        self.assertTrue(actual == other)
        self.assertFalse(actual == other_neq)
        self.assertFalse(actual == 1)

    def test_add(self):
        actual = MonteCarloRange(min= 0, probable=1, max=2).add(MonteCarloRange(min= 1, probable=2, max=3))
        expected = MonteCarloRange(min= 1, probable=3, max=5)
        actual_scalar = MonteCarloRange(min= 0, probable=1, max=2).add(1)
        expected_scalar = MonteCarloRange(min= 1, probable=2, max=3)
        not_expected = MonteCarloRange(min= 2, probable=3, max=5)
        self.assertTrue(actual == expected)
        self.assertTrue(actual_scalar == expected_scalar)
        self.assertFalse(actual == not_expected)

    def test_serialization_and_deserialization(self):
        original = MonteCarloRange(min= 1, probable=3, max=5)
        org_dict = original.to_dict()
        copy = MonteCarloRange.from_dict(org_dict)
        self.assertEqual(original, copy)
        self.assertNotEqual(original, MonteCarloRange.from_dict({
            "min": 1,
            "probable": 3,
            "max": 10
        }))
        
class TestMonteCarloSimulation(unittest.TestCase):
    def test_creation(self):
        range = MonteCarloRange(min=1, probable=2, max=3)
        sim = MonteCarloSimulation(range=range)
        self.assertAlmostEqual(sim.min, 1, delta=0.1)
        self.assertAlmostEqual(sim.probable, 2, delta=0.1)
        self.assertAlmostEqual(sim.max, 3, delta=0.1)
        self.assertAlmostEqual(sim.p90, Decimal(2.5), delta=0.1)
    
    def test_equals(self):
        sim = MonteCarloSimulation(range=MonteCarloRange(min=1, probable=2, max=3))
        other = MonteCarloSimulation(range=MonteCarloRange(min=1, probable=2, max=3))
        self.assertTrue(sim == sim)
        self.assertFalse(sim == other)
    
    def test_serialization_deserialization(self):
        sim = MonteCarloSimulation(range=MonteCarloRange(min=1, probable=2, max=3))
        other = MonteCarloSimulation().from_dict(sim.to_dict())
        self.assertTrue(sim == other)
    
    def test_multiplication(self):
        first = MonteCarloSimulation(range=MonteCarloRange(min=1, probable=2, max=3))
        second = MonteCarloSimulation(range=MonteCarloRange(min=1, probable=2, max=3))
        
        mul = first.multiply(second)
        mul_oper = first * second
        mul_roper = second * first
        threshold = 0.3
        self.assertAlmostEqual(mul.min, 1, delta=threshold)
        self.assertAlmostEqual(mul.min, mul_oper.min, delta=threshold)
        self.assertAlmostEqual(mul.min, mul_roper.min, delta=threshold)
        self.assertAlmostEqual(mul.probable, 4, delta=1)
        self.assertAlmostEqual(mul.probable, mul_oper.probable, delta=1)
        self.assertAlmostEqual(mul.probable, mul_roper.probable, delta=1)
        self.assertAlmostEqual(mul.max, 9, delta=threshold)
        self.assertAlmostEqual(mul.max, mul_oper.max, delta=threshold)
        self.assertAlmostEqual(mul.max, mul_roper.max, delta=threshold)
        self.assertAlmostEqual(mul.p90, Decimal(7), delta=threshold)
        self.assertAlmostEqual(mul.p90, mul_oper.p90, delta=threshold)
        self.assertAlmostEqual(mul.p90, mul_roper.p90, delta=threshold)
        scalar = 2
        mul_scalar = first.multiply(scalar)
        mul_scalar_oper = first * scalar
        mul_scalar_roper = scalar * first
        self.assertAlmostEqual(mul_scalar.min, 2, delta=threshold)
        self.assertAlmostEqual(mul_scalar.min, mul_scalar_oper.min, delta=threshold)
        self.assertAlmostEqual(mul_scalar.min, mul_scalar_roper.min, delta=threshold)
        self.assertAlmostEqual(mul_scalar.probable, 4, delta=1)
        self.assertAlmostEqual(mul_scalar.probable, mul_scalar_oper.probable, delta=1)
        self.assertAlmostEqual(mul_scalar.probable, mul_scalar_roper.probable, delta=1)
        self.assertAlmostEqual(mul_scalar.max, 6, delta=threshold)
        self.assertAlmostEqual(mul_scalar.max, mul_scalar_oper.max, delta=threshold)
        self.assertAlmostEqual(mul_scalar.max, mul_scalar_roper.max, delta=threshold)
        self.assertAlmostEqual(mul_scalar.p90, Decimal(5), delta=threshold)
        self.assertAlmostEqual(mul_scalar.p90, mul_scalar_oper.p90, delta=threshold)
        self.assertAlmostEqual(mul_scalar.p90, mul_scalar_roper.p90, delta=threshold)
    
    def test_addition(self):
        first = MonteCarloSimulation(range=MonteCarloRange(min=1, probable=2, max=3))
        second = MonteCarloSimulation(range=MonteCarloRange(min=1, probable=2, max=3))
        
        add = first.add(second)
        add_oper = first + second
        add_roper = second + first
        threshold = 0.3
        self.assertAlmostEqual(add.min, 2, delta=threshold)
        self.assertAlmostEqual(add.min, add_oper.min, delta=threshold)
        self.assertAlmostEqual(add.min, add_roper.min, delta=threshold)
        self.assertAlmostEqual(add.probable, 4, delta=1)
        self.assertAlmostEqual(add.probable, add_oper.probable, delta=1)
        self.assertAlmostEqual(add.probable, add_roper.probable, delta=1)
        self.assertAlmostEqual(add.max, 6, delta=threshold)
        self.assertAlmostEqual(add.max, add_oper.max, delta=threshold)
        self.assertAlmostEqual(add.max, add_roper.max, delta=threshold)
        self.assertAlmostEqual(add.p90, Decimal(5), delta=threshold)
        self.assertAlmostEqual(add.p90, add_oper.p90, delta=threshold)
        self.assertAlmostEqual(add.p90, add_roper.p90, delta=threshold)
        scalar = 2
        add_scalar = first.add(scalar)
        add_scalar_oper = first + scalar
        add_scalar_roper = scalar + first
        self.assertAlmostEqual(add_scalar.min, 3, delta=threshold)
        self.assertAlmostEqual(add_scalar.min, add_scalar_oper.min, delta=threshold)
        self.assertAlmostEqual(add_scalar.min, add_scalar_roper.min, delta=threshold)
        self.assertAlmostEqual(add_scalar.probable, 4, delta=1)
        self.assertAlmostEqual(add_scalar.probable, add_scalar_oper.probable, delta=1)
        self.assertAlmostEqual(add_scalar.probable, add_scalar_roper.probable, delta=1)
        self.assertAlmostEqual(add_scalar.max, 5, delta=threshold)
        self.assertAlmostEqual(add_scalar.max, add_scalar_oper.max, delta=threshold)
        self.assertAlmostEqual(add_scalar.max, add_scalar_roper.max, delta=threshold)
        self.assertAlmostEqual(add_scalar.p90, Decimal(4), delta=0.6)
        self.assertAlmostEqual(add_scalar.p90, add_scalar_oper.p90, delta=0.6)
        self.assertAlmostEqual(add_scalar.p90, add_scalar_roper.p90, delta=0.6)
    
    def test_delta(self):
        first = MonteCarloSimulation(range=MonteCarloRange(min=1, probable=2, max=3))
        second = MonteCarloSimulation(range=MonteCarloRange(min=2, probable=4, max=6))
        scalar = 2
        sub = first.delta(second)
        sub_scalar = first.delta(scalar)
        # 1-2 = -1, 2-4 = -2, 3-6 = -3
        threshold = 0.3
        self.assertAlmostEqual(sub.min, -3, delta=threshold)
        self.assertAlmostEqual(sub.probable, -2, delta=threshold)
        self.assertAlmostEqual(sub.max, -1, delta=threshold)
        self.assertAlmostEqual(sub_scalar.min, -1, delta=threshold)
        self.assertAlmostEqual(sub_scalar.probable, 0, delta=threshold)
        self.assertAlmostEqual(sub_scalar.max, 1, delta=threshold)

if __name__ == '__main__':
    unittest.main()