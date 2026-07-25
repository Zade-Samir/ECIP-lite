"""
Tests for Design Reasoning & ADR Creation (Prompt 096).
"""
import pytest
from services.architecture_copilot.copilot_engine import ArchitectureCopilotEngine


def test_adr_creation():
    copilot = ArchitectureCopilotEngine()
    adr = copilot.create_adr(
        title="ADR-001: Adopt Event-Driven Architecture",
        context="Monolithic synchronous HTTP calls causing latency spikes.",
        decision="Use Kafka for asynchronous domain event propagation.",
        consequences=["Improved decouplability", "Eventual consistency overhead"],
    )

    assert adr.title == "ADR-001: Adopt Event-Driven Architecture"
    assert adr.status == "PROPOSED"
    assert len(adr.consequences) == 2
