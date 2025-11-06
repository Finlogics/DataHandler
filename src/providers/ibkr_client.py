from ib_async import IB, Stock, Index, CFD
import asyncio


class IBKRClient:
    """Wrapper for ib_async to fetch historical market data"""

    # LifeCycle -------------------------------------------------------------
    def __init__(self, config):
        self.config = config
        self.ib = IB()
        self.ib.disconnectedEvent += self._on_disconnected

    async def connect(self):
        """Connects to IBKR Gateway/TWS with retry logic"""
        max_attempts = 10
        current_attempt = 0
        delay_secs = 60

        while current_attempt < max_attempts:
            try:
                await self.ib.connectAsync(self.config.host, self.config.port, clientId=self.config.client_id, timeout=20, readonly=True)
                print(f"IBKR Client connected with host={self.config.host}, port={self.config.port}, clientId={self.config.client_id}")
                break
            except Exception as err:
                current_attempt += 1
                if current_attempt < max_attempts:
                    print(f"Connection failed, retrying in {delay_secs} seconds... (attempt {current_attempt}/{max_attempts})")
                    await asyncio.sleep(delay_secs)
                else:
                    raise Exception(f"Max reconnection attempts ({max_attempts}) exceeded") from err

    async def disconnect(self):
        """Disconnects from IBKR"""
        self.ib.disconnect()

    def _on_disconnected(self):
        """Auto-reconnect handler when IB Gateway disconnects"""
        print("Disconnected from IB Gateway. Attempting to reconnect...")
        asyncio.create_task(self.connect())

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

    async def fetch_historical_data(self, ticker, granularity, end_date, currency='USD', exchange='SMART', contract_type='Stock', what_to_show='TRADES'):
        """Fetches historical data for ticker at granularity ending at end_date"""
        
        if contract_type == 'Stock':
            contract = Stock(ticker, exchange, currency)
        elif contract_type == 'Index':
            contract = Index(ticker, exchange, currency)
        elif contract_type == 'CFD':
            contract = CFD(ticker, exchange, currency)
        else:
            raise ValueError(f"Unsupported contract type: {contract_type}")
        
        verified = await self.ib.qualifyContractsAsync(contract)
        if not verified or not verified[0]:
            raise ValueError(f"Could not verify contract for ticker {ticker} on exchange {exchange} with currency {currency}")
        
        bars = await self.ib.reqHistoricalDataAsync(verified[0], endDateTime=end_date, durationStr=self._get_duration(granularity),
                                                     barSizeSetting=self._get_bar_size(granularity), whatToShow=what_to_show, useRTH=True)
        return [{'date': bar.date, 'open': bar.open, 'high': bar.high, 'low': bar.low, 'close': bar.close, 'volume': bar.volume, 
                 'average': bar.average, 'barCount': bar.barCount} for bar in bars]

    # IO --------------------------------------------------------------------
    # Misc ------------------------------------------------------------------
