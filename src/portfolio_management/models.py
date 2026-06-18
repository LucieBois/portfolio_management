from typing import Annotated

from pydantic import BaseModel, StringConstraints, field_validator

type CleanStr = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True)]


class AssetModel(BaseModel):
    name: str
    isin: str
    esg: bool
    defense: float
    oil: float
    distributive: bool

    @field_validator("defense", "oil", mode="before")
    def validate_percentage(cls, value: float) -> float:
        if not (0 <= value <= 1):
            raise ValueError("Value must be between 0 and 100")
        return value
