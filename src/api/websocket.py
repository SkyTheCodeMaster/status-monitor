from __future__ import annotations

import tomllib
import urllib.parse
from typing import TYPE_CHECKING

from aiohttp import web
from aiohttp.web import Response, WebSocketResponse
from yarl import URL

from .utils.plugins import ALL_PLUGINS
from .utils.websocket_handler import WebsocketHandler

if TYPE_CHECKING:
  from utils.extra_request import Request

with open("config.toml") as f:
  config = tomllib.loads(f.read())
  frontend_version = config["pages"]["frontend_version"]
  api_version = config["srv"]["api_version"]

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
    "update_frequency": request.app.config.UPDATE_FREQUENCY,
    "collect_stats": addons_record.get("collectstats"),
    "missed_plugins": ",".join(bad_list) # If the server is missing some plugins, let the client know.
  }

  return web.json_response(packet)

@routes.get("/ws/connect/")
async def get_ws_connect(request: Request) -> Response:
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

  exists = (await request.conn.fetchrow("SELECT EXISTS (SELECT Name) FROM Machines WHERE Name = $1;", parsed_name))["exists"]
  
  if not exists:
    return Response(status=400, text="machine not registered")

  ws = WebSocketResponse(autoclose=False)
  await ws.prepare(request)

  await request.app.websocket_handler.add_machine(parsed_name, ws, addons_list)
  return ws

async def setup(app: web.Application) -> None:
  websocket_handler = WebsocketHandler(app)

  app.websocket_handler = websocket_handler

  for route in routes:
    app.LOG.info(f"  ↳ {route}")
  app.add_routes(routes)