from __future__ import annotations

class Plugin:
  async def run(self, extras_dict: dict) -> None:
    if "test" in extras_dict:
      extras_dict["test"] = "Processed by example plugin"

class InternetStats:
  current: dict[str,float]
  five_minutes: dict[str,float]

  def __init__(self, internet_packet: dict[str,dict]) -> None:
    self.current = internet_packet.get("current")
    self.five_minutes = internet_packet.get("5m")

class MonitorPacket:
  cpu: dict[str,float]
  ram: dict[str,float]
  disk: dict[str,int] #?
  boot_time: int
  internet: InternetStats
  extras: dict

  def __init__(self, packet: dict) -> None:
    self.cpu = packet.get("cpu")
    self.ram = packet.get("ram")
    self.disk = packet.get("disk")
    self.boot_time = packet.get("boot_time")
    self.internet = InternetStats(packet.get("internet"))
    self.extras = packet.get("extras")

  async def process_extras(self, plugins: list[str], ALL_PLUGINS: dict[str, Plugin]):# -> None:
    valid_plugins = [plugin for plugin in plugins if plugin in ALL_PLUGINS]
    for plugin in valid_plugins:
      await ALL_PLUGINS[plugin].run(self.extras) # This is expected to modify `extras` in place.