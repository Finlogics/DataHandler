import asyncio

# Create event loop before importing ib_insync (required for Python 3.14)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from src.config import Config
from src.file_manager import FileManager
from src.ibkr_client import IBKRClient
from src.orders_parser import OrdersParser
from src.data_downloader import DataDownloader

async def main():
    """Main entry point with infinite loop for periodic downloads"""
    config = Config()
    file_manager = FileManager()
    ibkr_client = IBKRClient(config)
    orders_parser = OrdersParser()
    downloader = DataDownloader(ibkr_client, file_manager, orders_parser)

    print("Attempting to connect to IBKR...")
    while True:
        try:
            await ibkr_client.connect()
            print("Connected to IBKR successfully")
            break
        except Exception as e:
            print(f"\nFailed to connect to IBKR: {e}")
            print("Retrying in 30 seconds...\n")
            await asyncio.sleep(30)

    while True:
        try:
            print(f"Starting download cycle")
            await downloader.run()
            print("Download cycle completed, sleeping for 1 hour")
            await asyncio.sleep(3600)
        except Exception as e:
            print(f"Error during download: {e}")
            await asyncio.sleep(60)

if __name__ == '__main__':
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
