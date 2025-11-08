from abc import ABC, abstractmethod
from collections import defaultdict
import json
from pathlib import Path

from pydantic import ValidationError


import logging

from dexory.models import (
    LocationsByFeatureType,
    LocationsStoreType,
    WarehouseLayoutModel,
    WarehouseLocationModel,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


class WarehouseLayoutLoader(ABC):
    """
    Abstract class for loading warehouse layout information. Could be in the form of
    a .JSON (as supplied in example), or some other format or data source.
    """

    @abstractmethod
    def load(self) -> WarehouseLayoutModel:
        """Parse raw layout data into structured dicts and models."""
        pass


class JsonWarehouseLayoutLoader(WarehouseLayoutLoader):
    """
    Implementation that loads from a JSON file as in demo.
    """

    def __init__(self, json_path: Path):
        super().__init__()
        self.json_path = json_path

    def load(self) -> WarehouseLayoutModel:
        """Load and parse the raw json data into structured internal format."""

        # Load JSON file
        with open(self.json_path, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise TypeError(
                f"Expected dict at root of {self.json_path}, got {type(data).__name__}"
            )

        # Parse data
        locations: LocationsStoreType = {}
        keys_by_rack_face: LocationsByFeatureType = defaultdict(list)
        keys_by_column: LocationsByFeatureType = defaultdict(list)
        for rack_face_area in data.get("rack_face_areas", []):
            logging.info(f"Parsing rack face area {rack_face_area['name']}")
            for location in rack_face_area.get("locations", []):
                try:
                    # Creates pydantic model directly from dicts
                    location_model = WarehouseLocationModel(
                        **{**rack_face_area, **location},
                        **{"rackface": rack_face_area["name"]},
                    )
                    if location_model.name in locations:
                        # Note: probably better ways to handle this
                        logging.warning(f"Duplicate location: {location_model.name}")
                        continue
                    # Store loaded location model
                    locations[location_model.name] = location_model
                    keys_by_rack_face[rack_face_area["name"]].append(
                        location_model.name
                    )
                    distinct_column_key = (
                        f"{rack_face_area['name']}_{location_model.column}"
                    )
                    keys_by_column[distinct_column_key].append(location_model.name)

                except ValidationError as e:
                    logging.warning(
                        f"Skipped invalid location {location.get('name')}: {e}"
                    )

        return WarehouseLayoutModel(
            locations=locations,
            keys_by_rack_face=keys_by_rack_face,
            keys_by_column=keys_by_column,
        )
