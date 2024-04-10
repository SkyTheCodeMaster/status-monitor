from __future__ import annotations

from typing import TYPE_CHECKING, Any
from api.utils.data_classes import ConnectedMachine, Plugin

if TYPE_CHECKING:
  pass

class XmrigPlugin(Plugin, name="xmrig"):
  async def run(self, extras_dict: dict, machine: ConnectedMachine) -> None:
    # Because xmrig is already in the extras dict, we don't need to process it.
    return None

  async def out(self, extras_dict: dict, machine: ConnectedMachine) -> Any:
    return extras_dict["xmrig"]