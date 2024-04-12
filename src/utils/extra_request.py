from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp.web import Application as BaseApplication
from aiohttp.web import Request as BaseRequest

if TYPE_CHECKING:
  from logging import Logger
  from aiohttp import ClientSession

  from asyncpg import Connection, Pool
  from api.utils.websocket_handler import WebsocketHandler

class StatusConfig:
  UPDATE_FREQUENCY: int # Number of seconds for update frequency

class Application(BaseApplication):
  pool: Pool
  LOG: Logger
  cs: ClientSession
  POSTGRES_ENABLED: bool
  status_config: StatusConfig
  config: dict # config.toml
  websocket_handler: WebsocketHandler

class Request(BaseRequest):
  app: Application
  conn: Connection
  pool: Pool
  LOG: Logger
  session: ClientSession