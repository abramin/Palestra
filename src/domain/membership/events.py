from dataclasses import dataclass

from src.domain.shared.base import DomainEvent


@dataclass
class UserRegisteredEvent(DomainEvent):
    user_id: str
    email: str
    first_name: str
    last_name: str
