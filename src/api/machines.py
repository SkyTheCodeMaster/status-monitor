from __future__ import annotations

import json
import urllib.parse
from typing import TYPE_CHECKING
import asyncio

from aiohttp import web
from aiohttp.web import Response

from utils.utils import validate_parameters

if TYPE_CHECKING:
  from utils.extra_request import Request
  from asyncpg import Record

routes = web.RouteTableDef()


@routes.get("/machines/get/all/")
async def get_machines_get_all(request: Request) -> Response:
  try:
    async with asyncio.timeout(3):
      packet = await request.app.websocket_handler.get_all_data()
      return web.json_response(packet)
  except asyncio.TimeoutError:
    return Response(status=500, text="top level timeout reached")


@routes.get("/machines/get/")
async def get_machines_get(request: Request) -> Response:
  query = request.query

  machine_name = query.get("name", None)
  if machine_name is None:
    return Response(status=400, text="missing name in query")

  parsed_name = urllib.parse.unquote_plus(machine_name)

  packet = await request.app.websocket_handler.get_data(parsed_name)
  if parsed_name in request.app.websocket_handler.connected_machines:
    print(
      request.app.websocket_handler.connected_machines[parsed_name].ws.closed
    )
  else:
    print("not connected")
  if packet is None:
    return web.Response(status=404)
  else:
    return web.json_response(packet)


@routes.post("/machines/create/")
async def post_machines_create(request: Request) -> Response:
  """
  {
    "name": "Machine Name Here" - Return error if name and category already registered.
    "category": "Machine's category" - ^^^
    "stats_enabled": true
    "plugins": "a,b,c"
    "extra_config": {"extra_plugin_config_here":"AAA"}
  }
  """
  try:
    data: dict = await request.json()
  except ValueError:
    return Response(status=400, text="invalid json body")

  required_params = ["name", "category"]
  ok, missing = validate_parameters(data, required_params)
  if not ok:
    return Response(status=400, text=f"missing required parameter {missing}")

  name: str = data.get("name")
  category: str = data.get("category")
  stats_enabled: bool = data.get("stats_enabled", True)
  plugins: str = data.get("plugins", [])
  extra_config: dict = data.get("extra_config", {})

  # Check if the name and category already exist.
  machine_exists = await request.conn.fetchrow(
    "SELECT * FROM Machines WHERE Name ILIKE $1;",
    name,
  )
  if machine_exists is not None:
    return Response(status=400, text="name already registered")

  # Now just throw it into the database.
  extra_str = json.dumps(extra_config)

  result = await request.conn.execute(
    "INSERT INTO Machines (Name, Category, CollectStats, Addons, ExtraConfig) VALUES ($1,$2,$3,$4,$5);",
    name,
    category,
    stats_enabled,
    plugins,
    extra_str,
  )

  if result == "INSERT 0 1":
    return Response()
  else:
    request.LOG.error(f"POST /machines/create/ failed; SQL result: {result}")
    return Response(status=500)


@routes.get("/machines/info/")
async def get_machines_info(request: Request) -> Response:
  """pass name in query.
  returns same format as in POST /machines/create/
  """
  name = request.query.get("name", None)
  if name is None:
    return Response(status=400, text="must pass machine in query")

  name = urllib.parse.unquote_plus(name)

  record = await request.conn.fetchrow(
    "SELECT * FROM Machines WHERE Name ILIKE $1;",
    name,
  )

  if record is None:
    return Response(status=404, text="machine not found")

  packet = {
    "name": record.get("name"),
    "category": record.get("category"),
    "stats_enabled": record.get("collectstats"),
    "plugins": record.get("addons"),
  }

  try:
    packet["extra_config"] = json.loads(record.get("extraconfig", "{}"))
  except TypeError:
    packet["extra_config"] = {}

  return web.json_response(packet)


@routes.post("/machines/update/")
async def post_machines_update(request: Request) -> Response:
  """
  {
    "name": "Machine Name Here" - Return error if name and category are not existing.
    "new": { All of the fields are optional.
      "name": "Machine Name Here" - Return error if name and category already registered.
      "category": "Machine's category" - ^^^
      "stats_enabled": true
      "plugins": "a,b,c"
      "extra_config": {"extra_plugin_config_here":"AAA"}
    }
  }
  """
  try:
    data: dict = await request.json()
  except ValueError:
    return Response(status=400, text="invalid json body")

  required_params = ["name", "new"]
  ok, missing = validate_parameters(data, required_params)
  if not ok:
    return Response(status=400, text=f"missing required parameter {missing}")

  name: str = data.get("name")

  new: dict = data.get("new")

  # Check if the name and category already exist.
  machine_exists: Record = await request.conn.fetchrow(
    "SELECT * FROM Machines WHERE Name ILIKE $1;",
    name,
  )

  if machine_exists is None:
    return Response(status=400, text="machine not found")

  new_name: str = new.get("name", machine_exists.get("name"))
  new_category: str = new.get("category", machine_exists.get("category"))
  new_stats_enabled: bool = new.get(
    "stats_enabled", machine_exists.get("collectstats")
  )
  new_plugins: str = new.get("plugins", machine_exists.get("addons"))
  new_extra_config: dict = new.get(
    "extra_config", machine_exists.get("extraconfig")
  )

  # Now just throw it into the database.

  result = await request.conn.execute(
    """
    UPDATE
      Machines
    SET
      Name = $2,
      Category = $3,
      CollectStats = $4,
      Addons = $5,
      ExtraConfig = $6
    WHERE
      Name ILIKE $1;
    """,
    name,
    new_name,
    new_category,
    new_stats_enabled,
    new_plugins,
    json.dumps(new_extra_config),
  )

  if result == "UPDATE 1":
    return Response()
  else:
    request.LOG.error(f"POST /machines/update/ failed; SQL result: {result}")
    return Response(status=500)


