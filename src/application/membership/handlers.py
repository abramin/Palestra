from typing import Callable, Protocol

from src.application.membership.commands import RegisterUserCommand
from src.application.unit_of_work import UnitOfWork
from src.domain.membership.email import Email
from src.domain.membership.events import UserRegisteredEvent
from src.domain.membership.exceptions import EmailAlreadyExistsError


class EventBus(Protocol):
    def publish(self, events: list) -> None: ...


class RegisterUserResult:
    def __init__(self, user_id: str, email: str):
        self.user_id = user_id
        self.email = email


class RegisterUserHandler:
    def __init__(
        self,
        unit_of_work_factory: Callable[[], UnitOfWork],
        event_bus: EventBus,
    ):
        self.__unit_of_work_factory = unit_of_work_factory
        self.__event_bus = event_bus

    def handle(self, command: RegisterUserCommand) -> RegisterUserResult:
        email = Email(command.email)

        with self.__unit_of_work_factory() as uow:
            if uow.user_repository.exists_by_email(str(email)):
                raise EmailAlreadyExistsError(
                    f"User with email {command.email} already exists."
                )

            user = uow.user_repository.create(
                email=str(email),
                password=command.password,
                first_name=command.first_name,
                last_name=command.last_name,
            )
            uow.commit()

        event = UserRegisteredEvent(
            user_id=str(user.id),
            email=str(email),
            first_name=command.first_name,
            last_name=command.last_name,
        )
        self.__event_bus.publish([event])

        return RegisterUserResult(user_id=str(user.id), email=str(email))
