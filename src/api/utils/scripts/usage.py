from __future__ import annotations

import copy
import hashlib
import logging
import time
from typing import TYPE_CHECKING

import py_expression_eval

from api.utils.data_classes import ConnectedMachine, MonitorPacket, Script
from utils.extra_request import Application
from utils.utils import validate_parameters

if TYPE_CHECKING:
  from typing import Any

  from api.utils.data_classes import ConnectedMachine, MonitorPacket

LOG = logging.getLogger(__name__)

DEFAULT_CONFIG = {
  "alert_targets": ["ntfy"],
  "alert_interval": 86400,
  "cpu_threshold": -1,
  "mem_threshold": 90,
  "disk_threshold": 90,
}


def hash(message: str) -> str:
  return hashlib.sha512(message.encode()).digest().hex()


# extra_config["usagealert"] = {
#   "alert_targets": ["Phone 1", "Phone 2"]
#   "alert_interval": 86400 # Alert every 24 hours
#   "cpu_threshold": -1, # Anything below 0 disables alerts
#   "mem_threshold": 90 # Ram used percent from 0-100
#   "disk_threshold": 90 # Disk used percent from 0-100
#   "raw_alert": {
#     "extra/extendedstats/disk/sdab/": {
#       "value": "(used/total)*100", # All of the first-level keys are passed into this as variables for use.
#       "threshold": 90 # When value is over this, alert
#       "message": "{name} disk b is over 90%!", # Message to send
#     }
#   }
#   # Same thing for processed_alert
#
# }

def get_value(d: dict, key: str, default: Any = None) -> Any:
  "Extract a value from a dictionary, following / in key name."
  if isinstance(key, str):
    if "/" in key:
      split: list[str] = key.split("/")
      first_level = split.pop(0)
      second_level = split[0]
      rest = "/".join(split)
      value = d.get(first_level, default)
      if not isinstance(value, dict):
        # We can't index a non-dict. Return and ignore recursion.
        return value
      elif second_level not in value:
        return default
      else:
        return get_value(value, rest, default)
    else:
      return d.get(key, default)
  else:
    return d.get(key, default)

# This script will alert phones when machine stat usage reaches a threshold (configured in extra_config or default to 90%)
class UsageScript(Script, name="usage"):
  evaluator: py_expression_eval.Parser
  sent_alerts: dict[
    str, tuple[int, str]
  ]  # Machine name: (Timestamp of last sent, Hash of message)

  # Send a new message regardless of timestamp if hash doesnt match.
  def __init__(self, app: Application) -> None:
    super().__init__(app)
    self.evaluator = py_expression_eval.Parser()
    self.sent_alerts = {}

  async def run(self, packet: MonitorPacket, machine: ConnectedMachine) -> None:
    if "usagealert" not in machine.extra_config:
      # Set in the defaults
      machine.extra_config["usagealert"] = copy.deepcopy(DEFAULT_CONFIG)
      if not await machine.write_extra_config(self.pool):
        LOG.warning(f"Failed to write default config for {machine.name}!")

    alert_config = machine.extra_config["usagealert"]

    message = f"Alert for {machine.name}:\n"

    if "cpu_threshold" in alert_config and alert_config["cpu_threshold"] > 0:
      if packet.cpu["1m"] > alert_config["cpu_threshold"]:
        message += f"CPU @ {packet.cpu['1m']} (Over limit of {alert_config['cpu_threshold']})\n"

    if "mem_threshold" in alert_config and alert_config["mem_threshold"] > 0:
      ram_percent = (packet.ram["used"] / packet.ram["total"]) * 100
      print(f"[SCRIPTS] [USAGE] [{machine.name}] {ram_percent} > {alert_config['mem_threshold']}")
      if ram_percent > alert_config["mem_threshold"]:
        message += f"RAM @ {round(ram_percent,1)}% (Over limit of {alert_config['mem_threshold']}%)\n"

    self.app.LOG.info(f"{alert_config}")
    if "disk_threshold" in alert_config and alert_config["disk_threshold"] > 0:
      disk_percent = (packet.disk["used"] / packet.disk["total"]) * 100
      if disk_percent > alert_config["disk_threshold"]:
        message += f"Disk @ {round(disk_percent,1)}% (Over limit of {alert_config['disk_threshold']}%)\n"

    if "raw_alert" in alert_config:
      for base_key, data in alert_config["raw_alert"].items():
        # First check if all required values are present.
        ok,missing = validate_parameters(data, ["value","message","threshold"])
        if not ok:
          LOG.warning(f"{machine.name} raw_alert for {base_key} is missing parameter {missing}!")
          continue

        raw_data: dict = get_value(packet.raw, base_key)
        if raw_data is None:
          LOG.warning(f"{machine.name} raw alert for {base_key} couldn't find data in packet.raw!")
          continue

        equation = data["value"]
        variables = {}
        for key,value in raw_data.items():
          if isinstance(value, (int, float)):
            variables[key] = value
        
        parsed: py_expression_eval.Expression = self.evaluator.parse(equation)
        result = parsed.evaluate(variables)

        threshold = data["threshold"]
        if result > threshold:
          alert_message: str = data["message"]
          if not alert_message.endswith("\n"):
            alert_message += "\n"
          message += alert_message

    if "processed_alert" in alert_config:
      packet_out = await packet.out(machine.plugins, machine)
      for base_key, data in alert_config["processed_alert"].items():
        # First check if all required values are present.
        ok,missing = validate_parameters(data, ["value","message","threshold"])
        if not ok:
          LOG.warning(f"{machine.name} processed_alert for {base_key} is missing parameter {missing}!")
          continue

        raw_data: dict = get_value(packet_out, base_key)
        if raw_data is None:
          LOG.warning(f"{machine.name} processed alert for {base_key} couldn't find data in packet.out!")
          continue

        equation = data["value"]
        variables = {}
        for key,value in raw_data.items():
          if isinstance(value, (int, float)):
            variables[key] = value
        
        parsed: py_expression_eval.Expression = self.evaluator.parse(equation)
        result = parsed.evaluate(variables)

        threshold = data["threshold"]
        if result > threshold:
          alert_message: str = data["message"]
          if not alert_message.endswith("\n"):
            alert_message += "\n"
          message += alert_message

    message_hash = hash(message)

    if machine.name in self.sent_alerts:
      sent, mhash = self.sent_alerts[machine.name]

      # If we're still on cooldown and the message hash is identical, do not send
      if (
        sent + alert_config["alert_interval"] > time.time()
        and mhash == message_hash
      ):
        return
    # If we're not on cooldown OR the message hash is different, send.
    if "ntfy" in alert_config["alert_targets"]:
      self.app.LOG.warning(f"Sending alert for {machine.name} over ntfy!")
      await self.send_ntfy_notification(message, title=f"{machine.name} alert", priority=4, click=machine.url(["basicstats"]))
    self.sent_alerts[machine.name] = (time.time(), message_hash)