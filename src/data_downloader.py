from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import asyncio

from src.configuration.config import Config
from src.configuration.download_requests_parser import DownloadRequestsParser
from src.file_manager import FileManager
from src.normalization_tracker import NormalizationTracker
from src.providers.base_client import ProviderClient

class DataDownloader:
    """Orchestrates data download from multiple providers"""

    # LifeCycle -------------------------------------------------------------
    def __init__(self, provider_clients: dict[str, ProviderClient], file_manager: FileManager, download_requests_parser: DownloadRequestsParser, config: Config, normalization_trackers: dict[tuple[str, str], NormalizationTracker]):
        self.provider_clients = provider_clients
        self.file_manager = file_manager
        self.download_requests_parser = download_requests_parser
        self.config = config
        self.normalization_trackers = normalization_trackers

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
        return status != 'completed' and status!= 'not_available'

    def _is_major_granularity(self, granularity):
        """Returns True if granularity is 1D or larger"""
        return granularity.endswith('D') or granularity.endswith('W')

    async def download_request(self, download_request):
        """Downloads all data for a single download request"""
        currency = download_request.get('currency', 'USD')
        exchange = download_request.get('exchange', 'SMART')
        contract_type = download_request.get('type', 'Stock')
        what_to_show = download_request.get('whatToShow', 'TRADES')
        provider = download_request.get('provider', 'ibkr')
        client = self.provider_clients[provider]
        normalization_tracker = self.normalization_trackers[(provider, what_to_show)]
        for ticker in download_request['tickers']:
            for granularity in download_request['granularities']:
                dates = self._generate_date_ranges(granularity, download_request['starting_date'])[::-1]
                for date_str in dates:
                    raw_path = self.file_manager.get_file_path(ticker, granularity, date_str, True, what_to_show, provider)
                    if not self._should_download(raw_path):
                        continue
                    try:
                        end_date = self._get_end_date(granularity, date_str)
                        data = await client.fetch_historical_data(ticker, granularity, end_date, currency, exchange, contract_type, what_to_show)
                        if not data:
                            self.file_manager.mark_status(raw_path, 'not_available')
                            print(f"SKIPPED: {raw_path.name} - no data")
                            continue

                        self.file_manager.mark_status(raw_path, 'incomplete')
                        self.file_manager.write_csv(raw_path, data, True)

                        if not normalization_tracker.has_entry(ticker, granularity):
                            normalization_tracker.add_entry(ticker, granularity, data)

                        normalized = normalization_tracker.normalize_value(ticker, granularity, data)
                        processed_path = self.file_manager.get_file_path(ticker, granularity, date_str, False, what_to_show, provider)
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
        """Runs download for all download requests"""
        download_requests = self.download_requests_parser.get_download_requests()
        for download_request in download_requests:
            await self.download_request(download_request)

    # IO --------------------------------------------------------------------
    # Misc ------------------------------------------------------------------
