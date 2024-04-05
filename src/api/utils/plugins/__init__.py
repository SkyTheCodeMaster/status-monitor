from __future__ import annotations

import importlib
import pathlib
from typing import TYPE_CHECKING

from api.utils.data_classes import Plugin

if TYPE_CHECKING:
  from typing import Any

path = pathlib.Path(__file__)
plugin_files: list[pathlib.Path] = [p for p in path.parent.iterdir() if p.is_file() and p.name != "__init__.py"]
ALL_PLUGINS: dict[str, Plugin] = {}

def get_module(name:str, * ,package=None) -> Any:
  n = importlib.util.resolve_name(name,package)
  spec = importlib.util.find_spec(n)
  lib = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(lib)
  return lib

for plugin_file in plugin_files:
  mod_name = "api.utils.plugins." + plugin_file.name.removesuffix(".py")
  module = get_module(mod_name)
  plugin_names: list[str] = [name for name in dir(module) if getattr(module, name) == type and issubclass(getattr(module, name), Plugin)]
  for plugin_name in plugin_names:
    plugin: Plugin = getattr(module, plugin_name)
    ALL_PLUGINS[plugin.name] = plugin