from dataclasses import dataclass

from src.application.command import Command


@dataclass
class RegisterUserCommand(Command):
    email: str
    password: str
    first_name: str
    last_name: str
