import json
from pathlib import Path

class OrdersParser:
    """Parses orders.json configuration file"""

    # LifeCycle -------------------------------------------------------------
    def __init__(self, orders_file='orders.json'):
        self.orders_file = Path(orders_file)

    # Business Logic --------------------------------------------------------
    def get_orders(self):
        """Returns list of order dictionaries from orders.json"""
        with open(self.orders_file, 'r') as f:
            return json.load(f)
