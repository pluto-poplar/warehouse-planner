from abc import ABC, abstractmethod

import numpy as np

from dexory.models import WarehouseLocationModel

MoveCostCacheType = dict[tuple[str, str], float]


class CachingMoveCostCalculator(ABC):
    """Abstract class for a computing and caching move costs between nodes."""

    def __init__(self) -> None:
        super().__init__()
        self.move_cost_cache: MoveCostCacheType = {}

    @abstractmethod
    def compute_cost(
        self, loc_0: WarehouseLocationModel, loc_1: WarehouseLocationModel
    ) -> float:
        pass

    def get_cost(
        self, loc_0: WarehouseLocationModel, loc_1: WarehouseLocationModel
    ) -> float:
        """Return cached move cost if available, otherwise compute and cache it."""

        key = (loc_0.name, loc_0.name)
        if key in self.move_cost_cache:
            return self.move_cost_cache[key]

        # Compute the cost and store it
        # Note accessing via nested objects probably a bad idea long term
        cost = self.compute_cost(loc_0, loc_1)

        # Note, assuming cost is not bidirectional
        self.move_cost_cache[key] = cost

        return cost

    def clear_cache(self) -> None:
        """Clear all cached move costs."""
        self.move_cost_cache.clear()


class TimeBasedMoveCostCalculator(CachingMoveCostCalculator):
    """Implementation of caching calculator for time-based move cost."""

    def __init__(
        self,
        speed_x: float = 1.0,
        speed_y: float = 1.0,
        speed_z: float = 0.5,
    ):
        super().__init__()
        self._speed_x = speed_x
        self._speed_y = speed_y
        self._speed_z = speed_z

    def compute_cost(
        self, loc_0: WarehouseLocationModel, loc_1: WarehouseLocationModel
    ) -> float:
        if loc_0.centroid is None or loc_1.centroid is None:
            raise ValueError("Centroid is None.")
        centroid_0 = np.array(loc_0.centroid)
        centroid_1 = np.array(loc_1.centroid)
        diff = np.abs(centroid_1 - centroid_0)
        cost_x = diff[0] / self._speed_x
        cost_y = diff[1] / self._speed_y
        cost_z = diff[2] / self._speed_z
        return float(cost_x + cost_y + cost_z)
