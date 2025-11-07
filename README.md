Dexory Pathfinding Demo
=======================

This repository contains a simplified pathfinding stack for warehouse layouts.
It includes:

- Layout models and loaders using Pydantic.
- Connectivity maps with configurable move-cost calculators.
- Pathfinders (Dijkstra) that operate on the connectivity graph.
- A demo workflow that wires the components together.

Prerequisites
-------------

Install [uv](https://github.com/astral-sh/uv) if it is not already available:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Quick Start
-----------

1. Install dependencies:

   ```
   uv sync
   ```

2. Run the test suite:

   ```
   uv run poe test
   ```

3. Execute the demo workflow (components are configured via `workflows/conf/demo.yaml`):

   ```
   uv run python workflows/demo_workflow.py
   ```

   Override parameters as needed, for example:

   ```
   uv run python workflows/demo_workflow.py connectivity_map.seed=42
   ```

Project Structure
-----------------

- `src/dexory/models.py`: Warehouse location models.
- `src/dexory/warehouse_layout.py`: Layout loader abstractions.
- `src/dexory/move_cost.py`: Move cost calculators (caching, time-based).
- `src/dexory/connectivity_maps.py`: Graph generation logic.
- `src/dexory/pathfinding.py`: PathFinder base and Dijkstra implementation.
- `workflows/demo_workflow.py`: Demo script for running tasks.
- `workflows/conf/demo.yaml`: Default configuration for the demo.
- `tests/`: Pytest suites for layout and cost components.

Execution Flow
--------------

1. `JsonWarehouseLayoutLoader` parses `demo_data/warehouse-layout.json` into a `WarehouseLayout`.
2. `RandomConnectivityMap` (or another map implementation) builds adjacency lists from the layout.
3. `TimeBasedMoveCostCalculator` is attached to the map to compute edge weights.
4. `DijkstraPathFinder` consumes the map and exposes `compute_optimal_path`.
5. The workflow reads `demo_data/tasks.csv`, extracts source/reserve pairs, and prints the resulting paths/costs.

Limitations
-----------

| Area | Current State | Needed Improvement |
| ---- | ------------- | ------------------ |
| Connectivity graphs | `RandomConnectivityMap` links nodes via random shuffles, ignoring layout geometry. | Implement aisle-aware graph builder that respects travel corridors (and then later one-way aisles, forbidden zones, and dynamic obstacles). |
| Move cost modeling | Basic axis-aligned time estimates. | It would be nice to incorporate richer models (turn penalties, acceleration limits, congestion feedback, lift restrictions) sourced from telemetry and safety rules. |
| Path planning | Dijkstra explores the entire reachable subgraph. | Introduce heuristic planners such as A* for better scalability. |
| Validation | Unit tests cover foundational components only. | Add integration/system tests validating path optimality and cost sanity against curated layouts plus performance benchmarks under load. |

TODO
----

- Replace `RandomConnectivityMap` with a deterministic, geometry-aware implementation derived from actual aisle data.
- Add an A* (or faster) path planner and benchmark against the existing Dijkstra implementation.
- Build end-to-end tests that load real layouts, run representative pick tasks, and assert both path feasibility and latency budgets.
- Add linting to CI
