from __future__ import annotations

import asyncio
import json
import time
from typing import TYPE_CHECKING

from .data_classes import BasicMachineStats, ConnectedMachine, MonitorPacket

if TYPE_CHECKING:
  from logging import Logger

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
  # Handle packet tasks that are running
  handle_packet_tasks: list[asyncio.Task]
  # Logging instance
  log: Logger

  def __init__(self, app: Application) -> None:
    self.connected_machines = {}
    self.current_stats = {}
    self.handle_packet_tasks = []
    self.app = app
    self.log = app.LOG

  async def setup(self) -> None:
    self.living_socket_task = asyncio.create_task(self._check_living_sockets())

  async def close(self) -> None:
    names = [cm.name for cm in self.connected_machines.values()]
    for name in names:
      try:
        await self.remove_machine(name)
      except Exception:
        self.app.LOG.error(f"Failed to disconnect {name}")
    self.living_socket_task.cancel()

  async def _check_living_sockets(self) -> None:
    while True:
      for cm in self.connected_machines.values():
        # It is offline if the WS is closed, or it hasn't talked in 10 minutes.
        is_online = (
          not cm.ws.closed and cm.last_communication > time.time() - 600
        )
        cm.online = is_online
      await asyncio.sleep(1)

  async def add_machine(
    self, machine_name: str, ws: WebSocketResponse, plugins: list[Plugin]
  ) -> None:
    self.log.debug(f"[WSH][{machine_name}] called add_machine")
    cm = ConnectedMachine(ws=ws, plugins=plugins, name=machine_name, app=self.app)
    cm.online = True
    self.log.debug(f"[WSH][{machine_name}] instantiated connectedmachine")

    async with self.app.pool.acquire() as conn:
      conn: Connection
      self.log.debug(f"[WSH][{machine_name}] got connection")
      record = await conn.fetchrow(
        "SELECT * FROM Machines WHERE Name ILIKE $1;", machine_name
      )
      self.log.debug(f"[WSH][{machine_name}] filling data")
      cm.fill_data(record)
      self.log.debug(f"[WSH][{machine_name}] finished filling")

    self.connected_machines[machine_name] = cm
    self.log.debug(f"[WSH][{machine_name}] inserted into cm dict")

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
    self.app.LOG.info(
      f"raw packet from {machine_name} of size {len(message.data)}"
    )
    if machine_name not in self.connected_machines:
      # print("Received packet from disconnected machine:", machine_name)
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
      await mp.process_extras(cm.plugins, cm)
      cm.last_communication = time.time()
      cm.stats = BasicMachineStats(mp)
    # self.app.LOG.info(f"Received packet from {cm.name}")

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
    packet = {
      "name": cm.name,
      "category": cm.category,
    }
    if not hasattr(cm, "stats"):
      packet["data"] = "invalid stats"
    else:
      packet["data"] = await cm.stats.latest_packet.out(cm.plugins, cm)
    return packet

  async def get_all_data(self) -> dict[str, dict]:
    out = {}
    for machine_name in self.connected_machines.keys():
      try:
        async with asyncio.timeout(0.05):
          out[machine_name] = await self.get_data(machine_name)
      except asyncio.TimeoutError:
        self.app.LOG.warning(
          f"{machine_name} took longer than 50ms to get_data!"
        )

    async with self.app.pool.acquire() as conn:
      conn: Connection
      all_machines = await conn.fetch("SELECT * FROM Machines;")
      for record in all_machines:
        if record.get("name") not in out:
          out[record.get("name")] = {
            "name": record.get("name"),
            "category": record.get("category"),
            "data": {"online": False, "stats": "invalid stats"},
          }
    return out

  async def update_client(self, machine_name: str) -> bool:
    if machine_name in self.connected_machines:
      cm = self.connected_machines[machine_name]
      await cm.ws.send_json(
        {
          "type": "updateclient",
          "error": 0,
        }
      )
      await cm.ws.close()
      self.connected_machines.pop(machine_name)
      return True
    return False

  async def update_all_clients(self) -> bool:
    names = [cm.name for cm in self.connected_machines.values()]
    for name in names:
      await self.update_client(name)
    return True