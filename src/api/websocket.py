from __future__ import annotations

import urllib.parse
from typing import TYPE_CHECKING
import time

from aiohttp import web
from aiohttp.web import Response, WebSocketResponse, WSMsgType
from yarl import URL

from .utils.plugins import ALL_PLUGINS, fetch_plugins
from .utils.scripts import fetch_scripts
from .utils.websocket_handler import WebsocketHandler

if TYPE_CHECKING:
  from utils.extra_request import Request

routes = web.RouteTableDef()

@routes.get("/ws/start/")
async def get_ws_start(request: Request) -> Response:
  query = request.query

  machine_name = query.get("name", None)
  addons = query.get("addons", None)

  if addons is not None:
    try:
      addons_list: list[str] = addons.split(",")
    except Exception:
      return Response(status=400, text="failed to parse addons list")
  else:
    addons_list = []

  if machine_name is None:
    return Response(status=400, text="missing name in query")

  parsed_name = urllib.parse.unquote_plus(machine_name)
  
  addons_record = await request.conn.fetchrow("SELECT Addons,CollectStats FROM Machines WHERE Name ILIKE $1;", parsed_name)
  if addons_record is None:
    return Response(status=400, text="machine not found!")

  database_addons = addons_record.get("addons", [])
  if database_addons is None:
    database_addons = []

  addons_list.extend(database_addons)
  super_list = list(set(addons_list))
  good_list: list[str] = []
  bad_list: list[str] = []

  for plugin_name in super_list:
    if plugin_name in ALL_PLUGINS:
      good_list.append(plugin_name)
    else:
      bad_list.append(plugin_name)

  query = {"name":machine_name}
  if good_list:
    query["addons"] = ",".join(good_list)
  scheme = "ws" if request.url.scheme == "http" else "wss"
  url = URL.build(scheme=scheme, port=request.url.port, host=request.url.host, path="/api/ws/connect/", query=query)

  packet = {
    "url": str(url),
    "update_frequency": request.app.status_config.UPDATE_FREQUENCY,
    "collect_stats": addons_record.get("collectstats"),
    "missed_plugins": ",".join(bad_list) # If the server is missing some plugins, let the client know.
  }

  return web.json_response(packet)

@routes.get("/ws/connect/")
async def get_ws_connect(request: Request) -> Response:
  query = request.query

  machine_name = query.get("name", None)
  addons = query.get("addons", None)

  request.LOG.debug(f"[WS][{machine_name}] received connect call")

  if addons is not None:
    try:
      addons_list: list[str] = addons.split(",")
    except Exception:
      return Response(status=400, text="failed to parse addons list")
  else:
    addons_list = []

  plugins_list = await fetch_plugins(addons_list, request.app.pool)
  request.LOG.debug(f"[WS][{machine_name}] {plugins_list}")

  if machine_name is None:
    return Response(status=400, text="missing name in query")

  parsed_name = urllib.parse.unquote_plus(machine_name)

  exists = (await request.conn.fetchrow("SELECT EXISTS (SELECT Name) FROM Machines WHERE Name = $1;", parsed_name))["exists"]

  if not exists:
    return Response(status=400, text="machine not registered")

  scripts = await request.conn.fetchrow("SELECT Scripts FROM Machines WHERE Name ILIKE $1;", parsed_name)
  scripts_list = await fetch_scripts(scripts["scripts"], request.app)

  request.LOG.debug(f"[WS][{machine_name}] machine exists, websocket it")

  ws = WebSocketResponse(autoclose=False)
  await ws.prepare(request)

  request.LOG.debug(f"[WS][{machine_name}] prepared websocket")

  ws_handler = request.app.websocket_handler

  await ws_handler.add_machine(parsed_name, ws, plugins_list, scripts_list)

  request.LOG.debug(f"[WS][{machine_name}] added machine")

  async for message in ws:
    request.LOG.debug(f"raw packet from {machine_name}: {WSMsgType(message.type).name}")
    if message.type in (WSMsgType.CLOSING, WSMsgType.CLOSED):
      break
    elif message.type != WSMsgType.TEXT:
      request.LOG.error(
        f"Received invalid message type {WSMsgType(message.type).name}; {hasattr(message,'data') and message.data or 'no data'}"
      )
    try:
      #ws_handler.handle_packet_tasks.append(
      #  asyncio.create_task(request.app.websocket_handler._handle_packet(parsed_name, message))
      #)
      start = time.time()
      await ws_handler._handle_packet(parsed_name, message)
      total = time.time() - start
      request.LOG.info(f"Handling packet for {parsed_name} took {total}s.")
    except Exception:
      request.LOG.exception(f"Failed handling packet for {parsed_name}")

  return ws

async def setup(app: web.Application) -> None:
  websocket_handler = WebsocketHandler(app)

  app.websocket_handler = websocket_handler

  for route in routes:
    app.LOG.info(f"  ↳ {route}")
  app.add_routes(routes)