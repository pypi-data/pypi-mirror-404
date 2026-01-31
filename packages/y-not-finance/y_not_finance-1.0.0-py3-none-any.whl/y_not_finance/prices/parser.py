"""
Data parsing logic for Yahoo Finance API responses.
"""

import logging
import pandas as pd
from typing import Dict, Any, Optional, Union, List

from .constants import SUPPORTED_FIELDS

logger = logging.getLogger(__name__)


def extract_prices(
    data: Dict[str, Any],
    interval: str,
    fields: Optional[Union[str, List[str]]] = None
) -> pd.DataFrame:
    """
    Extract price data from Yahoo Finance API response.
    
    Args:
        data: Raw JSON response from API
        interval: Data interval used
        fields: Field(s) to extract
        
    Returns:
        DataFrame with timestamp index and requested fields
    """
    try:
        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        indicators = result['indicators']['quote'][0]
        
        # Get adjclose if available
        adjclose_data = (
            result['indicators']['adjclose'][0]['adjclose']
            if 'adjclose' in result['indicators'] and result['indicators']['adjclose']
            else None
        )
        
        # Normalize fields to list
        if isinstance(fields, str):
            fields = [fields]
        
        # Default to adjclose or close
        if fields is None:
            fields = ['adjclose'] if adjclose_data is not None else ['close']
        
        # Validate fields
        invalid_fields = set(fields) - SUPPORTED_FIELDS
        if invalid_fields:
            logger.warning(f"Ignoring invalid fields: {invalid_fields}")
            fields = [f for f in fields if f in SUPPORTED_FIELDS]

        # Build data dictionary more efficiently
        data_dict = {'timestamp': timestamps}
        
        for field in fields:
            if field == 'adjclose':
                if adjclose_data is not None:
                    data_dict[field] = adjclose_data
            elif field in indicators:
                data_dict[field] = indicators[field]

        df = pd.DataFrame(data_dict)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)
        df.index.name = None
        
        return df

    except (KeyError, IndexError) as e:
        logger.error(f"Error extracting prices: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error during extraction: {e}")
        return pd.DataFrame()
