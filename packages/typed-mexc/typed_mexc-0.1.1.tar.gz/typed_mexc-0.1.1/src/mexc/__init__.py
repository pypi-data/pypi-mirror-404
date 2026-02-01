from dataclasses import dataclass as _dataclass
import asyncio as _asyncio

from .spot import Spot
from .futures import Futures
from . import spot, futures, core

@_dataclass
class MEXC:
  spot: Spot
  futures: Futures

  @classmethod
  def new(
    cls, api_key: str | None = None, api_secret: str | None = None, *,
    validate: bool = True,
  ):
    return cls(
      spot=Spot.new(api_key=api_key, api_secret=api_secret, default_validate=validate),
      futures=Futures.new(api_key=api_key, api_secret=api_secret, default_validate=validate),
    )
  
  async def __aenter__(self):
    await _asyncio.gather(
      self.spot.__aenter__(),
      self.futures.__aenter__(),
    )
    return self
  
  async def __aexit__(self, exc_type, exc_value, traceback):
    await _asyncio.gather(
      self.spot.__aexit__(exc_type, exc_value, traceback),
      self.futures.__aexit__(exc_type, exc_value, traceback),
    )