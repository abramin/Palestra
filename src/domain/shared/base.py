from typing import List
from dataclasses import dataclass, fields
import json

@dataclass
class DomainEvent:
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


class AggregateRoot():
    def __init__(self, id: str):
        self.id = id
        self.__events: List[DomainEvent] = []

    def _record(self, event: DomainEvent) -> None:
        self.__events.append(event)

    def pull_events(self) -> List[DomainEvent]:
        events = self.__events.copy()
        self.__events.clear()
        return events

