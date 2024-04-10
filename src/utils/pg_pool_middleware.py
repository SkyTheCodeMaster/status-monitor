from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from aiohttp.web import middleware

if TYPE_CHECKING:
  from aiohttp.web import Request
  from asyncpg import Connection

@middleware
async def pg_pool_middleware(request: Request, handler):
  request.LOG = request.app.LOG
  request.session = request.app.cs
  if request.app.POSTGRES_ENABLED:
    async with request.app.pool.acquire() as conn:
      conn: Connection
      request.conn = conn
      request.pool = request.app.pool
      async def warn_long_task():
        reps = 0
        while True:
          await asyncio.sleep(1)
          reps = reps + 1
          request.LOG.warning(f"call to {request.url} is taking a long time! Repeat: {reps}")

      #task = asyncio.create_task(warn_long_task())
      start = time.monotonic_ns()
      resp = await handler(request)
      #task.cancel()
      request.LOG.info(f"call to {request.url} took {(time.monotonic_ns()-start)/1000} microseconds")
      return resp
  else:
    resp = await handler(request)
    return resp