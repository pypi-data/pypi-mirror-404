"""
DataFrame processing and formatting logic.
"""

import logging
import pandas as pd
from typing import Dict, Optional

from .constants import SHORT_INTERVALS
from .utils import apply_range_filter, format_as_daily

logger = logging.getLogger(__name__)


def process_dataframe(
    prices_dict: Dict[str, pd.DataFrame],
    interval: str,
    range_str: Optional[str]
) -> pd.DataFrame:
    """
    Process and format the final DataFrame.
    
    Args:
        prices_dict: Dictionary mapping ticker to price DataFrame
        interval: Data interval used
        range_str: Range filter to apply
        
    Returns:
        Processed DataFrame
    """
    # Concatenate all ticker data
    df_prices = pd.concat(prices_dict, axis=1, sort=False)
    
    # Apply range filter if specified
    if range_str:
        df_prices = apply_range_filter(df_prices, range_str)
    
    # Format dates for long intervals
    if interval not in SHORT_INTERVALS:
        df_prices = format_as_daily(df_prices)
    
    # Flatten column names for single field
    if isinstance(df_prices.columns, pd.MultiIndex) and df_prices.columns.nlevels == 2 and len(df_prices.columns.levels[1]) == 1:
        df_prices.columns = df_prices.columns.droplevel(1)
    
    return df_prices.sort_index().ffill()
