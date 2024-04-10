from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import TYPE_CHECKING

import aiofiles
import aiohttp
import psutil
import yarl
from aiohttp.web import WSMsgType
from config import MACHINE_NAME, SERVER_URL
from plugins import fetch_plugins

if TYPE_CHECKING:
  pass

### Status Client Daemon - Monitoring tool for client machines.

reconnect_after = "never"
update_frequency = 5
collect_stats = True

fmt = "[%(filename)s][%(asctime)s][%(levelname)s] %(message)s"
datefmt = "%Y/%m/%d-%H:%M:%S"

logging.basicConfig(
  handlers=[
    # logging.FileHandler('log.txt'),
    logging.StreamHandler()
  ],
  format=fmt,
  datefmt=datefmt,
  level=logging.INFO,
)

# (bytes_recv, bytes_sent)
internet_by_minute: list[tuple] = []
internet_5m: tuple[int, int] = (0, 0)  # Bytes per second
internet_current: tuple[int, int] = (0, 0)  # ^^^

async def gather_internet_data(interval: int = 1) -> None:
  global internet_by_minute, internet_5m, internet_current
  try:
    logging.debug("Getting internet stats...")
    before = psutil.net_io_counters()
    await asyncio.sleep(interval)
    after = psutil.net_io_counters()
    bytes_sent = (after.bytes_sent - before.bytes_sent)/interval
    bytes_recv = (after.bytes_recv - before.bytes_recv)/interval
    internet_by_minute.insert(0, (bytes_sent, bytes_recv))
    internet_by_minute = internet_by_minute[0:5]

    internet_current = (bytes_sent, bytes_recv)

    f_sent = sum([x[0] for x in internet_by_minute])/len(internet_by_minute)
    f_recv = sum([x[1] for x in internet_by_minute])/len(internet_by_minute)

    internet_5m = (f_sent, f_recv)
  except Exception:
    logging.exception("Failed to update internet stats!")

async def gather_internet_data_loop() -> None:
  while True:
    interval = 1
    await gather_internet_data(interval)
    await asyncio.sleep(60-interval)


async def get_stats() -> dict:
  stats_info = {}
  logging.debug("get_stats called")
  # Get CPU info
  try:
    async with aiofiles.open("/proc/loadavg") as f:
      data = await f.read()
      # Assuming this is a POSIX-compliant system, this will work.
      m1, m5, m15 = data.split(" ")[0:3]
      stats_info["cpu"] = {"1m": m1, "5m": m5, "15m": m15}
  except Exception:
    logging.exception("cpu get failed!")
  # Get ram info
  logging.debug("Got CPU")
  virtual_memory = psutil.virtual_memory()
  stats_info["ram"] = {
    "used": virtual_memory.used,
    "free": virtual_memory.available,
    "total": virtual_memory.total,
  }
  logging.debug("Got mem")
  # Get disk info
  disk_usage = psutil.disk_usage("/")
  stats_info["disk"] = {
    "used": disk_usage.used,
    "free": disk_usage.free,
    "total": disk_usage.total,
  }
  logging.debug("Got disk")
  # Get boot time
  stats_info["boot_time"] = psutil.boot_time()
  logging.debug("Got boot time")
  # Get internet usage
  stats_info["internet"] = {
    "current": {
      "outgoing": internet_current[1],
      "incoming": internet_current[0],
    },
    "5m": {"outgoing": internet_5m[1], "incoming": internet_5m[0]},
  }
  logging.debug("Got internet")
  return stats_info


