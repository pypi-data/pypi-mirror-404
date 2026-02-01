import yfinance as yf
import pandas as pd
from typing import Optional, List, Union

class DataLoader:
    """
    A robust data loader for fetching financial data.
    """
    @staticmethod
    def download_data(ticker: Union[str, List[str]], start: str, end: str) -> pd.DataFrame:
        """
        Downloads data from Yahoo Finance.
        
        Args:
            ticker: Single ticker string or list of tickers.
            start: Start date 'YYYY-MM-DD'.
            end: End date 'YYYY-MM-DD'.
        
        Returns:
            pd.DataFrame: Adjusted Close prices and other data.
        """
        print(f"Fetching data for {ticker}...")
        data = yf.download(ticker, start=start, end=end, progress=False)
        if data.empty:
            raise ValueError(f"No data found for {ticker}. Check ticker symbol or date range.")
        
        # Flatten multi-level columns (yfinance returns MultiIndex for single tickers)
        if isinstance(data.columns, pd.MultiIndex):
            # For single ticker, take the first level only
            if isinstance(ticker, str):
                data.columns = data.columns.get_level_values(0)
            else:
                # For multiple tickers, keep as-is or flatten appropriately
                pass
        
        return data