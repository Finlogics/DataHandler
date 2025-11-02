# DataHandler

Market data downloader using Interactive Brokers API. Downloads historical price data for configured tickers and saves to local storage.

## Requirements

- Python 3.8+
- Interactive Brokers Gateway or TWS
- Active IBKR account with market data subscriptions

## Installation

Complete step-by-step installation guide for a fresh system. Prerequisites: Anaconda/Miniconda, Git, and an active IBKR account with market data subscriptions.

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

# Alternative: Install Python dependencies from requirements.txt
# pip install -r requirements.txt

# Make the gateway setup script executable
chmod +x config/setup-gateway.sh

# Run gateway setup script (use 'paper' for paper trading or 'live' for live trading)
# This installs Java, Xvfb, IB Gateway (v1037), IBC (v3.23.0), and creates systemd service
# Script will prompt for your IBKR username and password
./config/setup-gateway.sh paper

# Start the IBKR Gateway systemd service
sudo systemctl start ibgateway

# Check gateway status (takes 30-60 seconds to fully start)
sudo systemctl status ibgateway

# Run the application to verify installation
# Downloaded data will be saved to raw-data/ directory
python main.py
```

### Gateway Service Management

The IBKR Gateway runs as a systemd service and will auto-start on system reboot.

Common service commands:
```bash
sudo systemctl start ibgateway    # Start the gateway
sudo systemctl stop ibgateway     # Stop the gateway
sudo systemctl restart ibgateway  # Restart the gateway
sudo systemctl status ibgateway   # Check gateway status
sudo systemctl disable ibgateway  # Disable auto-start on boot
sudo systemctl enable ibgateway   # Enable auto-start on boot
```

### Troubleshooting

**Connection Issues:**
- Verify gateway is running: `sudo systemctl status ibgateway`
- Check gateway logs: `journalctl -u ibgateway -f`
- Ensure API port 4002 is not blocked by firewall
- Verify IBKR credentials are correct in `~/ibc/config.ini`

**Data Download Issues:**
- Confirm you have active market data subscriptions in your IBKR account
- Check that tickers in orders.json are valid symbols
- Verify starting_date is not too far in the past (IBKR has historical data limits)

**Python Environment Issues:**
- Ensure conda environment is activated: `conda activate down`
- Reinstall dependencies: `pip install --force-reinstall -r requirements.txt`

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

### Setup IBKR Gateway
```bash
./config/setup-gateway.sh
```

### Run Data Downloader
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