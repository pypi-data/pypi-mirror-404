"""
Configuration for supported stock indexes and their data sources.
"""

from typing import Dict, Any

# Available stock lists configuration
STOCK_LISTS: Dict[str, Dict[str, Any]] = {
    "^GSPTSE": {
        "name": "S&P/TSX Composite Index",
        "url": "https://globeandmail.pl.barchart.com/module/dataTable",
        "source": "globeandmail",
    },
    "^DJI": {
        "name": "Dow Jones Industrial Average",
        "url": "https://stockanalysis.com/list/dow-jones-stocks/__data.json?",
        "source": "stockanalysis"
    },
    "^SPX": {
        "name": "S&P 500 Index",
        "url": "https://stockanalysis.com/list/sp-500-stocks/__data.json",
        "source": "stockanalysis"
    },
    "^IXIC": {
        "name": "NASDAQ Composite Index",
        "url": "https://stockanalysis.com/list/nasdaq-100-stocks/__data.json",
        "source": "stockanalysis"
    },
    "megacaps": {
        "name": "Mega Caps",
        "url": "https://stockanalysis.com/list/mega-cap-stocks/__data.json",
        "source": "stockanalysis"
    },
    "largecaps": {
        "name": "Large Caps",
        "url": "https://stockanalysis.com/list/large-cap-stocks/__data.json",
        "source": "stockanalysis"
    },
    "midcaps": {
        "name": "Mid Caps",
        "url": "https://stockanalysis.com/list/mid-cap-stocks/__data.json",
        "source": "stockanalysis"
    },
    "smallcaps": {
        "name": "Small Caps",
        "url": "https://stockanalysis.com/list/small-cap-stocks/__data.json",
        "source": "stockanalysis"
    },
    "microcaps": {
        "name": "Micro Caps",
        "url": "https://stockanalysis.com/list/micro-cap-stocks/__data.json",
        "source": "stockanalysis"
    },
    "nanocaps": {
        "name": "Nano Caps",
        "url": "https://stockanalysis.com/list/nano-cap-stocks/__data.json",
        "source": "stockanalysis"
    },
}
