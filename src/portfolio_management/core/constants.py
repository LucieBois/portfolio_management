from portfolio_management.models import AssetModel

BASE_ASSETS: list[AssetModel] = [
    AssetModel(
        name="Amundi MSCI Europe ESG Leaders UCITS ETF",
        isin="LU1940199711",
        esg=True,
        defense=0.0,
        oil=0.0,
    ),
    AssetModel(
        name="Amundi Index MSCI Emerging Markets SRI",
        isin="LU1861138961",
        esg=True,
        defense=0.0,
        oil=0.0,
    ),
    AssetModel(
        name=" Amundi Core EURO STOXX 50 UCITS ETF EUR Acc",
        isin="LU1681047236",
        esg=False,
        defense=0.0,
        oil=0.0492,
    ),
    AssetModel(
        name="AMUNDI PHYSICAL GOLD ETC",
        isin="FR0013416716",
        esg=False,
        defense=0.0,
        oil=0.0,
    ),
]
