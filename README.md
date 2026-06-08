# portfolio-management

This package depends on >= 3.14. This is a private repository, that aims at creating an optimal ETF portfolio for the user.

## What it does

Here are the **SHORT-TERM** features that will be implemented:

1. Retrieve financial data for a provided list of asset
  - The list of assets should updatable using a CLI
  - The data provider will likely be Yahoo finance
2. Use mean-variance analysis to create an optimal portfolio
  - Provide stats regarding past max variations within a year
  - Provide expected return, variance, etc.
3. Use factor analysis to determine optimal portfolio
  - First, FF 3 factors, then offer the possibility to retrieve other factors (don't know how yet)
