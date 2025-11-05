import configparser
from pathlib import Path

class Config:
    """Application configuration from config.ini"""

    # LifeCycle -------------------------------------------------------------
    def __init__(self, config_file='config/config.ini'):
        parser = configparser.ConfigParser()
        parser.read(config_file)
        self.host = parser.get('IBKR', 'host')
        self.port = parser.getint('IBKR', 'port')
        self.client_id = parser.getint('IBKR', 'client_id')
        self.processed_data_dir = parser.get('Paths', 'processed_data_dir')
        self.raw_data_dir = parser.get('Paths', 'raw_data_dir')
        self.orders_file = parser.get('Paths', 'orders_file')
        self.connection_retry_seconds = parser.getint('Timing', 'connection_retry_seconds')
        self.download_cycle_seconds = parser.getint('Timing', 'download_cycle_seconds')
        self.request_delay_seconds = parser.getint('Timing', 'request_delay_seconds')
        self.error_retry_seconds = parser.getint('Timing', 'error_retry_seconds')
