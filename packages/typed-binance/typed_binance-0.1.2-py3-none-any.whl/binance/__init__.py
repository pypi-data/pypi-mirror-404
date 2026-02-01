from binance.core import AuthRouter
from .simple_earn import SimpleEarn
from .wallet import Wallet

class Binance(AuthRouter):
  simple_earn: SimpleEarn
  wallet: Wallet