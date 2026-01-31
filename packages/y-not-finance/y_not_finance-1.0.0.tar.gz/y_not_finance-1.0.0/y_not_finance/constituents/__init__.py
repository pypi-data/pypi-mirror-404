"""
Constituents module - Stock index constituent fetching.

This module provides functionality to fetch stock tickers and company names
from various stock market indexes including S&P 500, NASDAQ, TSX, etc.
"""

from .client import get_constituents
from .config import STOCK_LISTS

__all__ = ['get_constituents', 'STOCK_LISTS']
