from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import yarl

if TYPE_CHECKING:
  from asyncio import Task
  from logging import Logger
  from typing import Any

  import aiohttp
  import asyncpg
  from aiohttp.web import WebSocketResponse

  from utils.extra_request import Application

LOG = logging.getLogger(__name__)

class Plugin:
  pool: asyncpg.Pool
  name: str  # Name used for referencing plugins
  side: str  # Whether or not to run this on client.
  priority: int  # When to run the plugin.
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

  def __init_subclass__(
    cls, *, name: str = None, side: str = "both", priority: int = 0, **kwargs
  ) -> None:
    super().__init_subclass__(**kwargs)
    if name is None:
      name = cls.__qualname__

    cls.name = name
    cls.side = side
    cls.priority = priority


class Script:
  pool: asyncpg.Pool
  cs: aiohttp.ClientSession
  app: Application
  name: str  # Name used for referencing scripts
  priority: int  # When to run the plugin.
  _ntfy_url: str
  _ntfy_token: str
  _ntfy_topic: str

  def __init__(self, app: Application) -> None:
    self.pool = app.pool
    self.cs = app.cs
    self.app = app

  async def run(self, packet: MonitorPacket, machine: ConnectedMachine) -> None:
    pass

  def __init_subclass__(
    cls, *, name: str = None, priority: int = 0, **kwargs
  ) -> None:
    super().__init_subclass__(**kwargs)
    if name is None:
      name = cls.__qualname__

    cls.name = name
    cls.priority = priority

  async def send_ntfy_notification(
    self,
    body: str,
    *,
    title: str = None,
    priority: int = 3,
    tags: list[str] = None,
    click: str = None,
    markdown: bool = True,
    attach: str = None,
    topic: str = None,
    filename: str = None,
    delay: str = None,
  ) -> bool:
    """
    body: str: Body text for notification. Required.
    title: str: Title for notification.
    priority: int: 1 is lowest, 5 is highest. Default 3 (Middle).
    tags: list[str]: List of tags. If a tag matches an emoji shortcode, it is prepended to the title.
    click: str: URL to navigate to when notification is clicked.
    markdown: bool: Whether or not the message is markdown formatted. Default True.
    attach: str: URL to use for image.
    filename: str: Filename of attach URL.
    delay: str: How long to delay the notification for. formatted like "30min" or "9am"
    topic: str: Topic to send on. Defaults to config.toml topic.
    """

    headers = {"Authorization": f"Bearer {self.app.config.notify.token}"}

    if topic is None:
      topic = self.app.config.notify.topic

    data = {
      "topic": topic,
      "message": body,
      "priority": priority,
      "title": title,
      "tags": tags,
      "click": click,
      "markdown": markdown,
      "attach": attach,
      "filename": filename,
      "delay": delay,
    }

    for key in list(data.keys()):
      if data[key] is None:
        data.pop(key)

    async with self.app.cs.post(
      self.app.config.notify.url, headers=headers, data=json.dumps(data)
    ) as resp:
      if resp.status != 200:
        self.app.LOG.warning(f"{self.app.config.notify.topic} {headers}")
        self.app.LOG.warning(f"Failed to send ntfy! HTTP{resp.status}: {await resp.text()}")
      return resp.status == 200


class ConnectedMachine:
  name: str
  ws: WebSocketResponse
  plugins: list[Plugin]
  scripts: list[Script]
  reader_task: Task
  stats: BasicMachineStats
  running: bool
  last_communication: float
  category: str
  extra_config: dict
  online: bool
  app: Application
  _warnings: set

  def __init__(
    self,
    *,
    ws: WebSocketResponse,
    plugins: list[Plugin],
    scripts: list[Script],
    name: str,
    app: Application,
  ) -> None:
    self.ws = ws
    self.plugins = plugins
    self.scripts = scripts
    self.name = name
    self.app = app
    self.running = True
    self._warnings = set()

  def fill_data(self, record: asyncpg.Record) -> None:
    self.category = record.get("category", None)
    try:
      extra_config = record.get("extraconfig", "{}")
      self.extra_config = json.loads(extra_config)
    except Exception:
      self.extra_config = {}

  def url(self, open_tabs: list[str]) -> str:
    url = (
      yarl.URL(self.app.config.srv.url)
      / "machines"
      % {"c": self.category, "m": self.name, "mt": ",".join(open_tabs)}
    )
    return str(url)

  async def write_extra_config(self, pool: asyncpg.Pool) -> bool:
    data = json.dumps(self.extra_config)
    async with pool.acquire() as conn:
      conn: asyncpg.Connection
      result = await conn.execute(
        "UPDATE Machines SET ExtraConfig=$2 WHERE Name=$1;", self.name, data
      )
      return result == "UPDATE 1"

  def add_warning(self, source: str) -> None:
    self._warnings.add(source)

  def remove_warning(self, source: str) -> None:
    try:
      self._warnings.remove(source)
    except KeyError:
      pass

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
  _cached_out: Any
  _log: Logger

  def __init__(self, packet: dict, *, log: Logger = None) -> None:
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

    self._log = log

  async def process_extras(
    self, plugins: list[Plugin], connected_machine: ConnectedMachine
  ) -> None:
    for plugin in plugins:
      # This is expected to modify `extras` in place.
      await plugin.run(self.extras, connected_machine)

  async def run_scripts(
    self, scripts: list[Script], connected_machine: ConnectedMachine
  ) -> None:
    for script in scripts:
      try:
        if self._log:
          self._log.info(f"[SCRIPTS] Running {script.name} for {connected_machine.name}.")
        await script.run(self, connected_machine)
      except Exception:
        if self.log:
          self._log.exception(f"Failed running {script.name}!")

  async def out(
    self, plugins: list[Plugin], connected_machine: ConnectedMachine
  ) -> dict:
    if hasattr(self, "_cached_out"):
      return self._cached_out

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

    out["extras"] = {}

    for plugin in plugins:
      out["extras"][plugin.name] = await plugin.out(
        self.extras, connected_machine
      )

    self._cached_out = out
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
