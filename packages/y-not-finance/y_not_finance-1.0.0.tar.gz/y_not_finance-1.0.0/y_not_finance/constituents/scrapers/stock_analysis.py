"""Stock Analysis Scraper - Fetch stock tickers from stockanalysis.com."""

import logging
from typing import Dict

import requests

logger = logging.getLogger(__name__)

# Constants
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0'
}
REQUEST_TIMEOUT = 10
STOCK_DATA_NODE_INDEX = 2


def _extract_description(data: list) -> str:
    """Extract description text from data with fallback options.
    
    Args:
        data: Parsed JSON data list containing description field
        
    Returns:
        Description text, or empty string if not found
    """
    try:
        description_index = data[1].get('meta_description') or data[1].get('page_description')
        if description_index is not None:
            return data[description_index]
        return ''
    except (KeyError, IndexError, TypeError):
        return ''


def scrape_stock_analysis(
    url: str,
    list_name: str,
    list_display_name: str,
    include_benchmark: bool = False
) -> tuple[Dict[str, str], str]:
    """Scrape stock tickers from stockanalysis.com API.
    
    Args:
        url: API endpoint URL
        list_name: Internal identifier for the list
        list_display_name: Display name for logging
        include_benchmark: If True, include benchmark index
        
    Returns:
        Tuple of (dictionary mapping ticker symbols to company names, description string)
    """
    result: Dict[str, str] = {}
    description: str = ""
    
    if include_benchmark:
        result[list_name] = list_display_name
    
    try:
        with requests.Session() as session:
            response = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            raw_data = response.json()
            data = raw_data["nodes"][STOCK_DATA_NODE_INDEX]["data"]
            stock_data_index = data[0]['stockData']
            
            # Extract description
            description = _extract_description(data)

            # Extract ticker and company name pairs
            for i in data[stock_data_index]:
                ticker = data[i + 2]
                full_name = data[i + 3]
                
                # Normalize ticker format (replace dots with dashes)
                normalized_ticker = ticker.replace(".", "-")
                result[normalized_ticker] = full_name
            
    except requests.RequestException as e:
        logger.error(f"Network error fetching {list_display_name}: {e}")
    except (KeyError, IndexError, ValueError, requests.JSONDecodeError) as e:
        logger.error(f"Parse error from {list_display_name}: {e}")
    
    return result, description
