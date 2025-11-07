import asyncio

from ib_async.contract import Index

# Create event loop before importing ib_insync (required for Python 3.14)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from src.configuration.config import Config
from src.file_manager import FileManager
from src.providers.ibkr_client import IBKRClient
from src.providers.saxo_client import SaxoClient
from src.configuration.download_requests_parser import DownloadRequestsParser
from src.data_downloader import DataDownloader
from src.normalization_tracker import NormalizationTracker

async def main():
    """Main entry point with infinite loop for periodic downloads"""
    config = Config()
    file_manager = FileManager(config)
    normalization_trackers = {(
        'ibkr', 'TRADES'): NormalizationTracker(config.processed_data_dir, 'ibkr', 'TRADES'), 
        ('ibkr', 'BID_ASK'): NormalizationTracker(config.processed_data_dir, 'ibkr', 'BID_ASK'), 
        ('saxo', 'TRADES'): NormalizationTracker(config.processed_data_dir, 'saxo', 'TRADES'), 
        ('saxo', 'BID_ASK'): NormalizationTracker(config.processed_data_dir, 'saxo', 'BID_ASK')}
    ibkr_client = IBKRClient(config)
    saxo_client = SaxoClient(config)
    provider_clients = {'ibkr': ibkr_client, 'saxo': saxo_client}
    download_requests_parser = DownloadRequestsParser(config)
    downloader = DataDownloader(provider_clients, file_manager, download_requests_parser, config, normalization_trackers)

    if not config.client_id and not config.saxo_client_id:
        raise ValueError("At least one provider client_id must be configured")

    print("Attempting to connect to providers...")
    if config.client_id:
        while True:
            try:
                await ibkr_client.connect()
                print("Connected to IBKR successfully")
                break
            except Exception as e:
                error_msg = str(e) if str(e) else "Connection failed"
                print(f"\nFailed to connect to IBKR: {error_msg}")
                print(f"Retrying in {config.connection_retry_seconds} seconds...\n")
                await asyncio.sleep(config.connection_retry_seconds)
    if config.saxo_client_id and config.saxo_client_secret:
        try:
            await saxo_client.connect()
            print("Connected to Saxo successfully")
        except Exception as e:
            print(f"Failed to connect to Saxo: {e}")

    while True:
        try:
            print(f"Starting download cycle")
            await downloader.run()
            print(f"Download cycle completed, sleeping for {config.download_cycle_seconds} seconds(s)")
            await asyncio.sleep(config.download_cycle_seconds)
        except Exception as e:
            print(f"Error during download: {e}")
            await asyncio.sleep(config.error_retry_seconds)

if __name__ == '__main__':
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
