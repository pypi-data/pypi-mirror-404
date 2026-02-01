from typing_extensions import Literal, NotRequired
from dataclasses import dataclass
from decimal import Decimal

from binance.core import AuthEndpoint, validator, TypedDict

class FlexibleProductRow(TypedDict):
  asset: str
  """Asset name"""
  latestAnnualPercentageRate: Decimal
  """Latest annual percentage rate"""
  tierAnnualPercentageRate: NotRequired[dict[str, float]]
  """Tier annual percentage rates by tier label"""
  airDropPercentageRate: NotRequired[Decimal]
  """Air drop percentage rate"""
  canPurchase: bool
  """Whether the product can be purchased"""
  canRedeem: bool
  """Whether the product can be redeemed"""
  isSoldOut: bool
  """Whether the product is sold out"""
  hot: bool
  """Whether the product is hot"""
  minPurchaseAmount: Decimal
  """Minimum purchase amount"""
  productId: str
  """Product identifier"""
  subscriptionStartTime: int
  """Subscription start time (milliseconds)"""
  status: Literal['PREHEATING', 'PURCHASING', 'END']
  """Product status"""

class FlexibleListResponse(TypedDict):
  rows: list[FlexibleProductRow]
  """List of flexible products"""
  total: int
  """Total count"""

validate_response = validator(FlexibleListResponse)

@dataclass
class FlexibleList(AuthEndpoint):
  async def list(
    self,
    *,
    asset: str | None = None,
    current: int | None = None,
    size: int | None = None,
    recv_window: int | None = None,
    validate: bool | None = None
  ):
    """Get available Simple Earn flexible product list.

    - `asset`: Filter by asset
    - `current`: Currently querying page. Start from 1. Default: 1
    - `size`: Page size. Default: 10, Max: 100
    - `recv_window`: Request receive window (milliseconds)
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Binance API docs](https://developers.binance.com/docs/simple_earn/flexible-locked/account/Get-Simple-Earn-Flexible-Product-List)
    """
    params: dict = {}
    if asset is not None:
      params['asset'] = asset
    if current is not None:
      params['current'] = current
    if size is not None:
      params['size'] = size
    if recv_window is not None:
      params['recvWindow'] = recv_window
    r = await self.authed_request('GET', '/sapi/v1/simple-earn/flexible/list', params=params)
    return self.output(r.text, validate_response, validate=validate)
