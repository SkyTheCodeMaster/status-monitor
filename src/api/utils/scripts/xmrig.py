from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING

from api.utils.data_classes import Script

if TYPE_CHECKING:
  from api.utils.data_classes import ConnectedMachine, MonitorPacket

DEFAULT_CONFIG = {
  "notify": [
    "warning"
  ],
  "hashrate": 0
}

class XmrigScript(Script, name="xmrig"):
  async def run(self, packet: MonitorPacket, machine: ConnectedMachine) -> None:
    # This script is only run when the machine explicitly calls for it.
    # This adds the warning flag when the hashrate is too low.

    raw = packet.raw

    if "xmrig" not in machine.extra_config:
      # Set in the defaults
      machine.extra_config["xmrig"] = copy.deepcopy(DEFAULT_CONFIG)
      if not await machine.write_extra_config(self.pool):
        self.app.LOG.warning(f"Failed to write default config for {machine.name}!")

    if "xmrig" not in raw["extras"]:
      machine.remove_warning("xmrig")
      return

    if raw["extras"]["xmrig"] == "failed":
      machine.add_warning("xmrig")
      return

    if "xmrig" in machine.extra_config:
      target_hashrate = machine.extra_config["xmrig"]["hashrate"]
      notify = machine.extra_config["xmrig"]["notify"]

      current_hashrate = raw["extras"]["xmrig"]["hashrate"]["current"]

      if current_hashrate < (target_hashrate * 0.9):
        self.app.LOG.warning(f"[XMRIG] {machine.name} has low hashrate of {current_hashrate} vs target {target_hashrate}")
        message = f"{machine.name} low hashrate of {current_hashrate}!"
        if "ntfy" in notify:
          await self.send_ntfy_notification(message)
        if "warning" in notify:
          machine.add_warning("xmrig")
      else:
        machine.remove_warning("xmrig")