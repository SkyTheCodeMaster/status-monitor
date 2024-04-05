from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  pass

def validate_parameters(data: dict|list, params: list[str]) -> tuple[bool,str]:
  for param in params:
    if param not in data:
      return False,param
  return True,""