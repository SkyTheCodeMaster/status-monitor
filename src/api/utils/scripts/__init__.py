from __future__ import annotations

import importlib
import importlib.util
import pathlib
import inspect
from typing import TYPE_CHECKING

from api.utils.data_classes import Script

if TYPE_CHECKING:
  from typing import Any
  from utils.extra_request import Application

path = pathlib.Path(__file__)
plugin_files: list[pathlib.Path] = [
  p for p in path.parent.iterdir() if p.is_file() and p.name != "__init__.py"
]
ALL_SCRIPTS: dict[str, Script] = {}


def get_module(name: str, *, package=None) -> Any:
  n = importlib.util.resolve_name(name, package)
  spec = importlib.util.find_spec(n)
  lib = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(lib)
  return lib


for plugin_file in plugin_files:
  mod_name = "api.utils.scripts." + plugin_file.name.removesuffix(".py")
  module = get_module(mod_name)
  print(f"[SCRIPTS] Searching {mod_name} @ {plugin_file}")
  plugins: list[Script] = [
    getattr(module, name)
    for name in dir(module)
    if inspect.isclass(getattr(module, name))
    and issubclass(getattr(module, name), Script)
    and getattr(module, name) != Script
  ]
  for plugin in plugins:
    ALL_SCRIPTS[plugin.name] = plugin

async def fetch_scripts(names: list[str], app: Application) -> list[Script]:
  out = []

  for k,v in ALL_SCRIPTS.items():
    if not isinstance(v, Script):
      ALL_SCRIPTS[k] = v(app)
    if k in names:
      out.append(v)
  out.sort(key=lambda p: p.priority, reverse=True)
  return out

print("[SCRIPTS] Loaded server scripts:", ALL_SCRIPTS.keys())
