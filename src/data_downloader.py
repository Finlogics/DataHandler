from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import asyncio

from src.configuration.config import Config
from src.configuration.orders_parser import OrdersParser
from src.file_manager import FileManager
from src.normalization_tracker import NormalizationTracker
from src.providers.ibkr_client import IBKRClient

class DataDownloader:
    """Orchestrates data download from IBKR"""

    # LifeCycle -------------------------------------------------------------
    def __init__(self, ibkr_client:IBKRClient, file_manager:FileManager, orders_parser:OrdersParser, config:Config, normalization_tracker:NormalizationTracker):
        self.ibkr_client = ibkr_client
        self.file_manager = file_manager
        self.orders_parser = orders_parser
        self.config = config
        self.normalization_tracker = normalization_tracker

    # Business Logic --------------------------------------------------------
    def _generate_date_ranges(self, granularity, starting_date):
        """Generates list of date strings for files to download"""
        start = datetime.strptime(starting_date, '%Y-%m-%d')
        yesterday = datetime.now() - timedelta(days=1)
        dates = []
        if self._is_major_granularity(granularity):
            year = start.year
            while year <= yesterday.year:
                dates.append(str(year))
                year += 1
        else:
            current = start
            while current <= yesterday:
                dates.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)
        return dates

    def _should_download(self, file_path):
        """Returns True if file needs to be downloaded"""
        status = self.file_manager.get_file_status(file_path)
        return status != 'completed'

    def _is_major_granularity(self, granularity):
        """Returns True if granularity is 1D or larger"""
        return granularity.endswith('D') or granularity.endswith('W')

    async def download_order(self, order):
        """Downloads all data for a single order"""
        currency = order.get('currency', 'USD')
        exchange = order.get('exchange', 'SMART')
        contract_type = order.get('type', 'Stock')
        for ticker in order['tickers']:
            for granularity in order['granularities']:
                dates = self._generate_date_ranges(granularity, order['starting_date'])[::-1]
                for date_str in dates:
                    raw_path = self.file_manager.get_file_path(ticker, granularity, date_str, True)
                    if not self._should_download(raw_path):
                        continue
                    try:
                        end_date = self._get_end_date(granularity, date_str)
                        data = await self.ibkr_client.fetch_historical_data(ticker, granularity, end_date, currency, exchange, contract_type)

                        self.file_manager.mark_status(raw_path, 'incomplete')
                        self.file_manager.write_csv(raw_path, data, True)

                        if not self.normalization_tracker.has_entry(ticker, granularity):
                            self.normalization_tracker.add_entry(ticker, granularity, data)
                        
                        normalized = self.normalization_tracker.normalize_value(ticker, granularity, data)
                        processed_path = self.file_manager.get_file_path(ticker, granularity, date_str, False)
                        self.file_manager.write_csv(processed_path, normalized, False)
                        print(f"SUCCESS: {raw_path.name} - completed")
                    except Exception as e:
                        self.file_manager.mark_status(raw_path, 'corrupted')
                        print(f"FAILED: {raw_path.name} - corrupted - {e}")
                    await asyncio.sleep(self.config.request_delay_seconds)

    def _get_end_date(self, granularity, date_str):
        """Returns end date for IBKR request"""
        if self._is_major_granularity(granularity):
            return f"{date_str}1231 23:59:59"
        return f"{date_str.replace('-', '')} 23:59:59"

    async def run(self):
        """Runs download for all orders"""
        orders = self.orders_parser.get_orders()
        for order in orders:
            await self.download_order(order)

    # IO --------------------------------------------------------------------
    # Misc ------------------------------------------------------------------
