import asyncio

from ib_insync import Stock

# Create event loop before importing ib_insync (required for Python 3.14)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from src.configuration.config import Config
from src.file_manager import FileManager
from src.providers.ibkr_client import IBKRClient
from src.configuration.orders_parser import OrdersParser
from src.data_downloader import DataDownloader
from src.normalization_tracker import NormalizationTracker

async def main():
    """Main entry point with infinite loop for periodic downloads"""
    config = Config()
    file_manager = FileManager(config)
    normalization_tracker = NormalizationTracker(f'{config.processed_data_dir}/normalization.json')
    ibkr_client = IBKRClient(config)
    orders_parser = OrdersParser(config)
    downloader = DataDownloader(ibkr_client, file_manager, orders_parser, config, normalization_tracker)

    print("Attempting to connect to IBKR...")
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
