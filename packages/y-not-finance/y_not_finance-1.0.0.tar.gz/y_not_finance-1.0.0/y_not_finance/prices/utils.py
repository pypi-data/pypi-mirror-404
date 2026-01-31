"""
Utility functions for price data processing.
"""

import re
import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def parse_range_str(range_str: str) -> pd.Timedelta:
    """
    Parse range string into pandas Timedelta.
    
    Supported formats: '1m', '1h', '1d', '1wk', '1mo', '1y'
    
    Args:
        range_str: Time range string (e.g., '3mo', '50y', '1h')
        
    Returns:
        Pandas Timedelta object
        
    Raises:
        ValueError: If range format is invalid
    """
    match = re.match(r'^(\d+)(m|h|d|wk|mo|y)$', range_str)
    if not match:
        raise ValueError(
            f"Invalid range format: '{range_str}'. "
            f"Expected format: <number><unit> (e.g., '1d', '3mo', '5y')"
        )
    
    value, unit = match.groups()
    value = int(value)
    
    unit_mapping = {
        'm': lambda v: pd.Timedelta(minutes=v),
        'h': lambda v: pd.Timedelta(hours=v),
        'd': lambda v: pd.Timedelta(days=v),
        'wk': lambda v: pd.Timedelta(weeks=v),
        'mo': lambda v: pd.Timedelta(days=v * 30),  # Approximation
        'y': lambda v: pd.Timedelta(days=v * 365),  # Approximation
    }
    
    return unit_mapping[unit](value)


def apply_range_filter(df: pd.DataFrame, range_str: str) -> pd.DataFrame:
    """
    Filter DataFrame to specified time range.
    
    Args:
        df: DataFrame to filter
        range_str: Range string (e.g., '1mo', '5y')
        
    Returns:
        Filtered DataFrame
    """
    try:
        delta = parse_range_str(range_str)
        cutoff_time = pd.Timestamp.now(tz='UTC') - delta
        
        # Handle timezone-naive index
        if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is None:
            cutoff_time = cutoff_time.tz_localize(None)
            
        return df[df.index >= cutoff_time]
        
    except ValueError as e:
        logger.error(f"Error parsing range_str '{range_str}': {e}")
        return df


def format_as_daily(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert intraday data to daily format (YYYY-MM-DD).
    
    For each date, keeps only the last available value.
    
    Args:
        df: DataFrame with datetime index
        
    Returns:
        DataFrame with date index
    """
    df.index = pd.to_datetime(df.index).date
    df = df.groupby(level=0).last()
    return df
