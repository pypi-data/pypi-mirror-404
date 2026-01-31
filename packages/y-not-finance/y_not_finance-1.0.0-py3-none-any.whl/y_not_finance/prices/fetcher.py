"""
HTTP fetching logic for Yahoo Finance API.
"""

import logging
import random
import requests
from time import sleep
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor
from requests.exceptions import HTTPError, RequestException

from .constants import BASE_URL, DEFAULT_PARAMS, HEADERS

logger = logging.getLogger(__name__)


class YahooFinanceFetcher:
    """
    Handles HTTP requests to Yahoo Finance API with retry logic and rate limiting.
    """
    
    def __init__(
        self,
        max_workers: int = 10,
        rate_limit_delay: float = 0.1,
        timeout: int = 10,
        max_retries: int = 5
    ):
        """
        Initialize the fetcher.
        
        Args:
            max_workers: Maximum number of concurrent API requests
            rate_limit_delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.max_workers = max_workers
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.max_retries = max_retries
    
    def fetch_raw_json(
        self,
        ticker: str,
        max_range_str: str,
        interval: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch raw JSON data from Yahoo Finance API with retry logic.
        
        Args:
            ticker: Stock ticker symbol
            max_range_str: Maximum date range to fetch
            interval: Data interval (e.g., '1d', '1h')
            
        Returns:
            JSON response as dictionary, or None if request fails
        """
        backoff = self.rate_limit_delay
        
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(
                    BASE_URL.format(ticker=ticker),
                    params={**DEFAULT_PARAMS, 'range': max_range_str, 'interval': interval},
                    timeout=self.timeout
                )
                resp.raise_for_status()
                return resp.json()
                
            except HTTPError as e:
                status = e.response.status_code if hasattr(e, 'response') else None
                
                if status in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    wait = backoff * (2 ** (attempt - 1)) + random.uniform(0, 0.1)
                    logger.warning(
                        f"{ticker} [HTTP {status}] - Retrying in {wait:.2f}s "
                        f"(attempt {attempt}/{self.max_retries})"
                    )
                    sleep(wait)
                    continue
                    
                logger.error(f"HTTP error fetching {ticker}: {e}")
                return None
                
            except RequestException as e:
                logger.error(f"Request error for {ticker}: {e}")
                return None
                
            except Exception as e:
                logger.error(f"Unexpected error for {ticker}: {e}")
                return None
                
            finally:
                sleep(self.rate_limit_delay)
                
        logger.error(f"Max retries exceeded for {ticker}")
        return None
    
    def fetch_concurrent(
        self,
        tickers: List[str],
        max_range_str: str,
        interval: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch data for multiple tickers concurrently.
        
        Args:
            tickers: List of ticker symbols
            max_range_str: Maximum date range
            interval: Data interval
            
        Returns:
            Dictionary mapping ticker to raw JSON response
        """
        raw_json_data = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ticker = {
                executor.submit(self.fetch_raw_json, ticker, max_range_str, interval): ticker
                for ticker in tickers
            }
            
            for future in future_to_ticker:
                ticker = future_to_ticker[future]
                try:
                    raw_json = future.result()
                    if raw_json:
                        raw_json_data[ticker] = raw_json
                except Exception as e:
                    logger.error(f"Error fetching {ticker}: {e}")
        
        return raw_json_data
