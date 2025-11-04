# DataHandler

**⚠️ PRIVATE PACKAGE - DO NOT PUBLISH TO PYPI**

Market data downloader using Interactive Brokers API. Downloads historical price data for configured tickers and saves to local storage.

## Requirements

- Python 3.8+
- Interactive Brokers Gateway or TWS (must be installed and running separately)
- Active IBKR account with market data subscriptions

## Installation

```bash
# Clone the repository
git clone https://github.com/Finlogics/DataHandler.git

# Navigate to project directory
cd DataHandler

# Create conda environment named "down" with Python 3.14
conda create -n down python=3.14

# Activate the conda environment
conda activate down

# Install package in editable mode (recommended for development)
pip install -e .
```

**Note:** Ensure IB Gateway or TWS is installed and running before using this application. The application expects API access on port 4002 by default (configurable in config/config.ini).

## Configuration

### config/config.ini
Configure IBKR connection, file paths, and timing parameters:
- `[IBKR]`: Gateway/TWS connection settings (host, port, client_id)
- `[Paths]`: Data directory and orders file location
- `[Timing]`: Retry intervals and download cycle frequency

### config/orders.json
Define download orders as JSON array with:
- `name`: Order identifier
- `starting_date`: Historical data start date (YYYY-MM-DD)
- `granularities`: Time intervals (e.g., "1D", "1M")
- `tickers`: List of stock symbols

## Usage

```bash
python main.py
```

The application connects to IBKR Gateway, processes orders from orders.json, and downloads data periodically. Data is saved to the configured raw_data_dir.

## Project Structure

```
DataHandler/
├── config/           # Configuration files
├── raw-data/         # Downloaded market data
├── src/
│   ├── configuration/  # Config and order parsing
│   ├── providers/      # IBKR client implementation
│   ├── data_downloader.py
│   └── file_manager.py
└── main.py          # Entry point
```

## License

See LICENSE file.