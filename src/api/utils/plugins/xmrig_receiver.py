from __future__ import annotations

from typing import TYPE_CHECKING
from api.utils.data_classes import Plugin

if TYPE_CHECKING:
  pass

class XmrigPlugin(Plugin, name="xmrig"):
  pass