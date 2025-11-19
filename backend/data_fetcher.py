"""
Data Fetcher Module
Handles fetching market data from AlphaVantage MCP
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any

import pandas as pd

logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetches and processes market data from AlphaVantage"""
    
    def __init__(self, alphavantage_client=None):
        """Initialize data fetcher with AlphaVantage client"""
        self.av_client = alphavantage_client
        
    async def fetch_market_data(
        self,
        tickers: List[str],
        start_date: datetime,
        end_date: datetime,
        frequency: str,
        fields: List[str],
        include_dividends: bool = False,
        include_splits: bool = False,
        include_delistings: bool = False
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Fetch OHLCV data for given tickers
        
        Returns:
            - DataFrame with MultiIndex (timestamp, ticker) and OHLCV columns
            - Dict with corporate actions (dividends, splits, delistings)
        """
        logger.info(f"Fetching data for {len(tickers)} tickers from {start_date} to {end_date}")
        
        all_data = []
        corporate_actions = {
            'dividends': {},
            'splits': {},
            'delistings': []
        }
        
        for ticker in tickers:
            try:
                # Fetch OHLCV data based on frequency
                df = await self._fetch_ticker_data(ticker, frequency, start_date, end_date)
                
                if df is not None and not df.empty:
                    df['ticker'] = ticker
                    all_data.append(df)
                    
                    # Fetch corporate actions if requested
                    if include_dividends:
                        dividends = await self._fetch_dividends(ticker, start_date, end_date)
                        if dividends is not None:
                            corporate_actions['dividends'][ticker] = dividends
                    
                    if include_splits:
                        splits = await self._fetch_splits(ticker, start_date, end_date)
                        if splits is not None:
                            corporate_actions['splits'][ticker] = splits
                    
                    if include_delistings:
                        delisting_info = await self._check_delisting(ticker)
                        if delisting_info:
                            corporate_actions['delistings'].append(delisting_info)
                else:
                    logger.warning(f"No data found for {ticker}")
                    
            except Exception as e:
                logger.error(f"Error fetching data for {ticker}: {str(e)}")
                continue
        
        if not all_data:
            raise ValueError("No market data could be fetched for any ticker")
        
        # Combine all ticker data
        combined_df = pd.concat(all_data, ignore_index=False)
        
        # Filter to only requested fields
        available_fields = [f for f in fields if f.lower() in combined_df.columns]
        if 'timestamp' not in available_fields:
            available_fields = ['timestamp'] + available_fields
        if 'ticker' not in available_fields:
            available_fields = available_fields + ['ticker']
            
        combined_df = combined_df[available_fields]
        
        # Set multi-index
        combined_df = combined_df.set_index(['timestamp', 'ticker'])
        
        # Align data to common timestamps
        combined_df = self._align_timestamps(combined_df)
        
        logger.info(f"Successfully fetched {len(combined_df)} rows of data")
        return combined_df, corporate_actions
    
    async def _fetch_ticker_data(
        self, 
        ticker: str, 
        frequency: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data for a single ticker"""
        try:
            if self.av_client is None:
                logger.error("AlphaVantage client not configured. Cannot fetch data.")
                return None
            
            # Map frequency to AlphaVantage endpoint
            if frequency == 'daily':
                data = await self._fetch_daily_data(ticker)
            elif frequency in ['1min', '5min', '15min', '30min', '60min']:
                data = await self._fetch_intraday_data(ticker, frequency)
            elif frequency == 'weekly':
                data = await self._fetch_weekly_data(ticker)
            elif frequency == 'monthly':
                data = await self._fetch_monthly_data(ticker)
            else:
                raise ValueError(f"Unsupported frequency: {frequency}")
            
            if data is None:
                return None
            
            # Filter by date range
            data = data[(data['timestamp'] >= start_date) & (data['timestamp'] <= end_date)]
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            return None
    
    async def _fetch_daily_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Fetch daily data from AlphaVantage"""
        time_series_key = "Time Series (Daily)"
        data = await self._call_client(self.av_client.get_daily_adjusted, ticker, "full")
        time_series = data.get(time_series_key)
        if not time_series:
            logger.error(f"No daily data returned for {ticker}")
            return None
        return self._timeseries_to_df(time_series, include_adjusted=True)
    
    async def _fetch_intraday_data(self, ticker: str, interval: str) -> Optional[pd.DataFrame]:
        """Fetch intraday data from AlphaVantage"""
        interval_map = {
            "1min": "1min",
            "5min": "5min",
            "15min": "15min",
            "30min": "30min",
            "60min": "60min",
        }
        interval_str = interval_map.get(interval)
        if not interval_str:
            raise ValueError(f"Unsupported intraday interval: {interval}")
        
        data = await self._call_client(self.av_client.get_intraday, ticker, interval_str, "full")
        time_series_key = f"Time Series ({interval_str})"
        time_series = data.get(time_series_key)
        if not time_series:
            logger.error(f"No intraday data returned for {ticker} ({interval_str})")
            return None
        return self._timeseries_to_df(time_series, include_adjusted=False)
    
    async def _fetch_weekly_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Fetch weekly data from AlphaVantage"""
        data = await self._call_client(self.av_client.get_weekly_adjusted, ticker)
        time_series = data.get("Weekly Adjusted Time Series")
        if not time_series:
            logger.error(f"No weekly data returned for {ticker}")
            return None
        return self._timeseries_to_df(time_series, include_adjusted=True)
    
    async def _fetch_monthly_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Fetch monthly data from AlphaVantage"""
        data = await self._call_client(self.av_client.get_monthly_adjusted, ticker)
        time_series = data.get("Monthly Adjusted Time Series")
        if not time_series:
            logger.error(f"No monthly data returned for {ticker}")
            return None
        return self._timeseries_to_df(time_series, include_adjusted=True)
    
    async def _fetch_dividends(
        self, 
        ticker: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Fetch dividend history"""
        if self.av_client is None:
            return None
        data = await self._call_client(self.av_client.get_dividends, ticker)
        records = data.get("data", [])
        if not records:
            return None
        
        rows = []
        for record in records:
            ex_date = record.get("exDate")
            if not ex_date:
                continue
            ex_dt = pd.to_datetime(ex_date)
            if ex_dt < start_date or ex_dt > end_date:
                continue
            rows.append(
                {
                    "date": ex_dt,
                    "amount": float(record.get("amount", 0)),
                    "recordDate": record.get("recordDate"),
                    "paymentDate": record.get("paymentDate"),
                    "declarationDate": record.get("declarationDate"),
                }
            )
        
        if not rows:
            return None
        
        df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
        return df
    
    async def _fetch_splits(
        self, 
        ticker: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Fetch split history"""
        if self.av_client is None:
            return None
        data = await self._call_client(self.av_client.get_splits, ticker)
        records = data.get("data", [])
        if not records:
            return None
        
        rows = []
        for record in records:
            split_date = record.get("splitDate")
            if not split_date:
                continue
            split_dt = pd.to_datetime(split_date)
            if split_dt < start_date or split_dt > end_date:
                continue
            ratio = record.get("splitCoefficient") or record.get("splitCoefficientRatio")
            try:
                ratio_value = float(ratio) if ratio and ":" not in ratio else self._parse_split_ratio(ratio)
            except Exception:
                ratio_value = None
            rows.append(
                {
                    "date": split_dt,
                    "ratio": ratio_value,
                    "fromFactor": record.get("fromFactor"),
                    "toFactor": record.get("toFactor"),
                }
            )
        
        if not rows:
            return None
        
        df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
        return df
    
    async def _check_delisting(self, ticker: str) -> Optional[Dict]:
        """Check if ticker is delisted"""
        if self.av_client is None:
            return None
        data = await self._call_client(self.av_client.get_listing_status, state="delisted")
        listings = data if isinstance(data, list) else data.get("data", [])
        if not listings:
            return None
        
        for listing in listings:
            if listing.get("symbol", "").upper() == ticker.upper():
                return listing
        return None
    
    def _align_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Align all tickers to common timestamps"""
        # Get all unique timestamps
        timestamps = df.index.get_level_values('timestamp').unique()
        tickers = df.index.get_level_values('ticker').unique()
        
        # Create complete index
        complete_index = pd.MultiIndex.from_product(
            [timestamps, tickers],
            names=['timestamp', 'ticker']
        )
        
        # Reindex to include all combinations
        df = df.reindex(complete_index)
        
        return df
    
    
    def handle_missing_data(self, df: pd.DataFrame, method: str) -> pd.DataFrame:
        """
        Handle missing data according to specified method
        
        Args:
            df: DataFrame with potential missing values
            method: 'skip', 'forward-fill', or 'interpolate'
        """
        if method == 'skip':
            # Remove rows with any missing data
            return df.dropna()
        elif method == 'forward-fill':
            # Forward fill missing values
            return df.fillna(method='ffill')
        elif method == 'interpolate':
            # Linear interpolation
            return df.interpolate(method='linear')
        else:
            return df
    
    def apply_split_adjustments(
        self, 
        df: pd.DataFrame, 
        splits: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """Apply split adjustments to historical prices"""
        adjusted_df = df.copy()
        
        for ticker, split_data in splits.items():
            if split_data is None or split_data.empty:
                continue
            
            ticker_mask = adjusted_df.index.get_level_values('ticker') == ticker
            
            for _, split_row in split_data.iterrows():
                split_date = split_row['date']
                split_ratio = split_row['ratio']
                
                # Adjust prices before split date
                date_mask = adjusted_df.index.get_level_values('timestamp') < split_date
                mask = ticker_mask & date_mask
                
                price_cols = ['open', 'high', 'low', 'close']
                for col in price_cols:
                    if col in adjusted_df.columns:
                        adjusted_df.loc[mask, col] *= split_ratio
                
                if 'volume' in adjusted_df.columns:
                    adjusted_df.loc[mask, 'volume'] /= split_ratio
        
        return adjusted_df

    async def _call_client(self, func, *args, **kwargs) -> Any:
        """Run blocking AlphaVantage client call in executor"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    def _timeseries_to_df(self, time_series: Dict[str, Dict[str, str]], include_adjusted: bool) -> Optional[pd.DataFrame]:
        """Convert AlphaVantage time series dict to DataFrame"""
        rows = []
        for date_str, values in time_series.items():
            try:
                volume_value = (
                    values.get("6. volume")
                    or values.get("5. volume")
                    or values.get("volume")
                    or 0
                )
                row = {
                    "timestamp": pd.to_datetime(date_str),
                    "open": float(values.get("1. open")),
                    "high": float(values.get("2. high")),
                    "low": float(values.get("3. low")),
                    "close": float(values.get("4. close")),
                    "volume": float(volume_value),
                }
                if include_adjusted and "5. adjusted close" in values:
                    row["adjusted_close"] = float(values.get("5. adjusted close"))
                rows.append(row)
            except (TypeError, ValueError) as exc:
                logger.warning(f"Skipping malformed data point ({date_str}): {exc}")
                continue
        
        if not rows:
            return None
        
        df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
        return df

    def _parse_split_ratio(self, ratio: Optional[str]) -> Optional[float]:
        """Convert split ratio string (e.g., '2:1') to float multiplier"""
        if not ratio:
            return None
        if ":" in ratio:
            parts = ratio.split(":")
            if len(parts) == 2:
                try:
                    return float(parts[0]) / float(parts[1])
                except ValueError:
                    return None
        try:
            return float(ratio)
        except ValueError:
            return None