@routes.delete("/machines/delete/")
async def delete_machines_delete(request: Request) -> Response:
  "pass `name` in query."
  name = request.query.get("name", None)
  if name is None:
    return Response(status=400, text="must pass machine name in query")

  name = urllib.parse.unquote_plus(name)

  record = await request.conn.fetchrow(
    "SELECT * FROM Machines WHERE Name ILIKE $2;",
    name,
  )

  if record is None:
    return Response(status=404, text="machine not found")

  result = await request.conn.execute(
    "DELETE FROM Machines WHERE Name ILIKE $1;",
    name,
  )

  if result == "DELETE 1":
    return Response()
  else:
    request.LOG.error(f"DELETE /machines/delete/ failed; SQL result: {result}")
    return Response(status=500)


@routes.post("/machines/disconnect/")
async def post_machines_disconnect(request: Request) -> Response:
  "pass `name` in query."
  name = request.query.get("name", None)
  if name is None:
    return Response(status=400, text="must pass machine name in query")

  name = urllib.parse.unquote_plus(name)

  if (
    name not in request.app.websocket_handler.connected_machines
    or not request.app.websocket_handler.connected_machines[name].online
  ):
    return Response(status=409, text="machine not connected")

  await request.app.websocket_handler.remove_machine(name)
  return Response()


@routes.post("/machines/disconnect/all/")
async def post_machines_disconnect_all(request: Request) -> Response:
  names = list(request.app.websocket_handler.connected_machines.keys())

  for name in names:
    try:
      await request.app.websocket_handler.remove_machine(name)
    except Exception:
      request.LOG.error(f"failed to reconnect {name}")

  return Response()


@routes.post("/machines/reconnect/")
async def post_machines_reconnect(request: Request) -> Response:
  "pass `name` in query."
  name = request.query.get("name", None)
  if name is None:
    return Response(status=400, text="must pass machine name in query")

  name = urllib.parse.unquote_plus(name)

  try:
    reconnect_after = int(request.query.get("after", "5"))
  except ValueError:
    return Response(status=400, text="after must be integer!")

  if (
    name not in request.app.websocket_handler.connected_machines
    or not request.app.websocket_handler.connected_machines[name].online
  ):
    return Response(status=409, text="machine not connected")

  await request.app.websocket_handler.reconnect_machine(
    name, reconnect_after=reconnect_after
  )
  return Response()


@routes.post("/machines/reconnect/all/")
async def post_machines_reconnect_all(request: Request) -> Response:
  "pass `name` in query."
  try:
    reconnect_after = int(request.query.get("after", "5"))
  except ValueError:
    return Response(status=400, text="after must be integer!")

  names = list(request.app.websocket_handler.connected_machines.keys())

  for name in names:
    try:
      await request.app.websocket_handler.reconnect_machine(
        name, reconnect_after=reconnect_after
      )
    except Exception:
      request.LOG.exception(f"failed to reconnect {name}")

  return Response()


@routes.post("/machines/updateclient/")
async def post_machines_updateclient(request: Request) -> Response:
  "pass `name` in query."
  name = request.query.get("name", None)
  if name is None:
    return Response(status=400, text="must pass machine name in query")

  name = urllib.parse.unquote_plus(name)

  if (
    name not in request.app.websocket_handler.connected_machines
    or not request.app.websocket_handler.connected_machines[name].online
  ):
    return Response(status=409, text="machine not connected")

  await request.app.websocket_handler.update_client(name)
  return Response()


@routes.post("/machines/updateclient/all/")
async def post_machines_updateclient_all(request: Request) -> Response:
  names = list(request.app.websocket_handler.connected_machines.keys())

  for name in names:
    try:
      await request.app.websocket_handler.update_client(name)
    except Exception:
      request.LOG.exception(f"failed to update {name}")


async def setup(app: web.Application) -> None:
  for route in routes:
    app.LOG.info(f"  ↳ {route}")
  app.add_routes(routes)
