"""Factory helpers for scenario test data."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from app.models.location import ConnectionRequirement, DangerLevel, LocationConnection
from app.models.quest import Quest, QuestObjective
from app.models.scenario import (
    LocationDescriptions,
    ScenarioAct,
    ScenarioLocation,
    ScenarioProgression,
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
    quests: Sequence[Quest] | None = None,
    acts: Sequence[ScenarioAct] | None = None,
    content_packs: Sequence[str] | None = None,
) -> ScenarioSheet:
    """Create a ScenarioSheet with a single act referencing provided locations."""
    quests = list(quests) if quests is not None else []
    if acts is None:
        act_locations = [loc.id for loc in locations]
        acts = [
            ScenarioAct(id="act1", name="Act 1", locations=act_locations, objectives=[], quests=[q.id for q in quests])
        ]
    else:
        acts = list(acts)
    content_packs = list(content_packs) if content_packs is not None else ["srd"]
    return ScenarioSheet(
        id=scenario_id,
        title=title,
        description=description,
        starting_location_id=starting_location_id,
        locations=list(locations),
        quests=quests,
        progression=ScenarioProgression(acts=acts),
        content_packs=content_packs,
    )


def make_quest(
    *,
    quest_id: str = "quest-1",
    name: str = "Find the Relic",
    description: str = "Recover the lost relic from the forest.",
) -> Quest:
    """Create a simple quest with a single objective."""
    return Quest(
        id=quest_id,
        name=name,
        description=description,
        objectives=[QuestObjective(id=f"objective-{quest_id}", description="Reach the forest edge.")],
        rewards_description="Renown",
    )
