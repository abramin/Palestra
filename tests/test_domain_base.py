from dataclasses import dataclass
from typing import Protocol

import pytest

from src.application import Command, Query, UnitOfWork
from src.domain.shared import AggregateRoot, DomainEvent


class SampleAggregate(AggregateRoot):
    pass


@dataclass
class SampleCommand(Command):
    user_id: str
    count: int


@dataclass
class BadCommand(Command):
    payload: object


@dataclass
class SampleQuery(Query):
    user_id: str
    active_only: bool


@dataclass
class BadQuery(Query):
    payload: object


@dataclass
class SampleEvent(DomainEvent):
    name: str
    payload: dict


@dataclass
class BadEvent(DomainEvent):
    payload: object

def test_aggregate_root_records_and_pulls_events() -> None:
    agg = SampleAggregate("agg-1")
    event = SampleEvent(name="created", payload={"ok": True})

    agg._record(event)
    assert agg.pull_events() == [event]
    assert agg.pull_events() == []


def test_command_and_query_are_dataclasses() -> None:
    assert hasattr(Command, "__dataclass_fields__")
    assert hasattr(Query, "__dataclass_fields__")


def test_command_rejects_non_json_primitives() -> None:
    with pytest.raises((TypeError, ValueError)):
        BadCommand(payload=object())


def test_query_rejects_non_json_primitives() -> None:
    with pytest.raises((TypeError, ValueError)):
        BadQuery(payload=object())


def test_event_rejects_non_json_primitives() -> None:
    with pytest.raises((TypeError, ValueError)):
        BadEvent(payload=object())

def test_unit_of_work_is_protocol_with_context_manager() -> None:
    assert issubclass(UnitOfWork, Protocol)
    assert hasattr(UnitOfWork, "__enter__")
    assert hasattr(UnitOfWork, "__exit__")
    assert hasattr(UnitOfWork, "commit")
