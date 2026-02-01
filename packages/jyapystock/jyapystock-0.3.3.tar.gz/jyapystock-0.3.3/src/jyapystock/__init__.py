"""jyapystock package exports.

Provide a small convenience re-export so users can import symbols directly
from the package namespace: `from jyapystock import StockPriceProvider`.
"""

from .stock_price_provider import StockPriceProvider
import logging


__all__ = ["StockPriceProvider"]


# Create a logger for your library
logger = logging.getLogger(__name__)

logger.addHandler(logging.NullHandler())