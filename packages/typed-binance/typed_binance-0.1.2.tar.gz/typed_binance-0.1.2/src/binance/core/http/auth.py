from typing_extensions import Mapping, Any
from dataclasses import dataclass, field
from urllib.parse import urlencode

import httpx

from .client import HttpClient, HttpMixin
from ..util import timestamp

def sign(query_string: str, *, secret: str) -> str:
  import hmac
  import hashlib
  return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

def encode_query(obj) -> str:
  import json
  return (json.dumps(obj, separators=(',', ':'))) # binance can't cope with spaces, it seems

@dataclass
class AuthHttpClient(HttpClient):
  api_key: str = field(kw_only=True)
  api_secret: str = field(kw_only=True, repr=False)

  def sign(self, query_string: str) -> str:
    return sign(query_string, secret=self.api_secret)
  
  def signed_query(self, params: dict) -> str:
    # fix bools, which would show otherwise as "hello=True" instead of "hello=true"
    fixed_params = [(k, str(v).lower() if isinstance(v, bool) else v) for k, v in params.items()]
    query = urlencode(fixed_params)
    return query + '&signature=' + self.sign(query)

  async def authed_request(
    self, method: str, url: str,
    *,
    content: httpx._types.RequestContent | None = None,
    data: httpx._types.RequestData | None = None,
    files: httpx._types.RequestFiles | None = None,
    json: Any | None = None,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    cookies: httpx._types.CookieTypes | None = None,
    auth: httpx._types.AuthTypes | httpx._client.UseClientDefault | None = httpx.USE_CLIENT_DEFAULT,
    follow_redirects: bool | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    timeout: httpx._types.TimeoutTypes | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    extensions: httpx._types.RequestExtensions | None = None,
  ):
    params = {
      'timestamp': timestamp.now(),
      **(params or {}),
    }
    url += '?' + self.signed_query(params)

    headers = {
      'X-MBX-APIKEY': self.api_key,
      **(headers or {}),
    }
    return await self.request(
      method, url, headers=headers, json=json,
      content=content, data=data, files=files, auth=auth,
      follow_redirects=follow_redirects, cookies=cookies,
      timeout=timeout, extensions=extensions,
    )


@dataclass
class AuthHttpMixin(HttpMixin):
  base_url: str = field(kw_only=True)
  http: AuthHttpClient = field(kw_only=True) # type: ignore

  @classmethod
  def new(cls, api_key: str, api_secret: str, *, base_url: str):
    client = AuthHttpClient(api_key=api_key, api_secret=api_secret)
    return cls(base_url=base_url, http=client)
  
  async def __aenter__(self):
    await self.http.__aenter__()
    return self
  
  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.http.__aexit__(exc_type, exc_value, traceback)

  async def authed_request(
    self, method: str, path: str,
    *,
    content: httpx._types.RequestContent | None = None,
    data: httpx._types.RequestData | None = None,
    files: httpx._types.RequestFiles | None = None,
    json: Any | None = None,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    cookies: httpx._types.CookieTypes | None = None,
    auth: httpx._types.AuthTypes | httpx._client.UseClientDefault | None = httpx.USE_CLIENT_DEFAULT,
    follow_redirects: bool | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    timeout: httpx._types.TimeoutTypes | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    extensions: httpx._types.RequestExtensions | None = None,
  ):
    return await self.http.authed_request(
      method, self.base_url + path, headers=headers, json=json,
      content=content, data=data, files=files, auth=auth,
      follow_redirects=follow_redirects, cookies=cookies,
      timeout=timeout, extensions=extensions, params=params,
    )