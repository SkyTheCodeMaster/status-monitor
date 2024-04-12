from __future__ import annotations

import importlib
import importlib.util
import pathlib
import inspect
from typing import TYPE_CHECKING

from api.utils.data_classes import Plugin

if TYPE_CHECKING:
  from typing import Any
  from asyncpg import Pool

path = pathlib.Path(__file__)
plugin_files: list[pathlib.Path] = [
  p for p in path.parent.iterdir() if p.is_file() and p.name != "__init__.py"
]
ALL_PLUGINS: dict[str, Plugin] = {}


def get_module(name: str, *, package=None) -> Any:
  n = importlib.util.resolve_name(name, package)
  spec = importlib.util.find_spec(n)
  lib = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(lib)
  return lib


for plugin_file in plugin_files:
  mod_name = "api.utils.plugins." + plugin_file.name.removesuffix(".py")
  module = get_module(mod_name)
  print(f"[PLUGINS] Searching {mod_name} @ {plugin_file}")
  plugins: list[Plugin] = [
    getattr(module, name)
    for name in dir(module)
    if inspect.isclass(getattr(module, name))
    and issubclass(getattr(module, name), Plugin)
    and getattr(module, name) != Plugin
  ]
  for plugin in plugins:
    ALL_PLUGINS[plugin.name] = plugin

async def fetch_plugins(names: list[str], pool: Pool) -> list[Plugin]:
  out = []
  for k,v in ALL_PLUGINS.items():
    if k in names:
      out.append(v(pool))
  out.sort(key=lambda p: p.priority, reverse=True)
  return out

print("[PLUGINS] Loaded server plugins:", ALL_PLUGINS.keys())
