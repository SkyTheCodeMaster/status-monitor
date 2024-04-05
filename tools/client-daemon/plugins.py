from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  import aiohttp

ALL_PLUGINS = []

def fetch_plugins(addons: str) -> list[Plugin]:
  "addons is csv list of addons, returns list of plugin objects."
  names = addons.split(",")
  plugins = [
    value
    for value in locals().values()
    if issubclass(value, Plugin) and value != Plugin and value.name in names
  ]
  return plugins

class Plugin:
  name: str = "Example Plugin"

  @classmethod
  async def get_data(self, cs: aiohttp.ClientSession) -> dict:
    pass

