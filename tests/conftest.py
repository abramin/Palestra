"""
Shared pytest fixtures for Palestra tests.
"""
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Provides a DRF API test client."""
    return APIClient()


@pytest.fixture
def event_collector():
    """
    Collects domain events for test assertions.

    Use this instead of mocking the event bus to verify
    events are published with correct data.
    """

    class EventCollector:
        def __init__(self):
            self.events = []

        def publish(self, events):
            """Collect events instead of publishing."""
            if isinstance(events, list):
                self.events.extend(events)
            else:
                self.events.append(events)

        def clear(self):
            """Clear collected events between tests."""
            self.events.clear()

        def get_events_of_type(self, event_type):
            """Filter events by type for targeted assertions."""
            return [e for e in self.events if isinstance(e, event_type)]

    return EventCollector()


@pytest.fixture
def registered_user(db):
    """
    Creates a registered user for tests that need an existing user.
    Returns a dict with user data (password in plaintext for test assertions).
    """
    from src.infrastructure.persistence.models import User as UserModel

    user = UserModel.objects.create_user(
        email="existing@example.com",
        password="ExistingPass1!",
        first_name="Existing",
        last_name="User",
    )

    return {
        "id": str(user.id),
        "email": user.email,
        "password": "ExistingPass1!",  # Plaintext for login tests
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
