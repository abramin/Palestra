from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from src.domain.membership.exceptions import WeakPasswordError
from src.infrastructure.persistence.models import User


class UserRepository:
    def exists_by_email(self, email: str) -> bool:
        return User.objects.filter(email=email).exists()

    def create(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> User:
        try:
            validate_password(password)
        except ValidationError as e:
            raise WeakPasswordError("; ".join(e.messages)) from e

        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(password)
        user.save()
        return user

    def get_by_email(self, email: str) -> User | None:
        return User.objects.filter(email=email).first()


class DjangoUnitOfWork:
    def __init__(self):
        self.user_repository = UserRepository()
        self._transaction = None

    def __enter__(self):
        self._transaction = transaction.atomic()
        self._transaction.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._transaction.__exit__(exc_type, exc_val, exc_tb)

    def commit(self):
        pass  # Django's atomic() commits on successful exit

    def rollback(self):
        raise Exception("Rollback")  # Forces atomic() to rollback
