from __future__ import annotations

import asyncio
import json
import time
from typing import TYPE_CHECKING

from aiohttp.web import WSMsgType

from api.utils.plugins import ALL_PLUGINS

from .data_classes import BasicMachineStats, ConnectedMachine, MonitorPacket

if TYPE_CHECKING:
  from typing import Callable

  from aiohttp import WSMessage
  from aiohttp.web import WebSocketResponse
  from asyncpg import Connection

  from utils.extra_request import Application

  from .data_classes import Plugin


class WebsocketHandler:
  # A dictionary of machine name -> websockets
  connected_machines: dict[str, ConnectedMachine]
  # A dictionary of cached machine stats
  current_stats: dict[str, BasicMachineStats]
  # A dictionary of all available plugins for a machine.
  app: Application
  # Task to check which websockets are alive.
  living_socket_task: asyncio.Task

  def __init__(self, app: Application) -> None:
    self.connected_machines = {}
    self.current_stats = {}
    self.app = app

  async def setup(self) -> None:
    self.living_socket_task = asyncio.create_task(self._check_living_sockets())

  async def close(self) -> None:
    for cm in self.connected_machines.values():
      await self.remove_machine(cm.name)

    self.living_socket_task.cancel()

  async def _check_living_sockets(self) -> None:
    while True:
      for cm in self.connected_machines.values():
        cm.online = not cm.ws.closed
      await asyncio.sleep(1)

  async def add_machine(
    self, machine_name: str, ws: WebSocketResponse, plugins: list[str]
  ) -> None:
    # Resolve plugins
    resolved_plugins: dict[str, Plugin] = {}
    for plugin_name in plugins:
      resolved_plugins[plugin_name] = ALL_PLUGINS[plugin_name]

    cm = ConnectedMachine(ws=ws, plugins=resolved_plugins, name=machine_name)
    cm.online = True

    async with self.app.pool.acquire() as conn:
      conn: Connection
      record = await conn.fetchrow(
        "SELECT * FROM Machines WHERE Name ILIKE $1;", machine_name
      )
      cm.fill_data(record)

    self.connected_machines[machine_name] = cm
    await self.handle_packet(cm.name)

  async def remove_machine(self, machine_name: str) -> None:
    if machine_name in self.connected_machines:
      cm = self.connected_machines[machine_name]
      await cm.ws.send_json(
        {"type": "goodbye", "data": {"reconnect_after": "never"}, "error": 0}
      )
      await cm.ws.close()
      self.connected_machines.pop(machine_name)

  async def reconnect_machine(
    self, machine_name: str, *, reconnect_after: int = 5
  ) -> None:
    if machine_name in self.connected_machines:
      cm = self.connected_machines[machine_name]
      await cm.ws.send_json(
        {
          "type": "goodbye",
          "data": {"reconnect_after": reconnect_after},
          "error": 0,
        }
      )
      await cm.ws.close()
      self.connected_machines.pop(machine_name)

  async def _handle_packet(self, machine_name: str, message: WSMessage) -> None:
    self.app.LOG.info(f"raw packet from {machine_name} of size {len(message.data)}")
    if machine_name not in self.connected_machines:
      print("Received packet from disconnected machine:", machine_name)
      return
    cm = self.connected_machines[machine_name]
    try:
      raw_data = message.data
      if raw_data is None or not isinstance(raw_data, str):
        self.app.LOG.info(
          f"raw packet from {machine_name} is not correct type; it is {type(raw_data)}"
        )
        return
      data = json.loads(raw_data)
    except Exception:
      print("Failed parsing data packet from", machine_name)
      return

    cm.last_communication = time.time()

    # This is a top level packet, so we'll have type, error, and data.
    packet_type = data.get("type")
    packet_data = data.get("data")
    if packet_type == "monitor":
      mp = MonitorPacket(packet_data)
      await mp.process_extras(cm.plugins.values(), cm)
      cm.last_communication = time.time()
      cm.stats = BasicMachineStats(mp)
    self.app.LOG.info(f"Received packet from {cm.name}")

  async def handle_packet(
    self, machine_name: str
  ) -> Callable[[None, None], asyncio.Task]:
    cm = self.connected_machines[machine_name]

    async for message in cm.ws:
      if message.type in (WSMsgType.CLOSING, WSMsgType.CLOSED):
        break
      elif message.type != WSMsgType.TEXT:
        self.app.LOG.error(
          f"Received invalid message type {WSMsgType(message.type).name}; {hasattr(message,'data') and message.data or 'no data'}"
        )
      try:
        await self._handle_packet(machine_name, message)
      except Exception:
        self.app.LOG.exception(f"Failed handling packet for {cm.name}")

  def get_stats(self, name: str) -> BasicMachineStats:
    if name not in self.connected_machines:
      return None
    cm = self.connected_machines[name]
    return cm.stats

  def get_all_stats(self) -> dict[str, BasicMachineStats]:
    return {
      name: self.connected_machines[name].stats
      for name in self.connected_machines
    }

  async def get_data(self, name: str) -> dict:
    if name not in self.connected_machines:
      return None
    cm = self.connected_machines[name]
    if cm.stats is None:
      return None
    packet = {
      "name": cm.name,
      "category": cm.category,
      "data": await cm.stats.latest_packet.out(cm.plugins.values(), cm),
    }
    return packet

  async def get_all_data(self) -> dict[str, dict]:
    out = {}
    for machine_name in self.connected_machines.keys():
      out[machine_name] = await self.get_data(machine_name)
    
    async with self.app.pool.acquire() as conn:
      conn: Connection
      all_machines = await conn.fetch("SELECT * FROM Machines;")
      for record in all_machines:
        if record.get("name") not in out:
          out[record.get("name")] = {
            "name": record.get("name"),
            "category": record.get("category"),
            "data": {
              "online": False,
              "stats": "invalid stats"
            }
          }
    return out
