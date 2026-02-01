from binance.core import AuthRouter
from .capital import Capital

class Wallet(AuthRouter):
  capital: Capital
