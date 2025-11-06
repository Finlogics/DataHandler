import json
from pathlib import Path

class DownloadRequestsParser:
    """Parses download_requests.json configuration file"""

    # LifeCycle -------------------------------------------------------------
    def __init__(self, config):
        self.download_requests_file = Path(config.download_requests_file)

    # Business Logic --------------------------------------------------------
    def get_download_requests(self):
        """Returns list of download request dictionaries from download_requests.json"""
        with open(self.download_requests_file, 'r') as f:
            return json.load(f)
