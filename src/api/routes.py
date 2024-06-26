from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING

from aiohttp import web
from aiohttp.web import Response

if TYPE_CHECKING:
  from utils.extra_request import Request

routes = web.RouteTableDef()


@routes.get("/srv/get/")
async def get_lp_get(request: Request) -> Response:
  packet = {
    "frontend_version": request.app.config.pages.frontend_version,
    "api_version": request.app.config.pages.api_version,
  }

  if request.app.POSTGRES_ENABLED:
    database_size_record = await request.conn.fetchrow(
      "SELECT pg_size_pretty ( pg_database_size ( current_database() ) );"
    )
    packet["db_size"] = database_size_record.get("pg_size_pretty", "-1 kB")

  total_machines_record = await request.conn.fetchrow("SELECT COUNT(*) FROM Machines;")

  packet["total_machines"] = total_machines_record.get("count")
  packet["online_machines"] = len(
    [
      cm
      for cm in request.app.websocket_handler.connected_machines.values()
      if cm.online
    ]
  )
  return web.json_response(packet)


async def setup(app: web.Application) -> None:
  for route in routes:
    app.LOG.info(f"  ↳ {route}")
  app.add_routes(routes)
