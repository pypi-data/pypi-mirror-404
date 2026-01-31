"""
Main API for fetching stock index constituents.
"""

import logging
import pprint
from typing import Dict

from .config import STOCK_LISTS
from .scrapers import scrape_stock_analysis, scrape_tsx
from .utils import validate_list_name

logger = logging.getLogger(__name__)


def get_constituents(
    list_name: str,
    include_benchmark: bool = False,
    info: bool = False,
    preview: bool = False,
    description: bool = False,
) -> tuple[Dict[str, str], str]:
    """
    Fetch stock tickers and company names from specified index.
    
    Args:
        list_name: Key identifying which stock list to scrape
                  Available: ^GSPTSE, ^DJI, ^SPX, ^IXIC, megacaps, largecaps,
                            midcaps, smallcaps, microcaps, nanocaps
        include_benchmark: If True, include benchmark index in results
        info: If True, log summary information
        preview: If True, log preview of results
        description: If True, log the description of the list
        
    Returns:
        Tuple of (dictionary mapping ticker symbols to company names, description string)
        
    Examples:
        >>> from y_not_finance.constituents import get_constituents
        >>> 
        >>> # Get S&P 500 constituents
        >>> tickers, desc = get_constituents("^SPX", info=True)
        >>> 
        >>> # Get TSX constituents with benchmark
        >>> tickers, desc = get_constituents("^GSPTSE", include_benchmark=True)
    """
    if not validate_list_name(list_name, STOCK_LISTS):
        return {}, ""
    
    config = STOCK_LISTS[list_name]
    source = config.get("source")
    result: Dict[str, str] = {}
    desc: str = ""
    
    try:
        if source == "globeandmail":
            result, desc = scrape_tsx(include_benchmark=include_benchmark)
        elif source == "stockanalysis":
            url = config.get("url", "")
            result, desc = scrape_stock_analysis(
                url=url,
                list_name=list_name,
                list_display_name=config["name"],
                include_benchmark=include_benchmark
            )
        else:
            logger.error(f"Unknown source: {source}")
            return {}, ""
        
        if info:
            logger.info(f"Fetched {len(result)} tickers for '{list_name}' - {config['name']}")
        
        if description:
            logger.info(f"Description: {desc}")
        
        if preview:
            logger.info(f"Preview:\n{pprint.pformat(result)}")
        
        return result, desc
        
    except Exception as e:
        logger.error(f"Error fetching {list_name}: {e}")
        return {}, ""
