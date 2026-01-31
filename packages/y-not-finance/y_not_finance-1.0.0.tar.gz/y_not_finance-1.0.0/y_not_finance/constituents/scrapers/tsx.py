"""TSX Scraper - Fetch TSX stock tickers from Globe and Mail."""

import logging
from typing import Dict

import requests

logger = logging.getLogger(__name__)

# Constants
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0'
}
REQUEST_TIMEOUT = 10
BASE_URL = "https://globeandmail.pl.barchart.com/module/dataTable.json"
INITIAL_PAGE_URL = "https://www.theglobeandmail.com/investing/markets/indices/TXCX/components/"
BENCHMARK_TICKER = "^GSPTSE"
BENCHMARK_NAME = "TSX Composite Index"
BENCHMARK_DESCRIPTION = "The S&P/TSX Composite Index is the primary stock market index of Canada, representing the performance of large-cap Canadian companies across various sectors."
PAGE_LIMIT = 100


def scrape_tsx(include_benchmark: bool = False) -> tuple[Dict[str, str], str]:
    """Scrape TSX stock tickers from Globe and Mail.
    
    Args:
        include_benchmark: If True, include the TSX Composite Index benchmark
        
    Returns:
        Tuple of (dictionary mapping ticker symbols to company names, description string)
    """
    result: Dict[str, str] = {}
    
    if include_benchmark:
        result[BENCHMARK_TICKER] = BENCHMARK_NAME
    
    json_payload = _build_request_payload()
    
    try:
        with requests.Session() as session:
            # Pre-load cookies by visiting the index page
            try:
                session.get(INITIAL_PAGE_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            except requests.RequestException:
                logger.debug("Could not pre-load cookies")
            
            # Fetch all pages
            result.update(_fetch_all_pages(session, json_payload.copy()))
            
    except requests.RequestException as e:
        logger.error(f"Network error fetching TSX data: {e}")
    
    return result, BENCHMARK_DESCRIPTION


def _build_request_payload() -> dict:
    """Build JSON payload for API request.
    
    Returns:
        Request payload dictionary
    """
    return {
        "fields": "ticker,tickerName,lastPrice,priceChange,percentChange,openPrice,highPrice,lowPrice,tradeTime,quickLink",
        "lists": "stocks.indices.components.ca.txcx",
        "limit": PAGE_LIMIT,
        "orderDir": "desc",
        "orderBy": "marketCap",
        "page": 1
    }


def _fetch_all_pages(session: requests.Session, json_payload: dict) -> Dict[str, str]:
    """Paginate through all TSX data.
    
    Args:
        session: Active requests Session
        json_payload: API request payload
        
    Returns:
        Dictionary of all ticker-name pairs
    """
    result: Dict[str, str] = {}
    page_count = 0
    
    while True:
        try:
            response = session.post(
                BASE_URL,
                headers=HEADERS,
                json=json_payload,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data_list = response.json().get("data", [])
            
        except (requests.RequestException, ValueError) as e:
            logger.error(f"Error fetching page {json_payload['page']}: {e}")
            break
        
        if not data_list:
            break
        
        # Extract ticker-name pairs from current page
        page_data = _extract_page_data(data_list)
        result.update(page_data)
        
        page_count += 1
        json_payload["page"] += 1
    
    return result


def _extract_page_data(data_list: list) -> Dict[str, str]:
    """Extract ticker and company name from API response.
    
    Args:
        data_list: List of data items from API
        
    Returns:
        Dictionary of ticker-name pairs from this page
    """
    result: Dict[str, str] = {}
    
    try:
        for item in data_list:
            raw_data = item.get("raw", {})
            symbol = raw_data.get("symbol")
            symbol_name = raw_data.get("symbolName")
            
            if symbol and symbol_name:
                result[symbol] = symbol_name
    except (KeyError, AttributeError, TypeError) as e:
        logger.warning(f"Error extracting data: {e}")
    
    return result
