"""
AlphaVantage MCP Client Wrapper
Uses the official AlphaVantage HTTP API (via MCP integration) to fetch market data.
"""
import logging
import os
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)


class AlphaVantageMCPClient:
    """Client wrapper for AlphaVantage MCP tools"""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: Optional[str] = None, session: Optional[requests.Session] = None):
        """
        Initialize the client

        Args:
            api_key: AlphaVantage API key (defaults to ALPHAVANTAGE_API_KEY env variable)
            session: Optional requests session for connection pooling
        """
        self.api_key = api_key or os.getenv("ALPHAVANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("AlphaVantage API key not provided. Set ALPHAVANTAGE_API_KEY environment variable.")

        self.session = session or requests.Session()
        logger.info("AlphaVantage MCP client initialized")

    def _get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform GET request to AlphaVantage API"""
        params = {**params, "apikey": self.api_key}
        response = self.session.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "Error Message" in data:
            raise ValueError(f"AlphaVantage error: {data['Error Message']}")
        if "Note" in data:
            logger.warning(f"AlphaVantage note: {data['Note']}")
        return data

    def get_daily_adjusted(self, symbol: str, outputsize: str = "full") -> Dict[str, Any]:
        """Fetch daily adjusted time series"""
        return self._get(
            {
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": symbol,
                "outputsize": outputsize,
                "datatype": "json",
            }
        )

    def get_intraday(self, symbol: str, interval: str, outputsize: str = "compact") -> Dict[str, Any]:
        """Fetch intraday time series"""
        return self._get(
            {
                "function": "TIME_SERIES_INTRADAY",
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "datatype": "json",
                "adjusted": "true",
            }
        )

    def get_weekly_adjusted(self, symbol: str) -> Dict[str, Any]:
        """Fetch weekly adjusted time series"""
        return self._get(
            {
                "function": "TIME_SERIES_WEEKLY_ADJUSTED",
                "symbol": symbol,
                "datatype": "json",
            }
        )

    def get_monthly_adjusted(self, symbol: str) -> Dict[str, Any]:
        """Fetch monthly adjusted time series"""
        return self._get(
            {
                "function": "TIME_SERIES_MONTHLY_ADJUSTED",
                "symbol": symbol,
                "datatype": "json",
            }
        )

    def get_dividends(self, symbol: str) -> Dict[str, Any]:
        """Fetch dividend history"""
        return self._get(
            {
                "function": "DIVIDENDS",
                "symbol": symbol,
                "datatype": "json",
            }
        )

    def get_splits(self, symbol: str) -> Dict[str, Any]:
        """Fetch split history"""
        return self._get(
            {
                "function": "SPLITS",
                "symbol": symbol,
                "datatype": "json",
            }
        )

    def get_listing_status(self, date: Optional[str] = None, state: str = "active") -> Dict[str, Any]:
        """Fetch listing status"""
        params = {
            "function": "LISTING_STATUS",
            "state": state,
            "datatype": "json",
        }
        if date:
            params["date"] = date
        return self._get(params)

