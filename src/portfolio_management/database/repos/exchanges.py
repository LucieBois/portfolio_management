from sqlalchemy import Engine, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from portfolio_management.database import ExchangesORM
from portfolio_management.models import ExchangeModel


class ExchangesRepository:
    def __init__(self, engine: Engine):
        self.engine: Engine = engine

    def get_all_exchanges(self) -> list[ExchangeModel]:
        with self.engine.connect() as connection:
            statement = select(
                ExchangesORM.code,
                ExchangesORM.name,
                ExchangesORM.country,
                ExchangesORM.currency,
                ExchangesORM.operating_mic,
                ExchangesORM.country_iso2,
                ExchangesORM.country_iso3,
            )

            data_rows = connection.execute(statement).mappings().all()

            structured_data: list[ExchangeModel] = []

            for row in data_rows:
                row_dict = dict(row)
                structured_row = ExchangeModel(**row_dict)  # pyright: ignore[reportAny]
                structured_data.append(structured_row)

            return structured_data

    def upsert_exchanges(self, exchanges: list[ExchangeModel]) -> None:
        with Session(self.engine) as session:
            stmt = insert(ExchangesORM).values(
                [exchange.model_dump() for exchange in exchanges]
            )

            stmt = stmt.on_conflict_do_update(
                index_elements=[ExchangesORM.code],
                set_={
                    "name": stmt.excluded.name,
                    "country": stmt.excluded.country,
                    "currency": stmt.excluded.currency,
                    "operating_mic": stmt.excluded.operating_mic,
                    "country_iso2": stmt.excluded.country_iso2,
                    "country_iso3": stmt.excluded.country_iso3,
                },
            )
            _ = session.execute(stmt)
            session.commit()
