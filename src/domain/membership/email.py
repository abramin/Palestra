import re


class Email:
    def __init__(self, value: str):
        value = value.strip()
        if not self._is_valid_email(value):
            raise InvalidEmailError(f"Invalid email address: {value}")
        self.value = value.lower()

    def _is_valid_email(self, value: str) -> bool:
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(pattern, value) is not None

    def __str__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, Email):
            return self.value == other.value
        return False


class InvalidEmailError(Exception):
    pass
