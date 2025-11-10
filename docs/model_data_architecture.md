## Loading Layout Data

**Goal:** Maintain an internal representation that is agnostic to the data source while enforcing validation and providing convenient indexing.

* The primary source is `warehouse-layout.json`, but other sources (e.g., databases, APIs, or alternate formats) are possible.

---

### Warehouse Location Model

* Each discrete warehouse location is represented as a Pydantic `BaseModel`, providing validation, serialization, and compatibility with frameworks such as FastAPI.
* The model computes a centroid upon initialization, used as a single spatial reference point for the location.

```python
class WarehouseLocationModel(BaseModel):
    """Represents a single discrete location in the warehouse."""

    rackface: str
    id: str
    name: str
    ...
    ...
    centroid: tuple[float, float, float] | None = None

    def model_post_init(self, __context: dict[Any, Any]) -> None:
        """Compute the centroid automatically after validation."""
        ...
```

---

### Warehouse Layout Model

`WarehouseLayoutModel` provides the in-memory representation of the full warehouse layout—a structured collection of `WarehouseLocationModel` instances.

* `locations`: mapping of unique name to `WarehouseLocationModel`
* `keys_by_rack_face`: mapping of rack-face to list of location keys
* `keys_by_column`: mapping of unique column to list of location keys

```python
LocationsStoreType = dict[str, WarehouseLocationModel]
LocationsByFeatureType = dict[str, list[str]]

class WarehouseLayoutModel(BaseModel):
    """Structured in-memory representation of the warehouse layout."""

    locations: LocationsStoreType
    keys_by_rack_face: LocationsByFeatureType
    keys_by_column: LocationsByFeatureType

    def get_location(self, name: str) -> WarehouseLocationModel:
        """Return a location by name."""
        return self.locations[name]
```

### Layout Loading

* `WarehouseLayoutLoader` defines an abstract interface for loading layout data into a `WarehouseLayoutModel`.
* Concrete implementations must implement `load()`, which parses raw data and returns a validated model.

```python
class WarehouseLayoutLoader(ABC):
    """Abstract base class for loading warehouse layout information."""

    @abstractmethod
    def load(self) -> WarehouseLayoutModel:
        """Parse raw layout data into structured models."""
        pass
```

* The `JsonWarehouseLayoutLoader` implementation deserializes `.json` data and populates the model.
* **Note: The provided JSON includes repeated warehouse locations; handling these requires clarification.**

## Connectivity Graph Creation

**Goal:** Provide a flexible and extensible approach to generate connectivity graphs from different strategies—e.g., random connections, geometry-based methods.

* The connectivity graph defines relationships between warehouse locations (nodes) and valid movements (edges).
* This abstraction enables pathfinding and cost computations independent of data source or layout format.

### Base Class: `ConnectivityMap`

Defines the common interface and shared utilities for all connectivity graph implementations.

* Stores an adjacency map: `dict[str, set[str]]` (each node mapped to connected neighbors).
* Provides helper methods for graph manipulation:
  * `add_edge`: connect two nodes
  * `get_neighbors`: list connected nodes
  * `has_node`: verify node existence
  * `compute_graph_size`: count nodes and edges
* Subclasses must implement `construct_graph()` to define connection logic.

```python
class ConnectivityMap(ABC):

    def __init__(self, warehouse_layout: WarehouseLayoutModel) -> None:
        """Initialize with a warehouse layout."""
        ...

    @abstractmethod
    def construct_graph(self) -> None:
        """Build the graph (nodes = locations, edges = paths)."""
        raise NotImplementedError

    def compute_graph_size(self) -> tuple[int, int]:
        """Return the number of nodes and edges."""
        ...

    def add_edge(self, node_a: str, node_b: str, bidirectional: bool = False) -> None:
        """Add an edge between two nodes."""
        ...

    def get_neighbors(self, node: str) -> list[str]:
        """Return a list of neighboring nodes."""
        ...

    def has_node(self, node: str) -> bool:
        """Check if a node exists in the graph."""
        ...
```

### Move Cost Integration

A move-cost calculator can be attached to compute travel costs between connected nodes.

```python
    def calculate_move_cost(self, node_a: str, node_b: str) -> float:
        """Return the movement cost between two connected nodes."""
        return self._move_cost_calculator.get_cost(
            warehouse_location_a, warehouse_location_b
        )

    def set_move_cost_calculator(
        self, move_cost_calculator: CachingMoveCostCalculator
    ) -> None:
        """Attach a cost calculator to this instance."""
        self._move_cost_calculator = move_cost_calculator
```

`CachingMoveCostCalculator` caches previously computed costs to avoid redundant calculations.

### Random Graph Implementation

`RandomConnectivityMap`—the current implementation—creates random paths ensuring full graph connectivity.

Future, geometry-aware versions should:

* Connect locations by spatial proximity (e.g., within distance thresholds).
* Constrain movement to valid travel corridors such as aisles or lanes.
* Prevent edges crossing racks, walls, or restricted zones.
* Assign edge weights by distance, time, or other cost metrics.
* Support 2D/3D grid projections for realistic navigation.
* Handle directional constraints (e.g., rack face orientation).

---

## Pathfinding

**Goal:** Provide a clean, extensible framework for implementing various pathfinding algorithms.

### Base Class: `PathFinder`

Abstract interface for computing optimal paths across a given connectivity map.

```python
class PathFinder(ABC):
    """Abstract base class defining the interface for optimal path computation."""

    def __init__(self, connectivity_map: ConnectivityMap):
        self.connectivity_map = connectivity_map
        super().__init__()

    @abstractmethod
    def compute_optimal_path(self, node_a: str, node_b: str) -> tuple[list[str], float]:
        """Compute the optimal path and total cost between two nodes."""
        pass
```

### `DijkstraPathFinder` Implementation

A concrete implementation using Dijkstra’s algorithm, ensuring globally optimal paths on any weighted connectivity graph.

### Demo workflow
All of these tools are run together to complete tasks in the `tasks.csv` within `demo_workflow.py`. Because of the extensible/reusable nature of each processing step, the workflow is highly configurable via `Hydra`, e.g.:

```yaml
layout:
  path: demo_data/warehouse-layout.json

tasks:
  csv_path: demo_data/tasks.csv
  location_column: location
  reserve_column: Reserve stock locations
  nearby_empty_column: Nearby empty locations
  output_dir: demo_output
  max_tasks: null

connectivity_map:
  _target_: adaptive_warehouse.connectivity_maps.RandomConnectivityMap
  _partial_: true
  seed: null

move_cost:
  _target_: adaptive_warehouse.move_cost.TimeBasedMoveCostCalculator
  speed_x: 1.0
  speed_y: 1.0
  speed_z: 0.5

pathfinder:
  _target_: adaptive_warehouse.pathfinding.DijkstraPathFinder
```

TODO
----

- Replace `RandomConnectivityMap` with a deterministic, geometry-aware implementation derived from actual aisle data.
- Expand `TimeBasedMoveCostCalculator` to account for turn costs, acceleration limits, and congestion penalties.
- Add an A* (or faster) path planner and benchmark against the existing Dijkstra implementation.
- Build end-to-end tests that load real layouts, run representative pick tasks, and assert both path feasibility and latency budgets.
- git LFS for demo files