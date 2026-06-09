from pydantic import BaseModel, field_validator


class AssetModel(BaseModel):
    name: str
    isin: str
    esg: bool
    defense: float
    oil: float

    @field_validator("defense", "oil", mode="before")
    def validate_percentage(cls, value: float) -> float:
        if not (0 <= value <= 1):
            raise ValueError("Value must be between 0 and 100")
        return value
