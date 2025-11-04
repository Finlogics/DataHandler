import json
from pathlib import Path


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
                self.data[key] = {'open': entry['open'], 'volume': entry['volume'], 'barCount': entry['barCount']}

    # Business Logic
    # -------------------------------------------------------------------------

    def normalize_value(self, ticker: str, granularity: str, values: list[dict]) -> float:
        """Normalize a value based on stored normalization data."""
        key = (ticker, granularity)
        norm_data = self.data[key]

        ret=[]
        for value in values:
            normalized={'data': value['date']}
            normalized['open'] = value['open'] / norm_data['open'] * 2 - 1
            normalized['high'] = value['high'] / norm_data['open'] * 2 - 1
            normalized['low'] = value['low'] / norm_data['open'] * 2 - 1
            normalized['close'] = value['close'] / norm_data['open'] * 2 - 1
            normalized['average'] = value['average'] / norm_data['open'] * 2 - 1
            normalized['volume'] = value['volume'] / norm_data['volume'] * 2 - 1
            normalized['barCount'] = value['barCount'] / norm_data['barCount'] * 2 - 1
            ret.append(normalized)
        return ret
    
    def unnormalize_value(self, ticker: str, granularity: str, values: list[dict]) -> float:
        """Unnormalize a value based on stored normalization data."""
        key = (ticker, granularity)
        norm_data = self.data[key]

        ret=[]
        for value in values:
            unnormalized={'data': value['date']}
            unnormalized['open'] = norm_data['open'] * (value['open'] + 1) / 2
            unnormalized['high'] = norm_data['open'] * (value['high'] + 1) / 2
            unnormalized['low'] = norm_data['open'] * (value['low'] + 1) / 2
            unnormalized['close'] = norm_data['open'] * (value['close'] + 1) / 2
            unnormalized['average'] = norm_data['open'] * (value['average'] + 1) / 2
            unnormalized['volume'] = norm_data['volume'] * (value['volume'] + 1) / 2
            unnormalized['barCount'] = norm_data['barCount'] * (value['barCount'] + 1) / 2  
            ret.append(unnormalized)
        return ret

    def has_entry(self, ticker: str, granularity: str) -> bool:
        """Check if normalization entry exists for ticker-granularity combination."""
        return (ticker, granularity) in self.data

    def add_entry(self, ticker: str, granularity: str, open_val: float, volume: float, bar_count: int):
        """Add normalization entry and save to JSON."""
        self.data[(ticker, granularity)] = {'open': open_val, 'volume': volume, 'barCount': bar_count}
        self._save()
    


    # IO
    # -------------------------------------------------------------------------
    def _save(self):
        """Write in-memory data to JSON file."""
        entries = [{'ticker': k[0], 'granularity': k[1], **v} for k, v in self.data.items()]
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, 'w') as f:
            json.dump(entries, f, indent=2)
