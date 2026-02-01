from binance.core import AuthRouter
from .flexible import Flexible
from .fixed import Fixed

class SimpleEarn(AuthRouter):
  flexible: Flexible
  fixed: Fixed