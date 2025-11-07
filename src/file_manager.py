import os
import pandas as pd
from pathlib import Path

class FileManager:
    """Manages CSV files and flag files for data downloads"""

    # LifeCycle -------------------------------------------------------------
    def __init__(self, config):
        self.base_dir = Path(config.processed_data_dir)
        self.raw_data_dir = Path(config.raw_data_dir)

    # Business Logic --------------------------------------------------------
    def get_file_status(self, file_path):
        """Returns 'completed', 'corrupted', 'incomplete', 'not_available', or None"""
        path = Path(file_path)
        if path.with_suffix('.cpl').exists():
            return 'completed'
        if path.with_suffix('.crp').exists():
            return 'corrupted'
        if path.with_suffix('.icl').exists():
            return 'incomplete'
        if path.with_suffix('.na').exists():
            return 'not_available'
        return None

    def mark_status(self, file_path, status):
        """Marks file with status flag (completed/corrupted/incomplete)"""
        path = Path(file_path)
        for ext in ['.cpl', '.crp', '.icl', '.na']:
            path.with_suffix(ext).unlink(missing_ok=True)
        if status == 'completed':
            path.with_suffix('.cpl').touch()
        elif status == 'corrupted':
            path.with_suffix('.crp').touch()
        elif status == 'incomplete':
            path.with_suffix('.icl').touch()
        elif status == 'not_available':
            path.with_suffix('.na').touch()

    def get_file_path(self, ticker, granularity, date_str, is_raw: bool, what_to_show: str):
        """Returns path for CSV file based on whatToShow and granularity"""
        granularity_dir = (self.raw_data_dir if is_raw else self.base_dir) / what_to_show / granularity
        granularity_dir.mkdir(parents=True, exist_ok=True)
        return granularity_dir / f"{ticker}-{date_str}.csv"


    # IO --------------------------------------------------------------------
    def write_csv(self, file_path, data, is_raw:bool):
        """Writes DataFrame to CSV and marks as complete"""
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        if is_raw:
            self.mark_status(file_path, 'completed')


