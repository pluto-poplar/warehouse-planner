import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from dexory.models import WarehouseLocationModel
from dexory.warehouse_layout import JsonWarehouseLayoutLoader, WarehouseLayout


def test_json_loader_parses_valid_file(sample_json: Path):
    """Ensure a valid JSON file is parsed into a proper WarehouseLayout object."""
    loader = JsonWarehouseLayoutLoader(sample_json)
    layout = loader.load()

    assert isinstance(layout, WarehouseLayout)
    assert len(layout.locations) == 2
    assert "A11-120-00" in layout.locations
    assert "A11 2" in layout.keys_by_rack_face

    loc = layout.locations["A11-120-00"]
    assert isinstance(loc, WarehouseLocationModel)
    assert loc.front == "POSITIVE_X"
    assert loc.column == 0
    assert loc.shelf == 0

    # Check rack face grouping
    assert set(layout.keys_by_rack_face["A11 2"]) == {"A11-120-00", "A11-120-10"}


def test_invalid_root_type_raises(tmp_path: Path):
    """Raise TypeError when root of JSON is not a dict."""
    bad_path = tmp_path / "invalid.json"
    with open(bad_path, "w") as f:
        json.dump(["this", "is", "a", "list"], f)

    loader = JsonWarehouseLayoutLoader(bad_path)
    with pytest.raises(TypeError):
        loader.load()


def test_invalid_location_is_skipped(tmp_path: Path):
    """Invalid locations should be skipped gracefully."""
    bad_data = {
        "rack_face_areas": [
            {
                "id": "face-2",
                "name": "Broken Face",
                "locations": [
                    {"name": "Incomplete"},  # missing required fields
                ],
            }
        ]
    }
    bad_path = tmp_path / "bad.json"
    with open(bad_path, "w") as f:
        json.dump(bad_data, f)

    loader = JsonWarehouseLayoutLoader(bad_path)
    layout = loader.load()

    assert len(layout.locations) == 0
    assert layout.keys_by_rack_face == {}


def test_duplicate_locations_are_skipped(tmp_path: Path):
    """Duplicate location entries should be logged and skipped."""
    dup_data = {
        "rack_face_areas": [
            {
                "id": "face-3",
                "name": "Dup Face",
                "locations": [
                    {
                        "id": "loc-1",
                        "name": "A11-200-00",
                        "type": "rack",
                        "front": "POSITIVE_X",
                        "column": 0,
                        "shelf": 0,
                        "bounds": {
                            "min": {"x": 0, "y": 0, "z": 0},
                            "max": {"x": 1, "y": 1, "z": 1},
                        },
                    },
                    {
                        "id": "loc-2",
                        "name": "A11-200-00",  # duplicate name
                        "type": "rack",
                        "front": "POSITIVE_X",
                        "column": 1,
                        "shelf": 0,
                        "bounds": {
                            "min": {"x": 1, "y": 0, "z": 0},
                            "max": {"x": 2, "y": 1, "z": 1},
                        },
                    },
                ],
            }
        ]
    }
    dup_path = tmp_path / "dup.json"
    with open(dup_path, "w") as f:
        json.dump(dup_data, f)

    loader = JsonWarehouseLayoutLoader(dup_path)
    layout = loader.load()

    # Should keep only one of the duplicates
    assert len(layout.locations) == 1
    assert "A11-200-00" in layout.locations
    assert len(layout.keys_by_rack_face["Dup Face"]) == 1
