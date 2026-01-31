"""
Main client for fetching price data from Yahoo Finance.
"""

import logging
from typing import Union, List, Optional
import pandas as pd

from .constants import SHORT_INTERVALS, LONG_INTERVALS, SUPPORTED_FIELDS
from .fetcher import YahooFinanceFetcher
from .parser import extract_prices
from .processor import process_dataframe
from .utils import parse_range_str

logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """
    A client for fetching financial data from Yahoo Finance API.
    
    Features:
    - Multi-ticker concurrent fetching
    - Automatic retry with exponential backoff
    - Flexible date range filtering
    - Customizable field selection
    - Support for intraday and daily data
    """
    
    def __init__(
        self,
        max_workers: int = 10,
        rate_limit_delay: float = 0.1,
        timeout: int = 10,
        max_retries: int = 5
    ):
        """
        Initialize the Yahoo Finance API client.
        
        Args:
            max_workers: Maximum number of concurrent API requests
            rate_limit_delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.fetcher = YahooFinanceFetcher(
            max_workers=max_workers,
            rate_limit_delay=rate_limit_delay,
            timeout=timeout,
            max_retries=max_retries
        )
    
    def get_prices(
        self,
        tickers: Union[str, List[str]],
        range_str: Optional[str] = None,
        interval: str = "1d",
        fields: Optional[Union[str, List[str]]] = None
    ) -> pd.DataFrame:
        """
        Fetch price data for one or more tickers.
        
        This method fetches the maximum available data for the specified interval,
        then filters it based on the range_str parameter. Data is fetched concurrently
        for multiple tickers to optimize performance.
        
        Args:
            tickers: Single ticker string or list of ticker symbols
            range_str: Date range to filter (e.g., '1d', '5d', '1mo', '3mo', '50y').
                      If None, returns all available data.
            interval: Data interval - intraday: '1m', '5m', '15m', '30m', '1h'
                     or daily+: '1d', '5d', '1wk', '1mo', '3mo'
            fields: Field(s) to extract. Can be string or list.
                   Available: 'open', 'high', 'low', 'close', 'volume', 'adjclose'
                   Default: 'adjclose'
                   
        Returns:
            DataFrame with datetime index and price data. For single field and multiple
            tickers, columns are ticker names. For multiple fields, MultiIndex columns
            with (ticker, field) pairs.
            
        Examples:
            >>> client = YahooFinanceClient()
            >>> # Single ticker, single field
            >>> df = client.get_prices("AAPL", range_str="1mo", fields="close")
            >>> 
            >>> # Multiple tickers, single field
            >>> df = client.get_prices(["AAPL", "MSFT"], fields="adjclose")
            >>> 
            >>> # Multiple tickers, multiple fields
            >>> df = client.get_prices(["AAPL", "MSFT"], fields=["open", "close", "volume"])
        """
        # Normalize tickers to list
        if isinstance(tickers, str):
            tickers = [tickers]
        
        # Validate interval
        all_intervals = {**SHORT_INTERVALS, **LONG_INTERVALS}
        if interval not in all_intervals:
            logger.error(
                f"Unsupported interval: '{interval}'. "
                f"Supported: {list(all_intervals.keys())}"
            )
            return pd.DataFrame()

        # Get maximum range for interval
        max_range_str = all_intervals[interval]
        
        # Warn if requested range exceeds available range for this interval
        if range_str:
            try:
                requested_delta = parse_range_str(range_str)
                max_delta = parse_range_str(max_range_str)
                if requested_delta > max_delta:
                    logger.warning(
                        f"Requested range '{range_str}' exceeds maximum available for "
                        f"interval '{interval}' ({max_range_str}). "
                        f"Will return data for {max_range_str} instead."
                    )
            except ValueError:
                pass  # Invalid range_str will be handled later

        # Fetch data concurrently
        raw_json_data = self.fetcher.fetch_concurrent(tickers, max_range_str, interval)
        
        if not raw_json_data:
            logger.warning("No data fetched for any ticker")
            return pd.DataFrame()

        # Extract prices from raw data
        prices_dict = {}
        for ticker, raw_json in raw_json_data.items():
            try:
                prices = extract_prices(raw_json, interval, fields)
                if not prices.empty:
                    prices_dict[ticker] = prices
            except Exception as e:
                logger.error(f"Error processing data for {ticker}: {e}")

        if not prices_dict:
            logger.warning("No valid price data extracted")
            return pd.DataFrame()
        
        # Concatenate and process data
        df_prices = process_dataframe(prices_dict, interval, range_str)
        
        return df_prices
