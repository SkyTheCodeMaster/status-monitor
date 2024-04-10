from __future__ import annotations

import logging
import inspect
from typing import TYPE_CHECKING

from aiohttp import ClientSession

if TYPE_CHECKING:
  import aiohttp

LOG = logging.getLogger(__name__)


def fetch_plugins(addons: str) -> list[Plugin]:
  "addons is csv list of addons, returns list of plugin objects."
  names = addons.split(",")
  plugins = [
    value
    for value in globals().values()
    if inspect.isclass(value)
    and issubclass(value, Plugin)
    and value != Plugin
    and value.name in names
  ]
  return plugins


class Plugin:
  name: str = "Example Plugin"

  @classmethod
  async def get_data(self, cs: aiohttp.ClientSession) -> dict:
    pass


class XmrigPlugin(Plugin):
  name: str = "xmrig"

  @classmethod
  async def get_data(self, cs: ClientSession) -> dict | None:
    data: dict = None
    try:
      async with cs.get("http://127.0.0.1:5000/2/summary") as resp:
        data = await resp.json()
    except Exception:
      LOG.exception("Failed to gather data from xmrig API!")
      return None
    out = {}

    out["hashrate"] = {
      "current": data["hashrate"]["total"][0],
      "1m": data["hashrate"]["total"][1],
      "15m": data["hashrate"]["total"][2],
      "peak": data["hashrate"]["highest"],
    }

    out["version"] = data["version"]
    out["worker_id"] = data["worker_id"]
    out["uptime"] = data["uptime"]

    out["shares"] = {
      "total": data["results"]["shares_total"],
      "good": data["results"]["shares_good"],
      "avg_time_ms": data["results"]["avg_time_ms"],
      "hashes_total": data["results"]["hashes_total"],
    }

    return out
