from typing import Annotated, ClassVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

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


class ExchangeModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)

    name: CleanStr = Field(alias="Name")
    code: CleanStr = Field(alias="Code")
    operating_mic: CleanStr = Field(alias="OperatingMIC")
    country: CleanStr = Field(alias="Country")
    currency: CleanStr = Field(alias="Currency")
    country_iso2: CleanStr = Field(alias="CountryISO2")
    country_iso3: CleanStr = Field(alias="CountryISO3")
