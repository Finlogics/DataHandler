import configparser
from pathlib import Path

class Config:
    """Application configuration from config.ini"""

    # LifeCycle -------------------------------------------------------------
    def __init__(self, config_file='config/config.ini'):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(config_file)
        self.host = parser.get('IBKR', 'host')
        self.port = parser.getint('IBKR', 'port')
        client_id_str = parser.get('IBKR', 'client_id', fallback='')
        self.client_id = int(client_id_str) if client_id_str else None
        self.saxo_client_id = parser.get('SAXO', 'client_id', fallback='')
        self.saxo_client_secret = parser.get('SAXO', 'client_secret', fallback='')
        self.saxo_redirect_uri = parser.get('SAXO', 'redirect_uri', fallback='http://localhost:5000/callback')
        self.saxo_token_file = parser.get('SAXO', 'token_file', fallback='config/saxo_tokens.json')
        self.processed_data_dir = parser.get('Paths', 'processed_data_dir')
        self.raw_data_dir = parser.get('Paths', 'raw_data_dir')
        self.download_requests_file = parser.get('Paths', 'download_requests_file')
        self.connection_retry_seconds = parser.getint('Timing', 'connection_retry_seconds')
        self.download_cycle_seconds = parser.getint('Timing', 'download_cycle_seconds')
        self.request_delay_seconds = parser.getint('Timing', 'request_delay_seconds')
        self.error_retry_seconds = parser.getint('Timing', 'error_retry_seconds')
