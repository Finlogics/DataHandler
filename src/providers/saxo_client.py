import aiohttp
import asyncio
import json
import base64
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from aiohttp import web
from urllib.parse import urlencode
from src.providers.base_client import ProviderClient


class SaxoClient(ProviderClient):
    """Wrapper for Saxo OpenAPI to fetch historical market data"""

    # LifeCycle -------------------------------------------------------------
    def __init__(self, config):
        self.config = config
        self.session = None
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.base_url = 'https://gateway.saxobank.com/sim/openapi'
        self.auth_url = 'https://sim.logonvalidation.net/authorize'
        self.token_url = 'https://sim.logonvalidation.net/token'
        self.auth_code = None

    async def connect(self):
        """Connects to Saxo OpenAPI and authenticates"""
        self.session = aiohttp.ClientSession()
        await self._authenticate()
        print(f"Saxo Client connected")

    async def disconnect(self):
        """Disconnects from Saxo OpenAPI"""
        if self.session:
            await self.session.close()
            self.session = None

    async def _authenticate(self):
        """Authenticates with Saxo OpenAPI using OAuth2 authorization code flow"""
        if self._load_tokens():
            if await self._refresh_access_token():
                return
        await self._do_authorization_flow()

    async def _do_authorization_flow(self):
        """Performs OAuth2 authorization code flow"""
        import secrets
        state = secrets.token_urlsafe(32)
        params = {'response_type': 'code', 'client_id': self.config.saxo_client_id, 'redirect_uri': self.config.saxo_redirect_uri, 'state': state}
        auth_request_url = f"{self.auth_url}?{urlencode(params)}"
        print(f"Opening browser for Saxo authentication...")
        print(f"If browser doesn't open, visit: {auth_request_url}")
        webbrowser.open(auth_request_url)
        await self._start_callback_server(state)
        await self._exchange_code_for_token()

    async def _start_callback_server(self, expected_state: str):
        """Starts local HTTP server to receive OAuth callback"""
        app = web.Application()
        routes = web.RouteTableDef()
        @routes.get('/callback')
        async def callback(request):
            code = request.query.get('code')
            state = request.query.get('state')
            if state != expected_state:
                return web.Response(text='Invalid state parameter', status=400)
            self.auth_code = code
            return web.Response(text='Authentication successful! You can close this window.')
        app.add_routes(routes)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 5000)
        await site.start()
        while not self.auth_code:
            await asyncio.sleep(0.1)
        await runner.cleanup()

    async def _exchange_code_for_token(self):
        """Exchanges authorization code for access token"""
        auth_header = base64.b64encode(f"{self.config.saxo_client_id}:{self.config.saxo_client_secret}".encode()).decode()
        headers = {'Authorization': f'Basic {auth_header}', 'Content-Type': 'application/x-www-form-urlencoded'}
        data = {'grant_type': 'authorization_code', 'code': self.auth_code, 'redirect_uri': self.config.saxo_redirect_uri}
        async with self.session.post(self.token_url, headers=headers, data=data) as response:
            if response.status == 200:
                tokens = await response.json()
                self.access_token = tokens['access_token']
                self.refresh_token = tokens['refresh_token']
                self.token_expiry = datetime.now() + timedelta(seconds=tokens['expires_in'])
                self._save_tokens()
            else:
                raise Exception(f"Token exchange failed: {response.status}")

    async def _refresh_access_token(self) -> bool:
        """Refreshes access token using refresh token"""
        if not self.refresh_token:
            return False
        auth_header = base64.b64encode(f"{self.config.saxo_client_id}:{self.config.saxo_client_secret}".encode()).decode()
        headers = {'Authorization': f'Basic {auth_header}', 'Content-Type': 'application/x-www-form-urlencoded'}
        data = {'grant_type': 'refresh_token', 'refresh_token': self.refresh_token, 'redirect_uri': self.config.saxo_redirect_uri}
        async with self.session.post(self.token_url, headers=headers, data=data) as response:
            if response.status == 200:
                tokens = await response.json()
                self.access_token = tokens['access_token']
                self.refresh_token = tokens['refresh_token']
                self.token_expiry = datetime.now() + timedelta(seconds=tokens['expires_in'])
                self._save_tokens()
                return True
            return False

    # Business Logic --------------------------------------------------------
    def _get_horizon_minutes(self, granularity: str) -> int:
        """Maps granularity to Saxo horizon in minutes"""
        mapping = {'1S': 0, '5S': 0, '15S': 0, '30S': 0, '1M': 1, '5M': 5, '15M': 15, '30M': 30, '1H': 60, '1D': 1440, '1W': 10080}
        return mapping.get(granularity, 1440)

    def _map_asset_type(self, contract_type: str) -> str:
        """Maps contract type to Saxo AssetType"""
        mapping = {'Stock': 'Stock', 'Index': 'StockIndex', 'CFD': 'CfdOnIndex'}
        return mapping.get(contract_type, 'Stock')

    async def fetch_historical_data(self, ticker: str, granularity: str, end_date: str, currency: str = 'USD', exchange: str = 'SMART', contract_type: str = 'Stock', what_to_show: str = 'TRADES') -> list[dict]:
        """Fetches historical data for ticker at granularity ending at end_date"""
        horizon = self._get_horizon_minutes(granularity)
        asset_type = self._map_asset_type(contract_type)
        uic = await self._lookup_uic(ticker, asset_type)
        if not uic:
            return []
        url = f"{self.base_url}/chart/v1/charts"
        params = {'Uic': uic, 'AssetType': asset_type, 'Horizon': horizon, 'Count': 1200}
        headers = {'Authorization': f'Bearer {self.access_token}'}
        async with self.session.get(url, params=params, headers=headers) as response:
            if response.status != 200:
                return []
            data = await response.json()
            return self._convert_saxo_data(data, what_to_show)

    async def _lookup_uic(self, ticker: str, asset_type: str) -> int:
        """Looks up UIC for ticker (placeholder - implement actual lookup)"""
        return None

    def _convert_saxo_data(self, saxo_data: dict, what_to_show: str) -> list[dict]:
        """Converts Saxo OHLC format to IBKR-compatible format"""
        if 'Data' not in saxo_data:
            return []
        result = []
        for bar in saxo_data['Data']:
            if what_to_show == 'TRADES':
                converted = {'date': datetime.fromisoformat(bar['Time'].replace('Z', '+00:00')), 'open': (bar['OpenBid'] + bar['OpenAsk']) / 2, 'high': (bar['HighBid'] + bar['HighAsk']) / 2, 'low': (bar['LowBid'] + bar['LowAsk']) / 2, 'close': (bar['CloseBid'] + bar['CloseAsk']) / 2, 'volume': 0, 'average': (bar['CloseBid'] + bar['CloseAsk']) / 2, 'barCount': 0}
            else:
                converted = {'date': datetime.fromisoformat(bar['Time'].replace('Z', '+00:00')), 'open': bar['OpenBid'], 'high': bar['HighBid'], 'low': bar['LowBid'], 'close': bar['CloseBid'], 'volume': 0, 'average': bar['CloseBid'], 'barCount': 0}
            result.append(converted)
        return result

    # IO --------------------------------------------------------------------
    def _load_tokens(self) -> bool:
        """Loads tokens from file if they exist"""
        token_file = Path(self.config.saxo_token_file)
        if not token_file.exists():
            return False
        with open(token_file, 'r') as f:
            tokens = json.load(f)
            self.access_token = tokens.get('access_token')
            self.refresh_token = tokens.get('refresh_token')
            expiry_str = tokens.get('token_expiry')
            if expiry_str:
                self.token_expiry = datetime.fromisoformat(expiry_str)
            return True

    def _save_tokens(self):
        """Saves tokens to file"""
        token_file = Path(self.config.saxo_token_file)
        token_file.parent.mkdir(parents=True, exist_ok=True)
        tokens = {'access_token': self.access_token, 'refresh_token': self.refresh_token, 'token_expiry': self.token_expiry.isoformat() if self.token_expiry else None}
        with open(token_file, 'w') as f:
            json.dump(tokens, f)

    # Misc ------------------------------------------------------------------
