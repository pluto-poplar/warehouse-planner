Adaptive_Warehouse Pathfinding
=======================

This repository contains a simplified pathfinding stack for warehouse layouts.
It includes:

- Layout models and loaders using Pydantic.
- Connectivity maps with configurable move-cost calculators.
- Pathfinders (Dijkstra) that operate on the connectivity graph.
- A demo workflow that wires the components together.

**The current implementation uses a random connectivity graph and a very basic pathfinder, so it runs slowly and produces results that aren’t physically meaningful. The system, however, is designed to be highly extensible and modular, making it easy to incorporate better graph construction methods and pathfinding algorithms. I would have liked to explore this further, but due to time constraints, it seemed more important to build a solid foundation on which these tools can be developed.**

- [Full model and data architecture description](docs/model_data_architecture.md)
- [Production system ideas](docs/production_system.md)

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
   uv run workflows/demo_workflow.py
   ```

   Override parameters as needed, for example:

   ```
   uv run workflows/demo_workflow.py tasks.max_tasks=10 # Only solve 10 tasks
   ```

- Lowest-cost destination selections (evaluated across both `Reserve stock locations` and `Nearby empty locations`) are written to `tasks.output_dir/tasks_solution.csv` (defaults to `demo_output/tasks_solution.csv`).
- Set `tasks.max_tasks=<N>` to restrict how many rows from the task CSV are processed (e.g., `tasks.max_tasks=10` for smoke tests).
- Adjust the CSV column names via `tasks.reserve_column` and `tasks.nearby_empty_column` if headers differ.

Project Structure
-----------------

- `src/adaptive_warehouse/models.py`: Warehouse location models.
- `src/adaptive_warehouse/warehouse_layout.py`: Layout loader abstractions.
- `src/adaptive_warehouse/move_cost.py`: Move cost calculators (caching, time-based).
- `src/adaptive_warehouse/connectivity_maps.py`: Graph generation logic.
- `src/adaptive_warehouse/pathfinding.py`: PathFinder base and Dijkstra implementation.
- `workflows/demo_workflow.py`: Demo script for running tasks.
- `workflows/conf/demo.yaml`: Default configuration for the demo.
- `tests/`: Pytest suites for layout and cost components.

Execution Flow
--------------

1. `JsonWarehouseLayoutLoader` parses `demo_data/warehouse-layout.json` into a `WarehouseLayout`.
2. `RandomConnectivityMap` (or another map implementation) builds adjacency lists from the layout.
3. `TimeBasedMoveCostCalculator` is attached to the map to compute edge weights.
4. `DijkstraPathFinder` consumes the map and exposes `compute_optimal_path`.
5. The workflow reads `demo_data/tasks.csv`, merges the `Reserve stock locations` and `Nearby empty locations` pools for each task, and evaluates every candidate destination (respecting `tasks.max_tasks` if set).
6. The winning destination and its cost (seconds) are saved to `tasks.output_dir/tasks_solution.csv`.

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
- Expand `TimeBasedMoveCostCalculator` to account for turn costs, acceleration limits, and congestion penalties.
- Add an A* (or faster) path planner and benchmark against the existing Dijkstra implementation.
- Build end-to-end tests that load real layouts, run representative pick tasks, and assert both path feasibility and latency budgets.
- git LFS for demo files
