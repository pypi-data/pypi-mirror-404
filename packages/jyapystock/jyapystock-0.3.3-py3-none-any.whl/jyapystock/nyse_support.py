from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional, Union
from dateutil.parser import parse
import requests

NYSE_QUOTES_URL = "https://www.nyse.com/api/nyseservice/v1/quotes"


def _extract_latest_quote(payload: Any) -> Optional[dict[str, Any]]:
    if isinstance(payload, list) and payload:
        payload = payload[0]
    if not isinstance(payload, dict):
        return None

    quote = payload.get("quote")
    if isinstance(quote, dict):
        payload = quote

    def _to_float(value: Any) -> Optional[float]:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(",", ""))
            except ValueError:
                return None
        return None

    price = None
    for key in ("last", "lastPrice", "price", "tradePrice", "latestPrice"):
        price = _to_float(payload.get(key))
        if price is not None:
            break

    change_percent = None
    for key in ("pctchg", "changePercent", "change_percent"):
        change_percent = _to_float(payload.get(key))
        if change_percent is not None:
            break

    timestamp = payload.get("time") or payload.get("lastUpdateTime")

    if price is None and change_percent is None and timestamp is None:
        return None

    return {
        "price": price,
        "timestamp": timestamp,
        "change_percent": change_percent,
    }


def _parse_history_date(value: str) -> Optional[date]:
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _filter_history_by_date(
    rows: list[dict[str, Any]],
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    filtered = []
    for row in rows:
        row_date = row.get("date")
        if not isinstance(row_date, str):
            continue
        parsed = _parse_history_date(row_date)
        if parsed is None:
            continue
        if start_date <= parsed <= end_date:
            filtered.append(row)
    return filtered


def _normalize_history_row(row: dict[str, Any]) -> Optional[dict[str, Any]]:
    raw_date = row.get("date")
    if not isinstance(raw_date, str):
        return None
    parsed_date = _parse_history_date(raw_date)
    if parsed_date is None:
        return None

    def _to_float(value: Any) -> Optional[float]:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(",", ""))
            except ValueError:
                return None
        return None

    def _to_int(value: Any) -> Optional[int]:
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(float(value.replace(",", "")))
            except ValueError:
                return None
        return None

    return {
        "date": parsed_date.isoformat(),
        "open": _to_float(row.get("open")),
        "high": _to_float(row.get("high")),
        "low": _to_float(row.get("low")),
        "close": _to_float(row.get("close")),
        "volume": _to_int(row.get("volume")),
    }


def get_nyse_live_price(symbol: str) -> Optional[dict[str, Any]]:
    try:
        response = requests.get(
            NYSE_QUOTES_URL, params={"symbol": symbol}, timeout=10
        )
        response.raise_for_status()
    except requests.RequestException:
        return None

    return _extract_latest_quote(response.json())


def get_nyse_historical_prices(
    symbol: str,
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    country: str,
    history_url: Optional[str] = None,
) -> Optional[list[dict[str, Any]]]:
    if country != "usa":
        return None  # NYSE support only for USA
    # Normalize start/end to datetime if they are strings
    try:
        if isinstance(start_date, str):
            start_date = parse(start_date).date()
        if isinstance(end_date, str):
            end_date = parse(end_date).date()
    except Exception:
        # If parsing fails, leave as-is and let later formatting raise if necessary
        pass
    url = history_url or NYSE_QUOTES_URL
    params = {
        "symbol": symbol,
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return None
    payload = response.json()
    rows: list[dict[str, Any]] = []
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        history = payload.get("history")
        if isinstance(history, dict):
            data = history.get("data")
            if isinstance(data, list):
                rows = data
        quote_history = payload.get("quoteHistory")
        if isinstance(quote_history, dict):
            history_list = quote_history.get("historyList")
            if isinstance(history_list, list):
                rows = history_list
        data = payload.get("data")
        if isinstance(data, list):
            rows = data

    if not rows:
        return []

    filtered = _filter_history_by_date(rows, start_date, end_date)
    normalized = []
    for row in filtered:
        normalized_row = _normalize_history_row(row)
        if normalized_row is not None:
            normalized.append(normalized_row)
    return normalized


if __name__ == "__main__":
    from datetime import date, timedelta

    symbol = "ACHR"
    latest = get_nyse_live_price(symbol)
    end = date.today() - timedelta(days=30)
    start = end - timedelta(days=7)
    history = get_nyse_historical_prices(symbol, start, end, "usa")

    print(f"Latest price for {symbol}: {latest}")
    if history is None:
        print(f"History rows for {symbol} ({start} to {end}): None")
    else:
        print(f"History rows for {symbol} ({start} to {end}): {len(history)}")
