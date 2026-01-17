"""
Integration tests for user registration flow.

These tests hit real database boundaries and verify the complete
registration flow from command through handler to persistence.
"""
import pytest

from src.application.membership.commands import RegisterUserCommand
from src.application.membership.handlers import RegisterUserHandler
from src.domain.membership.email import InvalidEmailError
from src.domain.membership.events import UserRegisteredEvent
from src.domain.membership.exceptions import EmailAlreadyExistsError
from src.domain.membership.exceptions import WeakPasswordError
from src.infrastructure.persistence.models import User as UserModel


@pytest.fixture
def register_user_handler(db, event_collector):
    """Create handler with real UnitOfWork and event collector."""
    from src.infrastructure.persistence.unit_of_work import DjangoUnitOfWork

    def factory():
        return DjangoUnitOfWork()

    return RegisterUserHandler(
        unit_of_work_factory=factory,
        event_bus=event_collector,
    )


class TestUserRegistration_CreatesUserSuccessfully:
    """Tests successful user registration flow."""

    @pytest.mark.django_db(transaction=True)
    def test_creates_user_in_database(self, register_user_handler):
        command = RegisterUserCommand(
            email="newuser@example.com",
            password="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )

        register_user_handler.handle(command)

        assert UserModel.objects.filter(email="newuser@example.com").exists()

    @pytest.mark.django_db(transaction=True)
    def test_returns_user_id(self, register_user_handler):
        command = RegisterUserCommand(
            email="newuser@example.com",
            password="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )

        result = register_user_handler.handle(command)

        assert result.user_id is not None
        assert isinstance(result.user_id, str)

    @pytest.mark.django_db(transaction=True)
    def test_stores_hashed_password(self, register_user_handler):
        command = RegisterUserCommand(
            email="newuser@example.com",
            password="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )

        register_user_handler.handle(command)

        user = UserModel.objects.get(email="newuser@example.com")
        assert user.password != "StrongPass1!"
        assert user.check_password("StrongPass1!")

    @pytest.mark.django_db(transaction=True)
    def test_normalizes_email(self, register_user_handler):
        command = RegisterUserCommand(
            email="  NewUser@EXAMPLE.COM  ",
            password="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )

        register_user_handler.handle(command)

        assert UserModel.objects.filter(email="newuser@example.com").exists()

    @pytest.mark.django_db(transaction=True)
    def test_assigns_default_client_role(self, register_user_handler):
        command = RegisterUserCommand(
            email="newuser@example.com",
            password="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )

        register_user_handler.handle(command)

        user = UserModel.objects.get(email="newuser@example.com")
        assert user.role == UserModel.Role.CLIENT


class TestUserRegistration_PublishesEvents:
    """Tests that registration publishes correct domain events."""

    @pytest.mark.django_db(transaction=True)
    def test_publishes_user_registered_event(self, register_user_handler, event_collector):
        command = RegisterUserCommand(
            email="newuser@example.com",
            password="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )

        register_user_handler.handle(command)

        assert len(event_collector.events) == 1
        event = event_collector.events[0]
        assert isinstance(event, UserRegisteredEvent)

    @pytest.mark.django_db(transaction=True)
    def test_event_contains_user_details(self, register_user_handler, event_collector):
        command = RegisterUserCommand(
            email="newuser@example.com",
            password="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )

        register_user_handler.handle(command)

        event = event_collector.events[0]
        assert event.email == "newuser@example.com"
        assert event.first_name == "John"
        assert event.last_name == "Doe"
        assert event.user_id is not None

    @pytest.mark.django_db(transaction=True)
    def test_event_does_not_contain_password(self, register_user_handler, event_collector):
        command = RegisterUserCommand(
            email="newuser@example.com",
            password="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )

        register_user_handler.handle(command)

        event = event_collector.events[0]
        assert not hasattr(event, "password")
        assert "password" not in str(event)


class TestUserRegistration_RejectsDuplicateEmail:
    """Tests duplicate email handling."""

    @pytest.mark.django_db(transaction=True)
    def test_rejects_duplicate_email(self, register_user_handler):
        command = RegisterUserCommand(
            email="existing@example.com",
            password="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )
        register_user_handler.handle(command)

        with pytest.raises(EmailAlreadyExistsError):
            register_user_handler.handle(command)

    @pytest.mark.django_db(transaction=True)
    def test_rejects_duplicate_normalized_email(self, register_user_handler):
        command1 = RegisterUserCommand(
            email="user@example.com",
            password="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )
        register_user_handler.handle(command1)

        command2 = RegisterUserCommand(
            email="USER@EXAMPLE.COM",  # Same email, different case
            password="StrongPass1!",
            first_name="Jane",
            last_name="Doe",
        )

        with pytest.raises(EmailAlreadyExistsError):
            register_user_handler.handle(command2)


class TestUserRegistration_ValidatesInput:
    """Tests input validation at handler level."""

    @pytest.mark.django_db(transaction=True)
    def test_rejects_invalid_email(self, register_user_handler):
        command = RegisterUserCommand(
            email="not-an-email",
            password="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )

        with pytest.raises(InvalidEmailError):
            register_user_handler.handle(command)

    @pytest.mark.django_db(transaction=True)
    def test_rejects_weak_password(self, register_user_handler):
        command = RegisterUserCommand(
            email="newuser@example.com",
            password="weak",
            first_name="John",
            last_name="Doe",
        )

        with pytest.raises(WeakPasswordError):
            register_user_handler.handle(command)


class TestUserRegistration_TransactionBehavior:
    """Tests transaction rollback on failure."""

    @pytest.mark.django_db(transaction=True)
    def test_persists_user_even_if_event_publish_fails(self, db):
        """
        Per architecture: events are published AFTER transaction commits.
        If event publishing fails, the user is still persisted.
        Use outbox pattern or retry mechanism for reliable event delivery.
        """

        class FailingEventBus:
            def publish(self, events):
                raise RuntimeError("Event bus failure")

        from src.infrastructure.persistence.unit_of_work import DjangoUnitOfWork

        handler = RegisterUserHandler(
            unit_of_work_factory=lambda: DjangoUnitOfWork(),
            event_bus=FailingEventBus(),
        )

        command = RegisterUserCommand(
            email="newuser@example.com",
            password="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )

        with pytest.raises(RuntimeError):
            handler.handle(command)

        # User IS persisted - events are published after commit
        assert UserModel.objects.filter(email="newuser@example.com").exists()
