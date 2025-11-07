import pytest
import numpy as np

from dexory.models import Coord3DModel, BoundsModel, WarehouseLocationModel
from dexory.move_cost import CachingMoveCostCalculator, TimeBasedMoveCostCalculator


def test_get_cost_caches_results(loc_a, loc_b):
    """Ensure get_cost caches computed results."""

    class DummyCalc(CachingMoveCostCalculator):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def compute_cost(self, node_a, node_b):
            self.calls += 1
            return 123.45

    calc = DummyCalc()

    first = calc.get_cost(loc_a, loc_b)
    second = calc.get_cost(loc_a, loc_b)

    assert first == second == 123.45
    assert calc.calls == 1  # Computed only once


def test_clear_cache(loc_a, loc_b):
    """Clearing the cache should remove stored values."""
    class DummyCalc(CachingMoveCostCalculator):
        def compute_cost(self, node_a, node_b):
            return 1.0

    calc = DummyCalc()
    calc.get_cost(loc_a, loc_b)
    assert len(calc.move_cost_cache) == 1

    calc.clear_cache()
    assert calc.move_cost_cache == {}

def test_compute_cost_correctness(loc_a, loc_b):
    """Verify correct computation of axis-based travel time."""
    calc = TimeBasedMoveCostCalculator(speed_x=2.0, speed_y=3.0, speed_z=4.0)

    cost = calc.compute_cost(loc_a, loc_b)

    # Expected cost: |Δx|/speed_x + |Δy|/speed_y + |Δz|/speed_z
    c0 = np.array(loc_a.centroid)
    c1 = np.array(loc_b.centroid)
    expected = np.abs(c1 - c0) / np.array([2.0, 3.0, 4.0])
    assert np.isclose(cost, expected.sum(), atol=1e-8)


def test_get_cost_uses_cache(loc_a, loc_b):
    """get_cost() should cache computed results."""
    calc = TimeBasedMoveCostCalculator()

    first = calc.get_cost(loc_a, loc_b)
    second = calc.get_cost(loc_a, loc_b)

    assert first == second
    assert len(calc.move_cost_cache) == 1
