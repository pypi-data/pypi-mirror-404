from typing_extensions import TypeVar, TypedDict
import os
from dataclasses import dataclass, field
import orjson
from pydantic import TypeAdapter, ValidationError

from .http import HttpMixin, AuthHttpMixin, AuthHttpClient
from .validation import ValidationMixin, validator
from .exc import ApiError

T = TypeVar('T')

BINANCE_REST_URL = 'https://api.binance.com'

class ErrorResponse(TypedDict):
  code: int
  msg: str

error_adapter = TypeAdapter(ErrorResponse)

def is_err(response):
  try:
    error_adapter.validate_json(response, extra='forbid')
    return True
  except ValidationError:
    return False


@dataclass
class BaseMixin(ValidationMixin):
  base_url: str = field(kw_only=True, default=BINANCE_REST_URL)

  def output(self, data: str | bytes, validator: validator[T], validate: bool | None) -> T:
    if is_err(data):
      raise ApiError(data)
    return validator(data) if self.validate(validate) else orjson.loads(data)

@dataclass
class Endpoint(BaseMixin, HttpMixin):
  ...

@dataclass
class AuthEndpoint(Endpoint, AuthHttpMixin):
  base_url: str = field(kw_only=True, default=BINANCE_REST_URL)

  @classmethod
  def new(
    cls, api_key: str | None = None, api_secret: str | None = None, *,
    base_url: str = BINANCE_REST_URL, validate: bool = True,
  ):
    if api_key is None:
      api_key = os.environ['BINANCE_API_KEY']
    if api_secret is None:
      api_secret = os.environ['BINANCE_API_SECRET']
    client = AuthHttpClient(api_key=api_key, api_secret=api_secret)
    return cls(base_url=base_url, http=client, default_validate=validate)

@dataclass
class Router(Endpoint):
  def __post_init__(self):
    for field, cls in self.__annotations__.items():
      if issubclass(cls, Endpoint) or issubclass(cls, Router):
        setattr(self, field, cls(base_url=self.base_url, http=self.http, default_validate=self.default_validate))

@dataclass
class AuthRouter(Router, AuthEndpoint):
  ...