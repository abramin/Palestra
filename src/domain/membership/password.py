from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class WeakPasswordError(Exception):
    pass


class Password:
    MIN_LENGTH = 12
    SPECIAL_CHARACTERS = "!@#$%^&*"

    _hasher = PasswordHasher()

    def __init__(self, hashed_value: str):
        self._hashed_value = hashed_value

    @property
    def hashed_value(self) -> str:
        return self._hashed_value

    @classmethod
    def create(cls, plaintext: str) -> "Password":
        cls._validate_password(plaintext)
        hashed_val = cls._hasher.hash(plaintext)
        return Password(hashed_val)

    @classmethod
    def from_hash(cls, hashed_value: str) -> "Password":
        return Password(hashed_value)

    def verify(self, plaintext: str) -> bool:
        try:
            self._hasher.verify(self._hashed_value, plaintext)
            return True
        except VerifyMismatchError:
            return False

    def needs_rehash(self) -> bool:
        return self._hasher.check_needs_rehash(self._hashed_value)

    @classmethod
    def _validate_password(cls, password: str) -> None:
        if len(password) < cls.MIN_LENGTH:
            raise WeakPasswordError(
                f"Password must be at least {cls.MIN_LENGTH} characters long."
            )
        if not any(c.islower() for c in password):
            raise WeakPasswordError(
                "Password must contain at least one lowercase letter."
            )
        if not any(c.isupper() for c in password):
            raise WeakPasswordError(
                "Password must contain at least one uppercase letter."
            )
        if not any(c.isdigit() for c in password):
            raise WeakPasswordError("Password must contain at least one digit.")
        if not any(c in cls.SPECIAL_CHARACTERS for c in password):
            raise WeakPasswordError(
                "Password must contain at least one special character."
            )
