from ib_insync import IB, Stock


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
        mapping = {'1S': '1 secs', '5S': '5 secs', '15S': '15 secs', '30S': '30 secs', '1M': '1 min', '5M': '5 mins', '15M': '15 mins', '30M': '30 mins', '1H': '1 hour', '1D': '1 day', '1W': '1 week'}
        return mapping.get(granularity, '1 day')

    def _get_duration(self, granularity):
        """Returns duration string for IBKR request"""
        if granularity in ['1S', '5S', '15S', '30S', '1M', '5M', '15M', '30M', '1H']:
            return '1 D'
        return '1 Y'

    async def fetch_historical_data(self, ticker, granularity, end_date, currency='USD', exchange='SMART'):
        """Fetches historical data for ticker at granularity ending at end_date"""
        contract = Stock(ticker, exchange, currency)
        await self.ib.qualifyContractsAsync(contract)
        bars = await self.ib.reqHistoricalDataAsync(contract, endDateTime=end_date, durationStr=self._get_duration(granularity),
                                                     barSizeSetting=self._get_bar_size(granularity), whatToShow='TRADES', useRTH=True)
        return [{'date': bar.date, 'open': bar.open, 'high': bar.high, 'low': bar.low, 'close': bar.close, 'volume': bar.volume, 'average': bar.average, 'barCount': bar.barCount} for bar in bars]

    # IO --------------------------------------------------------------------
    # Misc ------------------------------------------------------------------
