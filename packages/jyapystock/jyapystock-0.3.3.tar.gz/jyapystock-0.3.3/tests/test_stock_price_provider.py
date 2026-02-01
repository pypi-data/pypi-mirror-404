import datetime
import unittest
from jyapystock.stock_price_provider import StockPriceProvider
import os
import logging

# Allow running provider-specific tests by setting the PROVIDER env var to
# one of: 'yfinance', 'alphavantage', 'nasdaq', 'nse'. When unset, all tests run.
PROVIDER = os.environ.get("PROVIDER")
if PROVIDER:
    PROVIDER = PROVIDER.lower()

def should_run_for(providers):
    if not PROVIDER:
        return True
    return PROVIDER in providers

class TestStockPriceProvider(unittest.TestCase):
    def setUp(self):
        self.provider_yf = StockPriceProvider(country="USA", source="yfinance")
        api_key = os.environ.get("ALPHAVANTAGE_API_KEY", "demo")
        self.provider_av = StockPriceProvider(country="USA", source="alphavantage", alpha_vantage_api_key=api_key)
        self.provider_yf_india = StockPriceProvider(country="India", source="yfinance")
        self.provider_nasdaq = StockPriceProvider(country="USA", source="nasdaq")
        self.provider_nse = StockPriceProvider(country="India", source="nse")
        self.provider_nyse = StockPriceProvider(country="USA", source="nyse")
        self.provider_auto = StockPriceProvider(country="USA", source="auto")
        self.provider_auto_india = StockPriceProvider(country="India", source="auto")
        logging.basicConfig(level=logging.WARNING)
    
    def test_live_price_yfinance(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping yfinance tests in this run")
        result = self.provider_yf.get_live_price("AAPL")
        self.assertIsInstance(result, dict)
        self.assertIn("price", result)
        self.assertIn("timestamp", result)
        self.assertIn("change_percent", result)
        self.assertGreater(result["price"], 0)
        # special case for symbol with dot
        result_dot = self.provider_yf.get_live_price("BRK.B")
        self.assertIsInstance(result_dot, dict)
        self.assertIn("price", result_dot)
        self.assertIn("timestamp", result_dot)
        self.assertIn("change_percent", result_dot)
        self.assertGreater(result_dot["price"], 0)

    def test_historical_price_yfinance(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping yfinance tests in this run")
        hist = self.provider_yf.get_historical_price("AAPL", "2023-01-01", "2023-01-10")
        self.assertIsInstance(hist, list)
        self.assertGreater(len(hist), 0)
        self.common_historical_price_test(hist)
    
    def test_live_price_yfinance_india(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping yfinance tests in this run")
        result = self.provider_yf_india.get_live_price("RELIANCE")
        self.assertIsInstance(result, dict)
        self.assertIn("price", result)
        self.assertIn("timestamp", result)
        self.assertIn("change_percent", result)
        self.assertGreater(result["price"], 0)

    def test_historical_price_yfinance(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping yfinance tests in this run")
        hist = self.provider_yf_india.get_historical_price("RELIANCE", "2023-01-01", "2023-01-10")
        self.assertIsInstance(hist, list)
        self.assertGreater(len(hist), 0)
        self.common_historical_price_test(hist)
    
    def test_get_stock_info_yfinance(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping yfinance tests in this run")
        info = self.provider_yf.get_stock_info("AAPL")
        self.assertIsInstance(info, dict)
        self.assertIn("symbol", info)
        self.assertIn("name", info)
        self.assertIn("current_price", info)
        self.assertIn("week_52_high", info)
        self.assertIn("market_cap_type", info)

    def test_get_stock_info_yfinance_india(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping yfinance tests in this run")
        info = self.provider_yf_india.get_stock_info("RELIANCE")
        self.assertIsInstance(info, dict)
        self.assertIn("symbol", info)
        self.assertIn("name", info)
        self.assertIn("current_price", info)
        self.assertIn("week_52_high", info)
        self.assertIn("market_cap_type", info)    

    def test_live_price_alpha_vantage(self):
        if not should_run_for(["alphavantage"]):
            self.skipTest("Skipping Alpha Vantage tests in this run")
        result = self.provider_av.get_live_price("IBM")
        self.assertIsInstance(result, dict)
        self.assertIn("price", result)
        self.assertIn("timestamp", result)
        self.assertIn("change_percent", result)

    def test_historical_price_alpha_vantage(self):
        if not should_run_for(["alphavantage"]):
            self.skipTest("Skipping Alpha Vantage tests in this run")
        hist = self.provider_av.get_historical_price("IBM", "2023-01-01", "2023-01-10")
        self.assertTrue(isinstance(hist, list))
        self.assertGreater(len(hist), 0)

    def test_live_price_auto(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping auto tests in this run")
        provider_auto = StockPriceProvider(country="USA")  # default None == auto
        result = provider_auto.get_live_price("AAPL")
        self.assertIsInstance(result, dict)
        self.assertIn("price", result)
        self.assertIn("timestamp", result)
        self.assertIn("change_percent", result)

    def test_historical_price_auto(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping auto tests in this run")
        provider_auto = StockPriceProvider(country="USA", source="auto")
        hist = provider_auto.get_historical_price("AAPL", "2023-01-01", "2023-01-10")
        # historical can be list or None depending on source availability
        self.assertTrue(isinstance(hist, list))
        self.assertGreater(len(hist), 0)
        self.common_historical_price_test(hist)

    def test_get_stock_info_auto(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping yfinance tests in this run")
        info = self.provider_auto.get_stock_info("AAPL")
        self.assertIsInstance(info, dict)
        self.assertIn("symbol", info)
        self.assertIn("name", info)
        self.assertIn("current_price", info)
        self.assertIn("week_52_high", info)
        self.assertIn("market_cap_type", info)

    def test_india_symbol_variants(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping India/yfinance tests in this run")
        # Ensure provider for India attempts .NS/.BO variants (result may be None if network/API fails)
        provider_in = StockPriceProvider(country="India")
        result = provider_in.get_live_price("RELIANCE")
        self.assertIsInstance(result, dict)
        self.assertIn("price", result)
        self.assertIn("timestamp", result)
        self.assertIn("change_percent", result)

    def test_india_historical_variants(self):
        if not should_run_for(["yfinance"]):
            self.skipTest("Skipping India/yfinance tests in this run")
        provider_in = StockPriceProvider(country="India")
        hist = provider_in.get_historical_price("RELIANCE", "2023-01-01", "2023-01-10")
        self.assertTrue(isinstance(hist, list))
        self.assertGreater(len(hist), 0)
        self.common_historical_price_test(hist)

    def test_historical_price_nasdaq(self):
        if not should_run_for(["nasdaq"]):
            self.skipTest("Skipping NASDAQ tests in this run")
        # Call the real NASDAQ provider (no mocking) — result may be None if API unavailable
        today = datetime.date.today()
        thirty_days_ago = today - datetime.timedelta(days=30)
        twenty_days_ago = today - datetime.timedelta(days=20)
        hist = self.provider_nasdaq.get_historical_price('AAPL', thirty_days_ago.isoformat(), twenty_days_ago.isoformat())
        # Should be a list of records or None depending on network/API
        self.assertTrue(isinstance(hist, list))
        self.assertGreater(len(hist), 0)
        self.common_historical_price_test(hist)
    
    def test_live_price_nasdaq(self):
        if not should_run_for(["nasdaq"]):
            self.skipTest("Skipping NASDAQ tests in this run")
        # Call the real NASDAQ live price (no mocking) — returns dict or None
        result = self.provider_nasdaq.get_live_price('AAPL')
        self.assertIsInstance(result, dict)
        self.assertIn("price", result)
        self.assertIn("timestamp", result)
        self.assertIn("change_percent", result)
        self.assertGreater(result["price"], 0)

    def test_live_price_nse(self):
        if not should_run_for(["nse"]):
            self.skipTest("Skipping NSE tests in this run")
        # Call the real NSE live price (no mocking) — returns dict or None
        result = self.provider_nse.get_live_price('SBIN')
        self.assertIsInstance(result, dict)
        self.assertIn("price", result)
        self.assertIn("timestamp", result)
        self.assertIn("change_percent", result)
        self.assertGreater(result["price"], 0)

    def test_historical_price_nse(self):
        if not should_run_for(["nse"]):
            self.skipTest("Skipping NSE tests in this run")
        hist = self.provider_nse.get_historical_price('INFY', '2025-12-17', '2025-12-24')
        self.assertTrue(isinstance(hist, list))
        self.assertGreater(len(hist), 0)
        self.common_historical_price_test(hist)

    def test_historical_price_nyse(self):
        if not should_run_for(["nyse"]):
            self.skipTest("Skipping NYSE tests in this run")
        # Call the real NYSE provider (no mocking) — result may be None if API unavailable
        hist = self.provider_nyse.get_historical_price('BAC', '2025-12-17', '2025-12-25')
        # Should be a list of records or None depending on network/API
        self.assertTrue(isinstance(hist, list))
        self.assertGreater(len(hist), 0)
        self.common_historical_price_test(hist)

    def test_live_price_nyse(self):
        if not should_run_for(["nyse"]):
            self.skipTest("Skipping NYSE tests in this run")
        # Call the real NYSE live price (no mocking) — returns dict or None
        result = self.provider_nyse.get_live_price('BAC')
        self.assertTrue(isinstance(result, dict) or result is None)
        if result is not None:
            self.assertIn("price", result)
            self.assertIn("timestamp", result)
            self.assertIn("change_percent", result)
            self.assertGreater(result["price"], 0)
    
    @classmethod
    def common_historical_price_test(cls, records):
        for record in records:
            assert "date" in record
            assert "open" in record
            assert "high" in record
            assert "low" in record
            assert "close" in record
            assert "volume" in record
            # assert date format is 'yyyy-mm-dd'
            try:
                datetime.datetime.strptime(record["date"], "%Y-%m-%d")
            except ValueError:
                raise AssertionError(f"Date format incorrect: {record['date']}")
            assert isinstance(record["open"], (int, float))
            assert isinstance(record["high"], (int, float))
            assert isinstance(record["low"], (int, float))
            assert isinstance(record["close"], (int, float))
            assert isinstance(record["volume"], (int, float))

if __name__ == "__main__":
    unittest.main()
