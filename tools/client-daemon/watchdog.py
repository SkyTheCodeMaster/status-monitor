from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  pass


async def _run_cmd(cmd: str) -> int:
  proc = await asyncio.create_subprocess_shell(
    cmd,
    stdout=asyncio.subprocess.STDOUT,
    stderr=asyncio.subprocess.STDOUT,
  )
  await proc.communicate()
  return proc.returncode


async def revert_version():
  await _run_cmd("rm plugins.py requirements.txt statuscd.py")
  await _run_cmd('if [ -d "venv"]; then rm -r venv; fi')
  await _run_cmd("cp -r old/* .")
  await _run_cmd("python3.11 -m venv venv")
  await _run_cmd(
    'bash -c "source venv/bin/activate; python3.11 -m pip install -r requirements.txt"'
  )


async def _read_stream(stream, cb) -> None:
  while True:
    line = await stream.readline()
    if line:
      cb(line)
    else:
      break


async def main():
  fail_count = 0
  # Run the main status monitor and see if it errors out within 10 minutes, if it does so 3 times, revert to old version.
  while True:
    print("[WATCHDOG] Starting program...")
    proc = await asyncio.create_subprocess_shell(
      'bash -c "source venv/bin/activate; python3.11 statuscd.py"',
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE,
    )

    await asyncio.gather(
      _read_stream(proc.stdout, lambda line: print(line.decode(), end="")),
      _read_stream(proc.stderr, lambda line: print(line.decode(), end="")),
    )

    print(f"[WATCHDOG] Program exited with return code: {proc.returncode}")

    if proc.returncode == 0:
      print("[WATCHDOG] Program ended normally. Exiting")
      return
    else:
      fail_count += 1
      print(f"[WATCHDOG] Program exited with return code {proc.returncode}. Fail counter is {fail_count}.")  # fmt: skip
      if fail_count < 3:
        print("[WATCHDOG] Program has failed 3 times in a row. Reverting to previous version.")  # fmt: skip
        await revert_version()


asyncio.run(main())
