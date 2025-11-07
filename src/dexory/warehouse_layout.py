from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path

from pydantic import ValidationError


import logging

from dexory.models import WarehouseLocationModel

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


LocationsStoreType = dict[str, WarehouseLocationModel]
LocationsByRackFaceType = dict[str, list[str]]


@dataclass
class WarehouseLayout:
    """Dataclass for storing warehouse layout."""

    locations: LocationsStoreType
    keys_by_rack_face: LocationsByRackFaceType

    def get_location(self, name: str) -> WarehouseLocationModel:
        """Get location by name."""
        return self.locations[name]


class WarehouseLayoutLoader(ABC):
    """
    Abstract class for loading warehouse layout information. Could be in the form of
    a .JSON (as supplied in example), or some other format or data source.
    """

    @abstractmethod
    def load(self) -> WarehouseLayout:
        """Parse raw layout data into structured dicts and models."""
        pass


class JsonWarehouseLayoutLoader(WarehouseLayoutLoader):
    """
    Implementation that loads from a JSON file as in demo.
    """

    def __init__(self, json_path: Path):
        super().__init__()
        self.json_path = json_path

    def load(self) -> WarehouseLayout:
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
        keys_by_rack_face: LocationsByRackFaceType = defaultdict(list)
        for rack_face_area in data.get("rack_face_areas", []):
            logging.info(f"Parsing rack face area {rack_face_area.get('name')}")
            for location in rack_face_area.get("locations", []):
                try:
                    # Creates pydantic model directly from dicts
                    location_model = WarehouseLocationModel(
                        **{**rack_face_area, **location}
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

                except ValidationError as e:
                    logging.warning(
                        f"Skipped invalid location {location.get('name')}: {e}"
                    )

        return WarehouseLayout(locations=locations, keys_by_rack_face=keys_by_rack_face)
