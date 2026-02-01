"""
yfinance support for jyapystock
Provides helper functions to fetch live and historical prices using yfinance
and to try country-specific symbol variants (e.g., .NS/.BO for India).
"""

from datetime import datetime
from typing import Optional, Union
import yfinance as yf
from dateutil.parser import parse



def get_symbol_variants(symbol: str, country: str) -> list:
    """Generate possible symbol variants based on country conventions."""
    variants = [symbol]
    if country == "india":
        if "." not in symbol and "^" not in symbol: # Avoid adding suffixes to indices or already suffixed symbols
            variants = [f"{symbol}.NS", f"{symbol}.BO", symbol]
    elif country == "usa":
        if "." in symbol:
            variants = [symbol.replace(".", "-"), symbol]
    return variants

def get_yfinance_live_price(symbol: str, country: str) -> Optional[dict]:
    """Try live price with possible symbol variants for the given country.

    Returns a dict with 'timestamp', 'price', and 'change_percent' (% change from previous day close),
    or None if not available.
    """
    variants = get_symbol_variants(symbol, country)

    for s in variants:
        try:
            ticker = yf.Ticker(s)
            # Get last 2 days of data to compute % change
            data = ticker.history(period="2d")
            if not data.empty:
                last_close = float(data["Close"].iloc[-1])
                prev_close = float(data["Close"].iloc[-2]) if len(data) > 1 else last_close
                change_percent = ((last_close - prev_close) / prev_close * 100) if prev_close != 0 else 0.0
                timestamp = data.index[-1].isoformat() if hasattr(data.index[-1], 'isoformat') else str(data.index[-1])
                return {
                    "timestamp": timestamp,
                    "price": last_close,
                    "change_percent": round(change_percent, 2)
                }
        except Exception:
            continue
    return None


def get_yfinance_historical_prices(symbol: str, start: Union[str, datetime], end: Union[str, datetime], country: str) -> Optional[list]:
    """Try historical price retrieval with symbol variants.

    Returns a list of records with Open/High/Low/Close/Volume or None if not found.
    """
    variants = get_symbol_variants(symbol, country)

    # Normalize start/end if strings are passed
    try:
        start_dt = parse(start) if isinstance(start, str) else start
    except Exception:
        start_dt = start
    try:
        end_dt = parse(end) if isinstance(end, str) else end
    except Exception:
        end_dt = end
    for s in variants:
        try:
            ticker = yf.Ticker(s)
            data = ticker.history(start=start_dt, end=end_dt)
            if not data.empty:
                # Ensure dates are included in the records
                df = data.reset_index()
                df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
                df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
                # change all fields to lowercase for consistency
                df.columns = [col.lower() for col in df.columns]
                return df.to_dict("records")
        except Exception:
            continue
    return None

def _get_value(info: dict, key: str) -> Optional[object]:
    return info.get(key)

def get_yfinance_stock_info(symbol: str, country: str) -> Optional[dict]:
    variants = get_symbol_variants(symbol, country)
    for s in variants:
        info = _fetch_stock_info(s)
        if info is not None:
            return info
    return None

def _fetch_stock_info(symbol: str) -> Optional[dict]:
    try:
        stock = yf.Ticker(symbol)
        info = stock.info or {}
        history = stock.history(period="1y")

        market_cap = _get_value(info, "marketCap")
        ma_20 = _moving_average(history, 20)
        ma_50 = _moving_average(history, 50)
        ma_200 = _moving_average(history, 200)

        return {
            "symbol": info.get("symbol", symbol.upper()),
            "name": _get_value(info, "shortName"),
            "currency": _get_value(info, "currency"),
            "current_price": _get_value(info, "currentPrice"),
            "week_52_high": _get_value(info, "fiftyTwoWeekHigh"),
            "week_52_low": _get_value(info, "fiftyTwoWeekLow"),
            "trailing_pe": _get_value(info, "trailingPE"),
            "forward_pe": _get_value(info, "forwardPE"),
            "market_cap": market_cap,
            "market_cap_type": _market_cap_type(market_cap),
            "dividend_yield": _get_value(info, "dividendYield"),
            "moving_average_20": ma_20,
            "moving_average_50": ma_50,
            "moving_average_200": ma_200,
        }
    except Exception as ex:
        print(f"Exception {ex}. Failed to fetch data for symbol: {symbol}")
        return None

def _market_cap_type(market_cap: Optional[object]) -> str:
    if not isinstance(market_cap, (int, float)):
        return "N/A"

    if market_cap < 2_000_000_000:
        return "small_cap"
    if market_cap < 10_000_000_000:
        return "mid_cap"
    if market_cap < 200_000_000_000:
        return "large_cap"
    return "mega_cap"


def _moving_average(history, window: int) -> Optional[float]:
    if history is None or history.empty or "Close" not in history:
        return None
    series = history["Close"].dropna()
    if series.empty:
        return None
    return float(series.rolling(window=window).mean().iloc[-1])
