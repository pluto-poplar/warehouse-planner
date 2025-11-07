import logging
import math
from pathlib import Path

import pandas as pd
from hydra import main
from hydra.utils import instantiate, to_absolute_path
from omegaconf import DictConfig

from dexory.warehouse_layout import JsonWarehouseLayoutLoader


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def _resolve_json_path(path_str: str) -> Path:
    """Return an absolute Path for a Hydra-configured location."""
    return Path(to_absolute_path(path_str))


def _parse_locations(raw_value: object) -> list[str]:
    """Convert comma-separated string(s) into a deduplicated list of locations."""
    if raw_value is None:
        return []
    if isinstance(raw_value, float) and math.isnan(raw_value):
        return []
    if not isinstance(raw_value, str):
        return []
    return [loc.strip() for loc in raw_value.split(",") if loc.strip()]


@main(version_base=None, config_path="conf", config_name="demo")
def run_demo(cfg: DictConfig) -> None:
    """Run the demo workflow using Hydra-provided configuration."""

    # Load the json as WarehouseLayout object
    layout_loader = JsonWarehouseLayoutLoader(_resolve_json_path(cfg.layout.path))
    warehouse_layout = layout_loader.load()

    # Create the connectivity map (Hydra instantiates a factory because of _partial_=true)
    connectivity_map_factory = instantiate(cfg.connectivity_map)
    connectivity_map = connectivity_map_factory(layout=warehouse_layout)

    # Create the move cost calculator
    move_cost_calculator = instantiate(cfg.move_cost)
    connectivity_map.set_move_cost_calculator(move_cost_calculator)

    # Create the path finder
    path_finder = instantiate(cfg.pathfinder, connectivity_map=connectivity_map)

    # Iterate over tasks
    tasks_path = _resolve_json_path(cfg.tasks.csv_path)
    df = pd.read_csv(tasks_path)
    max_tasks_cfg = cfg.tasks.get("max_tasks")
    max_tasks = int(max_tasks_cfg) if max_tasks_cfg is not None else None

    # Prepare output location
    output_dir = _resolve_json_path(cfg.tasks.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "tasks_solution.csv"

    results: list[dict[str, object]] = []

    for idx, (_, task_row) in enumerate(df.iterrows()):
        if max_tasks is not None and idx >= max_tasks:
            break
        source_location = task_row[cfg.tasks.location_column]
        reserve_locations = _parse_locations(task_row.get(cfg.tasks.reserve_column))

        nearby_column = cfg.tasks.nearby_empty_column
        nearby_locations = []
        if nearby_column is not None and nearby_column in task_row.index:
            nearby_locations = _parse_locations(task_row.get(nearby_column))

        candidate_locations: list[str] = []
        for loc in reserve_locations + nearby_locations:
            if loc not in candidate_locations:
                candidate_locations.append(loc)

        if not candidate_locations:
            logging.warning(
                "No candidate destinations for %s (row %s)", source_location, idx
            )
            record = {
                "task_location": source_location,
                "target_empty_location": "",
                "static_travel_cost_seconds": float("inf"),
            }
            results.append(record)
            continue

        best_target: str | None = None
        best_cost = float("inf")
        for candidate in candidate_locations:
            path, cost = path_finder.compute_optimal_path(source_location, candidate)
            if cost < best_cost:
                best_cost = cost
                best_target = candidate

        record = {
            "task_location": source_location,
            "target_empty_location": best_target or "",
            "static_travel_cost_seconds": best_cost,
        }
        logging.info(record)
        results.append(record)

    pd.DataFrame(results).to_csv(output_file, index=False)
    scope = f"first {max_tasks}" if max_tasks is not None else "all"
    logging.info(
        "Saved %s task solutions (%s tasks) to %s", len(results), scope, output_file
    )


if __name__ == "__main__":
    run_demo()
