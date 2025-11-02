from ib_insync import IB, Stock, util
from datetime import datetime, timedelta
import asyncio

class IBKRClient:
    """Wrapper for ib_insync to fetch historical market data"""

    # LifeCycle -------------------------------------------------------------
    def __init__(self, config):
        self.config = config
        self.ib = IB()

    async def connect(self):
        """Connects to IBKR Gateway/TWS"""
        await self.ib.connectAsync(self.config.host, self.config.port, clientId=self.config.client_id, timeout=20, readonly=True)

    async def disconnect(self):
        """Disconnects from IBKR"""
        self.ib.disconnect()

    # Business Logic --------------------------------------------------------
    def _get_bar_size(self, granularity):
        """Maps granularity to IBKR bar size"""
        mapping = {'1S': '1 secs', '1M': '1 min', '1D': '1 day'}
        return mapping.get(granularity, '1 day')

    def _get_duration(self, granularity):
        """Returns duration string for IBKR request"""
        if granularity in ['1S', '1M']:
            return '1 D'
        return '1 Y'

    async def fetch_historical_data(self, ticker, granularity, end_date):
        """Fetches historical data for ticker at granularity ending at end_date"""
        contract = Stock(ticker, 'SMART', 'USD')
        await self.ib.qualifyContractsAsync(contract)
        bars = await self.ib.reqHistoricalDataAsync(contract, endDateTime=end_date, durationStr=self._get_duration(granularity), barSizeSetting=self._get_bar_size(granularity), whatToShow='TRADES', useRTH=True)
        return [{'date': bar.date, 'open': bar.open, 'high': bar.high, 'low': bar.low, 'close': bar.close, 'volume': bar.volume, 'average': bar.average, 'barCount': bar.barCount} for bar in bars]

    # IO --------------------------------------------------------------------
    # Misc ------------------------------------------------------------------
