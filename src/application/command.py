from dataclasses import dataclass, fields
import json
from typing import Protocol

@dataclass
class Command:
    def __post_init__(self):
        for f in fields(self):
            value = getattr(self, f.name)
            if not self._is_json_serializable(value):
                raise TypeError("Command contains non-JSON-serializable fields")

    def _is_json_serializable(self, obj):
        try:
            json.dumps(obj)
            return True
        except (TypeError, OverflowError):
            return False