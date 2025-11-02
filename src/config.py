class Config:
    """IBKR connection configuration"""

    # LifeCycle -------------------------------------------------------------
    def __init__(self, host='127.0.0.1', port=4002, client_id=1):
        self.host = host
        self.port = port
        self.client_id = client_id
