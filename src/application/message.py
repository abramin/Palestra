from dataclasses import dataclass, fields

ALLOWED_PRIMITIVES = (str, int, float, bool, type(None))


@dataclass
class Message:
    """Base class for Commands and Queries - enforces primitive-only fields."""

    def __post_init__(self):
        for f in fields(self):
            value = getattr(self, f.name)
            if not self._is_primitive(value):
                raise TypeError(
                    f"Field '{f.name}' must be a primitive type "
                    f"(str, int, float, bool, None, list, dict), got {type(value).__name__}"
                )

    def _is_primitive(self, obj) -> bool:
        if obj is None or isinstance(obj, ALLOWED_PRIMITIVES):
            return True
        if isinstance(obj, list):
            return all(self._is_primitive(item) for item in obj)
        if isinstance(obj, dict):
            return all(
                isinstance(k, str) and self._is_primitive(v)
                for k, v in obj.items()
            )
        return False
