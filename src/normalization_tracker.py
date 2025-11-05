import json
from pathlib import Path
import pandas as pd


class NormalizationTracker:
    """Tracks normalization values for ticker-granularity combinations."""

    # LifeCycle
    # -------------------------------------------------------------------------
    def __init__(self, file_path: str):
        """Initialize tracker and load existing data from JSON file."""
        self.file_path = Path(file_path)
        self.data = {}
        if not self.file_path.exists():
            with open(self.file_path, 'w') as f:
                json.dump([], f)

        with open(self.file_path, 'r') as f:
            entries = json.load(f)
            for entry in entries:
                key = (entry['ticker'], entry['granularity'])
                self.data[key] = {k: v for k, v in entry.items() if k not in ['ticker', 'granularity']}

    # Business Logic
    # -------------------------------------------------------------------------

    def normalize_value(self, ticker: str, granularity: str, values: list[dict]) -> float:
        """Normalize a value based on stored normalization data."""
        key = (ticker, granularity)
        norm_data = self.data[key]

        ret=[]
        for value in values:
            normalized={'date': value['date']}
            normalized.update({k: value[k] / norm_data[k] * 2 - 1 for k in value.keys() if k!='date'})
            ret.append(normalized)
        return ret

    def unnormalize_value(self, ticker: str, granularity: str, values: list[dict]) -> float:
        """Unnormalize a value based on stored normalization data."""
        key = (ticker, granularity)
        norm_data = self.data[key]

        ret=[]
        for value in values:
            normalized={'date': value['date']}
            normalized.update({k: norm_data[k] * (value[k] + 1) / 2 for k in value.keys() if k!='date'})
            ret.append(normalized)
        return ret

    def has_entry(self, ticker: str, granularity: str) -> bool:
        """Check if normalization entry exists for ticker-granularity combination."""
        return (ticker, granularity) in self.data

    def add_entry(self, ticker: str, granularity: str, bar_data: list[dict]):
        """Add normalization entry and save to JSON."""
        df = pd.DataFrame(bar_data)
        max_values = {col: float(df[col].max()) for col in df.columns if col != 'date'}
        self.data[(ticker, granularity)] = max_values
        self._save()


    # IO
    # -------------------------------------------------------------------------
    def _save(self):
        """Write in-memory data to JSON file."""
        entries = [{'ticker': k[0], 'granularity': k[1], **v} for k, v in self.data.items()]
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, 'w') as f:
            json.dump(entries, f, indent=2)
