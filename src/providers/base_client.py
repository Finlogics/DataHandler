from abc import ABC, abstractmethod

class ProviderClient(ABC):
    """Base class for data provider clients"""

    @abstractmethod
    async def connect(self):
        """Connects to the provider"""
        pass

    @abstractmethod
    async def disconnect(self):
        """Disconnects from the provider"""
        pass

    @abstractmethod
    async def fetch_historical_data(self, ticker: str, granularity: str, end_date: str, currency: str = 'USD', exchange: str = 'SMART', contract_type: str = 'Stock', what_to_show: str = 'TRADES') -> list[dict]:
        """Fetches historical data; returns list of dicts with OHLCV fields"""
        pass
