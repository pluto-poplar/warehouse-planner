import pytest


import json
from pathlib import Path

from dexory.models import BoundsModel, Coord3DModel, WarehouseLocationModel


@pytest.fixture
def sample_json(tmp_path: Path) -> Path:
    """Fixture that writes a sample warehouse layout JSON to disk."""
    data = {
        "rack_face_areas": [
            {
                "id": "face-1",
                "name": "A11 2",
                "locations": [
                    {
                        "id": "loc-001",
                        "name": "A11-120-00",
                        "type": "rack",
                        "front": "POSITIVE_X",
                        "column": 0,
                        "shelf": 0,
                        "bounds": {
                            "min": {"x": 369.9, "y": 125.35, "z": 0.05},
                            "max": {"x": 371.9, "y": 126.075, "z": 1.25},
                        },
                    },
                    {
                        "id": "loc-002",
                        "name": "A11-120-10",
                        "type": "rack",
                        "front": "POSITIVE_X",
                        "column": 0,
                        "shelf": 1,
                        "bounds": {
                            "min": {"x": 369.9, "y": 125.35, "z": 1.7},
                            "max": {"x": 371.9, "y": 126.075, "z": 2.8},
                        },
                    },
                ],
            }
        ]
    }
    json_path = tmp_path / "warehouse.json"
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
    return json_path



@pytest.fixture
def loc_a() -> WarehouseLocationModel:
    """Warehouse location at origin."""
    bounds = BoundsModel(
        min=Coord3DModel(x=0.0, y=0.0, z=0.0),
        max=Coord3DModel(x=1.0, y=1.0, z=1.0),
    )
    return WarehouseLocationModel(
        id="A",
        name="A",
        type="rack",
        front="POSITIVE_X",
        column=0,
        shelf=0,
        bounds=bounds,
    )


@pytest.fixture
def loc_b() -> WarehouseLocationModel:
    """Warehouse location displaced in space."""
    bounds = BoundsModel(
        min=Coord3DModel(x=2.0, y=3.0, z=4.0),
        max=Coord3DModel(x=3.0, y=4.0, z=5.0),
    )
    return WarehouseLocationModel(
        id="B",
        name="B",
        type="rack",
        front="POSITIVE_X",
        column=1,
        shelf=0,
        bounds=bounds,
    )

