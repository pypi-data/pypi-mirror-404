from typing_extensions import NotRequired
from dataclasses import dataclass
from decimal import Decimal

from ...core import AuthEndpoint, validator, TypedDict

class CapitalConfigNetwork(TypedDict):
  network: str
  """Network name"""
  coin: str
  """Coin symbol"""
  withdrawIntegerMultiple: Decimal
  """Withdraw amount must be a multiple of this"""
  isDefault: bool
  """Whether this is the default network"""
  depositEnable: bool
  """Deposit enabled"""
  withdrawEnable: bool
  """Withdraw enabled"""
  depositDesc: NotRequired[str]
  """Deposit description (shown when depositEnable is false)"""
  withdrawDesc: NotRequired[str]
  """Withdraw description (shown when withdrawEnable is false)"""
  specialTips: NotRequired[str]
  """Special tips"""
  specialWithdrawTips: NotRequired[str]
  """Special withdraw tips"""
  name: str
  """Display name"""
  resetAddressStatus: bool
  """Reset address status"""
  addressRegex: str
  """Address validation regex"""
  memoRegex: str
  """Memo validation regex"""
  withdrawFee: Decimal
  """Withdraw fee"""
  withdrawMin: Decimal
  """Minimum withdraw amount"""
  withdrawMax: Decimal
  """Maximum withdraw amount"""
  withdrawInternalMin: NotRequired[Decimal]
  """Minimum internal transfer amount"""
  depositDust: NotRequired[Decimal]
  """Deposit dust threshold"""
  minConfirm: int
  """Min confirmations for balance"""
  unLockConfirm: int
  """Confirmations for balance unlock"""
  sameAddress: bool
  """Obsoleted; prefer withdrawTag"""
  withdrawTag: bool
  """Whether memo is required to withdraw"""
  estimatedArrivalTime: int
  """Estimated arrival time"""
  busy: bool
  """Network busy"""
  contractAddressUrl: NotRequired[str]
  """Contract address URL"""
  contractAddress: NotRequired[str]
  """Contract address"""
  denomination: NotRequired[int]
  """Denomination (e.g. 1 1MBABYDOGE = denomination BABYDOGE)"""

class CapitalConfigCoin(TypedDict):
  coin: str
  """Coin symbol"""
  depositAllEnable: bool
  """Deposit enabled for all networks"""
  withdrawAllEnable: bool
  """Withdraw enabled for all networks"""
  name: str
  """Display name"""
  free: Decimal
  """Free balance"""
  locked: Decimal
  """Locked balance"""
  freeze: Decimal
  """Frozen balance"""
  withdrawing: Decimal
  """Amount in withdrawal"""
  ipoing: Decimal
  """Amount in IPO"""
  ipoable: Decimal
  """IPOable amount"""
  storage: Decimal
  """Storage balance"""
  isLegalMoney: bool
  """Whether legal tender"""
  trading: bool
  """Trading enabled"""
  networkList: list[CapitalConfigNetwork]
  """Networks for this coin"""

validate_response = validator(list[CapitalConfigCoin])

@dataclass
class Coins(AuthEndpoint):
  async def coins(
    self,
    *,
    recv_window: int | None = None,
    validate: bool | None = None
  ):
    """Get information of coins (available for deposit and withdraw) for user.

    - `recv_window`: Request receive window (milliseconds)
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Binance API docs](https://developers.binance.com/docs/wallet/capital)
    """
    params: dict = {}
    if recv_window is not None:
      params['recvWindow'] = recv_window
    r = await self.authed_request('GET', '/sapi/v1/capital/config/getall', params=params)
    return self.output(r.text, validate_response, validate=validate)
