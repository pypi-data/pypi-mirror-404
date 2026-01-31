"""
Constants for Yahoo Finance API client.
"""

# Yahoo Finance API endpoint
BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

# Supported data fields
SUPPORTED_FIELDS = {'open', 'high', 'low', 'close', 'volume', 'adjclose'}

# Intraday interval configurations with maximum available ranges
SHORT_INTERVALS = {
    '1m': '8d',
    '2m': '60d',
    '5m': '60d',
    '15m': '60d',
    '30m': '60d',
    '60m': '730d',
    '90m': '60d',
    '1h': '730d',
}

# Daily+ interval configurations with maximum available ranges
LONG_INTERVALS = {
    '1d': '1000y',
    '5d': '1000y',
    '1wk': '1000y',
    '1mo': '1000y',
    '3mo': '1000y',
}

# Default API parameters
DEFAULT_PARAMS = {
    'formatted': 'true',
    'crumb': 'e0Jf2Yh0ipZ',
    'lang': 'en-US',
    'region': 'US',
    'events': 'capitalGain|div|split|earn',
    'includeAdjustedClose': 'true',
    'useYfid': 'true',
    'corsDomain': 'finance.yahoo.com'
}

# HTTP headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}
