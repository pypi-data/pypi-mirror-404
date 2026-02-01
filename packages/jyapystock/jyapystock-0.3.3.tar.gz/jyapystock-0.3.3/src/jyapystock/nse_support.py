"""
NSE (National Stock Exchange of India) support for jyapystock.
Provides helper functions to fetch live and historical prices for Indian stocks.
"""

from nse import NSE
import logging
import tempfile
from typing import Optional, Union
from datetime import datetime
from dateutil.parser import parse


# Global NSE instance
_nse_instance = None


def _get_nse_instance():
    """Get or create a singleton NSE instance."""
    global _nse_instance
    if _nse_instance is None:
        temp_dir = tempfile.mkdtemp()
        _nse_instance = NSE(download_folder=temp_dir)
    return _nse_instance


def get_nse_live_price(symbol: str) -> Optional[dict]:
    """
    Fetch live quote for an Indian stock using NSE API.
    
    Returns a dict with 'timestamp', 'price', and 'change_percent', or None if not available.
    """
    try:
        nse = _get_nse_instance()
        # equityQuote returns simple data, quote returns detailed data
        result = nse.quote(symbol)
        
        if not result or 'priceInfo' not in result:
            return None
        
        price_info = result['priceInfo']
        last_price = price_info.get('lastPrice')
        change = price_info.get('change', 0)
        p_change = price_info.get('pChange', 0)  # percentage change
        
        metadata = result.get('metadata', {})
        timestamp = metadata.get('lastUpdateTime', '')
        
        if last_price is None:
            return None
        
        return {
            "timestamp": timestamp,
            "price": last_price,
            "change_percent": round(p_change, 2)
        }
    except Exception:
        return None


def get_nse_historical_prices(symbol: str, start: Union[str, datetime], end: Union[str, datetime]) -> Optional[list]:
    """
    Fetch historical prices for an Indian stock from NSE.
    
    `start` and `end` may be strings (ISO like '2023-01-01') or datetime objects.
    Returns a list of records with date/open/high/low/close/volume, or None if not available.
    """
    try:
        # Normalize start/end to date strings
        if isinstance(start, str):
            start_dt = parse(start).date()
        elif isinstance(start, datetime):
            start_dt = start.date()
        else:
            start_dt = start

        if isinstance(end, str):
            end_dt = parse(end).date()
        elif isinstance(end, datetime):
            end_dt = end.date()
        else:
            end_dt = end
        
        nse = _get_nse_instance()
        # fetch_equity_historical_data returns historical data
        data = nse.fetch_equity_historical_data(symbol, from_date=start_dt, to_date=end_dt)
        
        if not data or isinstance(data, str):
            # Data might be an error string or None
            return None
        
        # NSE returns a DataFrame or dict; normalize to list of dicts
        records = []
        if hasattr(data, 'to_dict'):
            # It's a pandas DataFrame
            for idx, row in data.iterrows():
                records.append({
                    'date': change_date_format(str(row.get('mtimestamp', idx))),
                    'open': row.get('chOpeningPrice'),
                    'high': row.get('chTradeHighPrice'),
                    'low': row.get('chTradeLowPrice'),
                    'close': row.get('chClosingPrice'),
                    'volume': row.get('chTotTradedVal')
                })
        elif isinstance(data, dict):
            # Already a dict
            records = [
                {
                    'date': change_date_format(item['mtimestamp']),
                    'close': item['chClosingPrice'],
                    'open': item['chOpeningPrice'],
                    'high': item['chTradeHighPrice'],
                    'low': item['chTradeLowPrice'],
                    'volume': item['chTotTradedVal']
                } 
                for item in data
            ]
        else:
            # List of records
            records = [
                {
                    'date': change_date_format(item['mtimestamp']),
                    'close': item['chClosingPrice'],
                    'open': item['chOpeningPrice'],
                    'high': item['chTradeHighPrice'],
                    'low': item['chTradeLowPrice'],
                    'volume': item['chTotTradedVal']
                } 
                for item in data
            ]
        
        return records if records else None
    except Exception as e:
        logging.error(f"Error fetching historical prices for {symbol} from NSE: {str(e)}")
        return None

def change_date_format(date_str: str) -> str:
    """Convert date to 'yyyy-mm-dd' format."""
    try:
        dt = parse(date_str).date()
        return dt.strftime("%Y-%m-%d")
    except Exception as e:
        logging.error(f"Error converting date format: {str(e)}")
        return date_str  # Return original if conversion fails