async def main(cs: aiohttp.ClientSession):
  plugins = None
  async with cs.get(SERVER_URL, params={"name": MACHINE_NAME}) as ws:
    data = await ws.json()
    TARGET_URL = data.get("url")
    update_frequency = data.get("update_frequency")
    collect_stats = data.get("collect_stats")
    addons = yarl.URL(TARGET_URL).query.get("addons")
    logging.info(f"requested plugins: {addons}")
    if addons is not None:
      plugins = fetch_plugins(addons)
    else:
      plugins = []
    logging.info(f"update frequency set to {update_frequency}s")
    logging.info(f"collect stats set to {collect_stats}")
    logging.info(f"loaded plugins: {[plugin.name for plugin in plugins]}")
  try:
    async with cs.ws_connect(TARGET_URL) as ws:

      async def send_data():
        logging.debug("Send_data called")
        monitor_packet = {}
        if collect_stats:
          try:
            monitor_packet["stats"] = await get_stats()
          except Exception:
            logging.exception("Failed to get stats!")
            return # We don't want to send data without stats.
          logging.debug("Got stats")
          
        monitor_packet["extras"] = {}

        for plugin in plugins:
          logging.debug(f"Running plugin {plugin.name}")
          monitor_packet["extras"][plugin.name] = await plugin.get_data(cs)

        logging.debug("Finished running plugins")

        packet = {"type": "monitor", "data": monitor_packet, "error": 0}

        logging.info("Sending monitor packet to server...")
        await ws.send_json(packet)

      async def sender_func():
        logging.debug("Sender started, waiting 1s")
        await asyncio.sleep(1)
        logging.debug("Sender started")
        while True:
          await send_data()
          await asyncio.sleep(update_frequency)

      async def receiver_func():
        running = True
        while running:
          try:
            if ws.closed:
              print("websocket closed")
              running = False
              continue
            message = await ws.receive()
            if message.type in (WSMsgType.CLOSE, WSMsgType.CLOSING, WSMsgType.CLOSED):
              running = False
              print("Received CLOSE/CLOSING/CLOSED message.")
              continue
            elif message.type != WSMsgType.TEXT:
              logging.error(f"Received invalid message type {WSMsgType(message.type).name}; {hasattr(message,'data') and message.data or 'no data'}")
            message_data = json.loads(message.data)
          except Exception:
            logging.exception("Failed parsing message from websocket")
            continue
          message_type = message_data.get("type")
          if message_type == "update":
            data = message_data.get("data")
            if "update_frequency" in data:
              global update_frequency
              update_frequency = data["update_frequency"]
              logging.info(f"update frequency set to {update_frequency}s")
            if "collect_stats" in data:
              global collect_stats
              collect_stats = data["collect_stats"]
              logging.info(f"collect stats set to {collect_stats}")
          elif message_type == "info":
            await send_data()
          elif message_type == "goodbye":
            data = message_data.get("data")
            logging.info(f"got goodbye {data}")
            global reconnect_after
            reconnect_after = data["reconnect_after"]
            raise asyncio.CancelledError
          elif message_type == "updateclient":
            logging.info("got updateclient")
            proc = await asyncio.create_subprocess_shell("pwd/update.sh")
            await proc.communicate()
            reconnect_after = "update"
            raise asyncio.CancelledError

      sender_task = asyncio.create_task(sender_func())
      receiver_task = asyncio.create_task(receiver_func())
      await asyncio.gather(sender_task, receiver_task)
  except Exception:
    logging.exception("ws died")


async def _main():
  global reconnect_after
  await gather_internet_data(1)
  internet_task = asyncio.create_task(gather_internet_data_loop())  # noqa: F841
  
  while True:
    async with aiohttp.ClientSession() as session:
      try:
        logging.info("Starting main")
        await main(session)
      except asyncio.CancelledError:
        pass
      except aiohttp.ClientConnectorError:
        logging.info("Failed to connect. Waiting 5 seconds.")
        reconnect_after = 5 # Wait a bit and try to reconnect
      logging.info("Main ended")
    if reconnect_after == "never":
      logging.info("Told to never reconnect.")
      break
    elif reconnect_after == "update":
      logging.info("Program has been updated")
      break
    else:
      logging.info(f"Told to reconnect after {reconnect_after}s")
      await asyncio.sleep(reconnect_after)

asyncio.run(_main())
sys.exit(0)