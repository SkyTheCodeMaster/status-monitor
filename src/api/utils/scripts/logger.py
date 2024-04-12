from __future__ import annotations

import datetime
import json
import logging
from typing import TYPE_CHECKING

import pytz

from api.utils.data_classes import Script

if TYPE_CHECKING:
  from asyncpg import Connection

  from api.utils.data_classes import ConnectedMachine, MonitorPacket

LOG = logging.getLogger(__name__)

class LoggerScript(Script, name="logger", priority=-9999):
  async def run(self, packet: MonitorPacket, machine: ConnectedMachine) -> None:
    # This script is only run when the machine explicitly calls for it.
    # This simply puts both the raw packet and the processed packet into the database.

    raw = packet.raw
    out = await packet.out(machine.plugins, machine)

    data = {
      "raw": raw,
      "processed": out
    }

    str_data = json.dumps(data)
    timestamp = datetime.datetime.now(tz=pytz.timezone(self.app.config.timezone))

    async with self.pool.acquire() as conn:
      conn: Connection
      await conn.execute("INSERT INTO LoggedData (Name, Time, Data) VALUES ($1, $2, $3);", machine.name, timestamp, str_data)
      LOG.debug(f"[Logger] Logged data for {machine.name}; Length {len(str_data)}")