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

    def model_post_init(self, __context: dict[Any, Any]) -> None:
        """Compute the centroid automatically after validation."""
        self.centroid = (
            (self.bounds.min.x + self.bounds.max.x) / 2.0,
            (self.bounds.min.y + self.bounds.max.y) / 2.0,
            (self.bounds.min.z + self.bounds.max.z) / 2.0,
        )
