from pydantic import BaseModel, Field


from typing import Any


class Coord3DModel(BaseModel):
    """Coordinate of a 3D point."""

    x: float
    y: float
    z: float


class BoundsModel(BaseModel):
    """Defines min/max bounds for a warehouse location."""

    min: Coord3DModel
    max: Coord3DModel


class WarehouseLocationModel(BaseModel):
    """Model that stores location of a single discrete location in the warehouse."""

    rackface: str
    id: str
    name: str
    type: str
    front: str
    column: int
    shelf: int
    bounds: BoundsModel = Field(..., description="3D spatial bounds of the location")

    centroid: tuple[float, float, float] | None = Field(
        description="Centroid of the bounding box, computed post init.", default=None
    )

    access_point: tuple[float, float, float] | None = Field(
        description="Access point to location, given front.", default=None
    )

    def model_post_init(self, __context: dict[Any, Any]) -> None:
        """Compute the centroid automatically after validation."""
        self._compute_centroid()
        self._compute_access_point()

    def _compute_centroid(self) -> None:
        """Compute the centroid."""
        self.centroid = (
            (self.bounds.min.x + self.bounds.max.x) / 2.0,
            (self.bounds.min.y + self.bounds.max.y) / 2.0,
            (self.bounds.min.z + self.bounds.max.z) / 2.0,
        )

    def _compute_access_point(self) -> None:
        """Project centroid onto the face indicated by `front`."""
        if self.centroid is None:
            self._compute_centroid()
        cx, cy, cz = self.centroid  # type: ignore[misc]
        match self.front:
            case "POSITIVE_X":
                self.access_point = (self.bounds.max.x, cy, cz)
            case "NEGATIVE_X":
                self.access_point = (self.bounds.min.x, cy, cz)
            case "POSITIVE_Y":
                self.access_point = (cx, self.bounds.max.y, cz)
            case "NEGATIVE_Y":
                self.access_point = (cx, self.bounds.min.y, cz)
            case _:
                raise ValueError(f"Unsupported front direction: {self.front}")


LocationsStoreType = dict[str, WarehouseLocationModel]
LocationsByFeatureType = dict[str, list[str]]


class WarehouseLayoutModel(BaseModel):
    """Dataclass for storing warehouse layout."""

    locations: LocationsStoreType
    keys_by_rack_face: LocationsByFeatureType
    keys_by_column: LocationsByFeatureType

    def get_location(self, name: str) -> WarehouseLocationModel:
        """Get location by name."""
        return self.locations[name]
