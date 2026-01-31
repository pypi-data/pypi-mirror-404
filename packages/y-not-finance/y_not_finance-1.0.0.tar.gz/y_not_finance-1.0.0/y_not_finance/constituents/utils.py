"""Utilities for stock scraper modules."""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


def validate_list_name(list_name: str, available_lists: Dict[str, dict]) -> bool:
    """Validate if a list name is available.
    
    Args:
        list_name: Name to validate
        available_lists: Dictionary of available lists
        
    Returns:
        True if valid, False otherwise
    """
    if list_name not in available_lists:
        available = ', '.join(available_lists.keys())
        logger.error(f"Invalid list: {list_name}. Available: {available}")
        return False
    return True
