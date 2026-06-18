from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from portfolio_management.database.base import Base


class TimestampMixin:
    """Add created_at and updated_at columns to models automatically"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp for record creation",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp for record update",
    )


class AssetsORM(Base, TimestampMixin):
    __tablename__: str = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)

    isin: Mapped[str] = mapped_column(unique=True, nullable=False)

    name: Mapped[str] = mapped_column(nullable=False, comment="Name of the asset")

    esg: Mapped[bool] = mapped_column(
        nullable=False, default=False, comment="Whether the asset is labeled as ESG"
    )

    defense: Mapped[float] = mapped_column(
        nullable=False,
        default=0.0,
        comment="Percentage of the asset's investment made in defense activities",
    )

    oil: Mapped[float] = mapped_column(
        nullable=False,
        default=0.0,
        comment="Percentage of the asset's investment made in oil activities",
    )

    distributive: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        comment="Whether the asset distributes dividends or not",
    )


class ExchangesORM(Base, TimestampMixin):
    __tablename__: str = "exchanges"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        unique=True, nullable=False, comment="Name of the exchange"
    )

    code: Mapped[str] = mapped_column(
        unique=True, nullable=False, comment="Code of the exchange"
    )

    operating_mic: Mapped[str] = mapped_column(
        unique=True, nullable=False, comment="Operating MIC of the exchange"
    )

    country: Mapped[str] = mapped_column(
        nullable=False, comment="Country of the exchange"
    )

    currency: Mapped[str] = mapped_column(
        nullable=False, comment="Currency of the exchange"
    )

    country_iso2: Mapped[str] = mapped_column(
        nullable=False, comment="ISO2 code of the country of the exchange"
    )

    country_iso3: Mapped[str] = mapped_column(
        nullable=False, comment="ISO3 code of the country of the exchange"
    )
