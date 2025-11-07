import logging
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


@main(version_base=None, config_path="conf", config_name="demo")
def run_demo(cfg: DictConfig) -> None:
    """Run the demo workflow using Hydra-provided configuration."""

    # Load the json as WarehouseLayout object
    layout_loader = JsonWarehouseLayoutLoader(_resolve_json_path(cfg.layout.path))
    warehouse_layout = layout_loader.load()

    # Create the connectivity map; defer instantiation if config requests partial construction
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
    for _, task_row in df.iterrows():
        source_location = task_row[cfg.tasks.location_column]
        reserve_locations = task_row[cfg.tasks.reserve_column].strip().split(",")
        target = reserve_locations[0]  # Just look at first reserve for now
        path, cost = path_finder.compute_optimal_path(source_location, target)
        logging.info(
            {"task": source_location, "target": target, "cost": cost, "path": path}
        )


if __name__ == "__main__":
    run_demo()
