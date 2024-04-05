from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from asyncio import Task
  from typing import Any

  import asyncpg
  from aiohttp.web import WebSocketResponse


class Plugin:
  pool: asyncpg.Pool
  name: str  # Name used for referencing plugins
  side: str  # Whether or not to run this on client.
  # Possible values: 'client', 'server', 'both'
  # If client, the run and out should do nothing, as it is just a namespace plugin.

  def __init__(self, pool: asyncpg.Pool) -> None:
    self.pool = pool

  async def run(self, extras_dict: dict, machine: ConnectedMachine) -> None:
    if "test" in extras_dict:
      extras_dict["test"] = (
        f"Processed by example plugin, for {machine.name} in {machine.category}"
      )

  async def out(self, extras_dict: dict, machine: ConnectedMachine) -> Any:
    return extras_dict["test"]

  def __init_subclass__(cls, *, name: str = None, side: str = "both", **kwargs) -> None:
    super().__init_subclass__(**kwargs)
    if name is None:
      name = cls.__qualname__

    cls.name = name
    cls.side = side


class ConnectedMachine:
  name: str
  ws: WebSocketResponse
  plugins: dict[str, Plugin]
  reader_task: Task
  stats: BasicMachineStats
  running: bool
  last_communication: float
  category: str
  extra_config: dict
  online: bool

  def __init__(
    self, *, ws: WebSocketResponse, plugins: dict[str, Plugin], name: str
  ) -> None:
    self.ws = ws
    self.plugins = plugins
    self.name = name
    self.running = True

  def fill_data(self, record: asyncpg.Record) -> None:
    self.category = record.get("category", None)
    try:
      extra_config = record.get("extraconfig", "{}")
      self.extra_config = json.loads(extra_config)
    except Exception:
      self.extra_config = {}


class InternetStats:
  current: dict[str, float]
  five_minutes: dict[str, float]

  def __init__(self, internet_packet: dict[str, dict]) -> None:
    self.current = internet_packet.get("current")
    self.five_minutes = internet_packet.get("5m")

  def out(self) -> dict:
    return {"current": self.current, "5m": self.five_minutes}


class MonitorPacket:
  # If this is false, then there is invalid data in the monitoring packet,
  # or the system doesn't report monitoring stats. It could also mean data
  # is incomplete.
  stats_valid: bool
  cpu: dict[str, float]
  ram: dict[str, float]
  disk: dict[str, int]  # ?
  boot_time: int
  internet: InternetStats
  extras: dict
  raw: dict

  def __init__(self, packet: dict) -> None:
    self.raw = packet
    monitoring_data = packet.get("stats", None)
    self.stats_valid = True
    if not monitoring_data:
      self.stats_valid = False
    else:
      try:
        self.cpu = monitoring_data.get("cpu")
        self.ram = monitoring_data.get("ram")
        self.disk = monitoring_data.get("disk")
        self.boot_time = monitoring_data.get("boot_time")
        self.internet = InternetStats(monitoring_data.get("internet"))
      except Exception:
        self.stats_valid = False

    self.extras = packet.get("extras")

  async def process_extras(
    self, plugins: list[Plugin], connected_machine: ConnectedMachine
  ) -> None:
    for plugin in plugins:
      # This is expected to modify `extras` in place.
      await plugin.run(self.extras, connected_machine)

  async def out(
    self, plugins: list[Plugin], connected_machine: ConnectedMachine
  ) -> dict:
    out = {}

    out["online"] = connected_machine.online

    if self.stats_valid:
      out["stats"] = {
        "cpu": self.cpu,
        "ram": self.ram,
        "disk": self.disk,
        "boot_time": self.boot_time,
        "internet": self.internet.out(),
      }
    else:
      out["stats"] = "invalid stats"

    for plugin in plugins:
      out[plugin.name] = await plugin.out(self.extras, connected_machine)

    return out


class Packet:
  type: str
  data: Any
  error: int | None

  def __init__(self, data: dict) -> None:
    "take in json.loads of sent packet"
    self.type = data.get("type")
    self.data = data.get("data")
    self.error = data.get("error")


class BasicMachineStats:
  latest_packet: MonitorPacket

  def __init__(self, monitor_packet: MonitorPacket) -> None:
    self.latest_packet = monitor_packet
