"""Factory helpers for scenario test data."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from app.models.location import ConnectionRequirement, DangerLevel, LocationConnection
from app.models.scenario import (
    LocationDescriptions,
    ScenarioLocation,
    ScenarioSheet,
)


def make_location_connection(
    *,
    to_location_id: str,
    description: str,
    direction: str | None = None,
    requirements: Sequence[ConnectionRequirement] | None = None,
    is_visible: bool = True,
    is_accessible: bool = True,
) -> LocationConnection:
    """Create a LocationConnection."""
    return LocationConnection(
        to_location_id=to_location_id,
        description=description,
        direction=direction,
        requirements=list(requirements) if requirements else [],
        is_visible=is_visible,
        is_accessible=is_accessible,
    )


def make_location(
    *,
    location_id: str,
    name: str,
    description: str,
    connections: Iterable[LocationConnection] | None = None,
    danger_level: DangerLevel = DangerLevel.MODERATE,
    descriptions: LocationDescriptions | None = None,
) -> ScenarioLocation:
    """Create a ScenarioLocation with optional connections."""
    return ScenarioLocation(
        id=location_id,
        name=name,
        description=description,
        connections=list(connections) if connections is not None else [],
        descriptions=descriptions,
        danger_level=danger_level,
    )


def make_scenario(
    *,
    scenario_id: str = "adventure",
    title: str = "Simple Adventure",
    description: str = "A short trip beyond town.",
    starting_location_id: str,
    locations: Sequence[ScenarioLocation],
    content_packs: Sequence[str] | None = None,
) -> ScenarioSheet:
    """Create a ScenarioSheet with provided locations."""
    content_packs = list(content_packs) if content_packs is not None else ["srd"]
    return ScenarioSheet(
        id=scenario_id,
        title=title,
        description=description,
        starting_location_id=starting_location_id,
        locations=list(locations),
        content_packs=content_packs,
    )
