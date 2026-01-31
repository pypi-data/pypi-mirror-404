"""
Y-Not-Finance: A comprehensive Python library for financial data.

This package provides two main modules:
1. prices - Fetch historical and intraday price data from Yahoo Finance
2. constituents - Fetch stock index constituents from various sources

Examples:
    >>> from y_not_finance import YahooFinanceClient, get_constituents
    >>> 
    >>> # Fetch price data
    >>> client = YahooFinanceClient()
    >>> prices = client.get_prices(["AAPL", "MSFT"], range_str="1mo")
    >>> 
    >>> # Get index constituents
    >>> tickers, description = get_constituents("^SPX", info=True)
"""

__version__ = "1.0.0"

# Import main classes and functions for convenience
from .prices import YahooFinanceClient
from .constituents import get_constituents, STOCK_LISTS

__all__ = [
    'YahooFinanceClient',
    'get_constituents',
    'STOCK_LISTS',
    '__version__',
]
