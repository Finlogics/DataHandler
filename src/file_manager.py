import os
import pandas as pd
from pathlib import Path

class FileManager:
    """Manages CSV files and flag files for data downloads"""

    # LifeCycle -------------------------------------------------------------
    def __init__(self, config):
        self.base_dir = Path(config.raw_data_dir)

    # Business Logic --------------------------------------------------------
    def get_file_status(self, file_path):
        """Returns 'completed', 'corrupted', 'incomplete', or None"""
        path = Path(file_path)
        if path.with_suffix('.cpl').exists():
            return 'completed'
        if path.with_suffix('.crp').exists():
            return 'corrupted'
        if path.with_suffix('.icl').exists():
            return 'incomplete'
        return None

    def mark_status(self, file_path, status):
        """Marks file with status flag (completed/corrupted/incomplete)"""
        path = Path(file_path)
        for ext in ['.cpl', '.crp', '.icl']:
            path.with_suffix(ext).unlink(missing_ok=True)
        if status == 'completed':
            path.with_suffix('.cpl').touch()
        elif status == 'corrupted':
            path.with_suffix('.crp').touch()
        elif status == 'incomplete':
            path.with_suffix('.icl').touch()

    def get_file_path(self, ticker, granularity, date_str):
        """Returns path for CSV file based on granularity"""
        granularity_dir = self.base_dir / granularity
        granularity_dir.mkdir(parents=True, exist_ok=True)
        return granularity_dir / f"{ticker}-{date_str}.csv"

    # IO --------------------------------------------------------------------
    def write_csv(self, file_path, data):
        """Writes DataFrame to CSV and marks as complete"""
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        self.mark_status(file_path, 'completed')

