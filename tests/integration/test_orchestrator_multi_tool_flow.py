"""Integration test covering a full orchestrator multi-tool turn."""

from __future__ import annotations

import json
import random
from collections.abc import AsyncIterator, Callable, Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import TypedDict, cast

import pytest

from app.agents.core.base import BaseAgent, ToolFunction
from app.agents.core.dependencies import AgentDependencies
from app.agents.core.types import AgentType
from app.container import Container
from app.interfaces.agents.summarizer import ISummarizerAgent
from app.models.ai_response import CompleteResponse, NarrativeResponse, StreamEvent, StreamEventType
from app.models.attributes import EntityType
from app.models.combat import MonsterSpawnInfo
from app.models.game_state import GameEventType, GameState, Message, MessageRole
from app.models.instances.monster_instance import MonsterInstance
from app.models.instances.npc_instance import NPCInstance
from app.models.location import DangerLevel
from app.models.memory import MemoryEventKind, WorldEventContext
from app.models.scenario import LocationDescriptions
from app.models.tool_results import RollDiceResult
from app.services.ai.ai_service import AIService
from app.services.ai.orchestrator_service import AgentOrchestrator
from app.services.common.path_resolver import PathResolver
from app.tools import combat_tools, dice_tools, entity_tools, inventory_tools, location_tools, quest_tools
from tests.factories import make_game_state, make_location, make_location_connection, make_quest

QUEST_ID = "moonlit-knowledge"
QUEST_OBJECTIVE_ID = f"objective-{QUEST_ID}"


class SharedState(TypedDict):
    """Mutable shared data exchanged between scripted agents."""

    monster_id: str
    monster_name: str
    ability_total: int
    fireball_total: int
    attack_total: int
    player_damage_total: int
    quest_id: str
    objective_id: str


class _NarrativeScriptAgent(BaseAgent):
    """Stub narrative agent that executes exploration and setup tools."""

    def __init__(
        self,
        deps_builder: Callable[[GameState], AgentDependencies],
        *,
        tool_kwargs: dict[str, object],
        response_text: str,
        aftermath_text: str,
        shared_state: SharedState,
    ) -> None:
        self._deps_builder = deps_builder
        self._tool_kwargs = tool_kwargs
        self._response_text = response_text
        self._aftermath_text = aftermath_text
        self._shared: SharedState = shared_state
        self._stage = 0
        self.prompts: list[str] = []

    def get_required_tools(self) -> list[ToolFunction]:
        return [
            location_tools.change_location,
            location_tools.discover_secret,
            location_tools.update_location_state,
            quest_tools.start_quest,
            dice_tools.roll_dice,
            combat_tools.spawn_monsters,
            combat_tools.start_combat,
        ]

    async def process(self, prompt: str, game_state: GameState, stream: bool = True) -> AsyncIterator[StreamEvent]:
        self.prompts.append(prompt)
        deps = self._deps_builder(game_state)
        ctx = SimpleNamespace(deps=deps)

        if self._stage == 0:
            await location_tools.change_location(ctx, **self._tool_kwargs)
            await location_tools.discover_secret(ctx, secret_id="moonlit-archive")
            await location_tools.update_location_state(
                ctx,
                danger_level="low",
                add_effect="soothing-luminescence",
            )

            self._shared["quest_id"] = QUEST_ID
            self._shared["objective_id"] = QUEST_OBJECTIVE_ID
            await quest_tools.start_quest(ctx, quest_id=QUEST_ID)

            ability_check = cast(
                RollDiceResult,
                await dice_tools.roll_dice(
                    ctx,
                    dice="2d20kh",
                    modifier=4,
                    roll_type="ability_check",
                    purpose="Moonlit Perception",
                    ability="Wisdom",
                    skill="Perception",
                ),
            )
            self._shared["ability_total"] = ability_check.total

            existing_ids = {monster.instance_id for monster in game_state.monsters}
            await combat_tools.spawn_monsters(
                ctx,
                monsters=[MonsterSpawnInfo(monster_index="ogre", quantity=1)],
            )
            new_monsters: list[MonsterInstance] = [m for m in game_state.monsters if m.instance_id not in existing_ids]
            if not new_monsters:
                raise AssertionError("Expected spawn_monsters to add a creature")
            spawned = new_monsters[0]
            self._shared["monster_id"] = spawned.instance_id
            self._shared["monster_name"] = spawned.display_name

            await combat_tools.start_combat(ctx, entity_ids=[spawned.instance_id])

            deps.conversation_service.add_message(
                game_state=game_state,
                role=MessageRole.DM,
                content=self._response_text,
                agent_type=AgentType.NARRATIVE,
                location=game_state.location,
                npcs_mentioned=[],
                combat_round=0,
            )

            self._stage = 1

            yield StreamEvent(
                type=StreamEventType.COMPLETE,
                content=NarrativeResponse(narrative=self._response_text),
            )
            return

        deps.conversation_service.add_message(
            game_state=game_state,
            role=MessageRole.DM,
            content=self._aftermath_text,
            agent_type=AgentType.NARRATIVE,
            location=game_state.location,
            npcs_mentioned=[],
            combat_round=0,
        )
        self._stage += 1

        yield StreamEvent(
            type=StreamEventType.COMPLETE,
            content=NarrativeResponse(narrative=self._aftermath_text),
        )


class _CombatScriptAgent(BaseAgent):
    """Stub combat agent performing spell damage, retaliation, and cleanup."""

    def __init__(
        self,
        deps_builder: Callable[[GameState], AgentDependencies],
        *,
        shared_state: SharedState,
        opening_text: str,
        resolution_text: str,
    ) -> None:
        self._deps_builder = deps_builder
        self._shared: SharedState = shared_state
        self._stage = 0
        self._opening_text = opening_text
        self._resolution_text = resolution_text
        self.prompts: list[str] = []

    def get_required_tools(self) -> list[ToolFunction]:
        return [
            dice_tools.roll_dice,
            entity_tools.update_hp,
            combat_tools.next_turn,
            combat_tools.end_combat,
            inventory_tools.modify_inventory,
            inventory_tools.modify_currency,
            quest_tools.complete_objective,
        ]

    async def process(self, prompt: str, game_state: GameState, stream: bool = True) -> AsyncIterator[StreamEvent]:
        self.prompts.append(prompt)
        deps = self._deps_builder(game_state)
        ctx = SimpleNamespace(deps=deps)

        monster_id = self._shared["monster_id"]
        if not monster_id:
            raise AssertionError("Combat script requires spawned monster id")

        if self._stage == 0:
            fireball = cast(
                RollDiceResult,
                await dice_tools.roll_dice(
                    ctx,
                    dice="8d6",
                    modifier=5,
                    roll_type="damage",
                    purpose="Wizard's Fireball",
                ),
            )
            self._shared["fireball_total"] = fireball.total

            deps.conversation_service.add_message(
                game_state=game_state,
                role=MessageRole.DM,
                content=self._opening_text,
                agent_type=AgentType.COMBAT,
                location=game_state.location,
                npcs_mentioned=[self._shared["monster_name"]],
                combat_round=game_state.combat.round_number,
                combat_occurrence=game_state.combat.combat_occurrence,
            )

            self._stage = 1

            yield StreamEvent(
                type=StreamEventType.COMPLETE,
                content=NarrativeResponse(narrative=self._opening_text),
            )
            return

        if self._stage == 1:
            fireball_total = self._shared["fireball_total"]
            attack_roll = cast(
                RollDiceResult,
                await dice_tools.roll_dice(
                    ctx,
                    dice="2d20kh",
                    modifier=6,
                    roll_type="attack",
                    purpose="Ogre Counterattack",
                    ability="Dexterity",
                ),
            )
            self._shared["attack_total"] = attack_roll.total

            await entity_tools.update_hp(
                ctx,
                entity_id=monster_id,
                entity_type=EntityType.MONSTER,
                amount=-fireball_total,
                damage_type="fire",
            )

            monster_entity = game_state.get_entity_by_id(EntityType.MONSTER, monster_id)
            if monster_entity is None:
                raise AssertionError("Expected ogre to remain present after damage application")
            remaining_hp = monster_entity.state.hit_points.current

            await combat_tools.next_turn(ctx)

            retaliation = cast(
                RollDiceResult,
                await dice_tools.roll_dice(
                    ctx,
                    dice="3d6",
                    modifier=2,
                    roll_type="damage",
                    purpose="Ogre Smash",
                ),
            )
            self._shared["player_damage_total"] = retaliation.total

            await entity_tools.update_hp(
                ctx,
                entity_id=game_state.character.instance_id,
                entity_type=EntityType.PLAYER,
                amount=-retaliation.total,
                damage_type="bludgeoning",
            )

            await combat_tools.next_turn(ctx)

            if remaining_hp > 0:
                await entity_tools.update_hp(
                    ctx,
                    entity_id=monster_id,
                    entity_type=EntityType.MONSTER,
                    amount=-remaining_hp,
                    damage_type="force",
                )

            combat_round = game_state.combat.round_number
            combat_occurrence = game_state.combat.combat_occurrence
            if game_state.combat.is_active:
                await combat_tools.end_combat(ctx)

            await inventory_tools.modify_inventory(ctx, item_index="potion-of-healing", quantity=1)
            await inventory_tools.modify_currency(ctx, gold=5)

            quest_id = self._shared["quest_id"]
            objective_id = self._shared["objective_id"]
            if not quest_id or not objective_id:
                raise AssertionError("Quest identifiers missing from shared state")
            await quest_tools.complete_objective(ctx, quest_id=quest_id, objective_id=objective_id)

            deps.conversation_service.add_message(
                game_state=game_state,
                role=MessageRole.DM,
                content=self._resolution_text,
                agent_type=AgentType.COMBAT,
                location=game_state.location,
                npcs_mentioned=[self._shared["monster_name"]],
                combat_round=combat_round,
                combat_occurrence=combat_occurrence,
            )

            self._stage = 2

            yield StreamEvent(
                type=StreamEventType.COMPLETE,
                content=NarrativeResponse(narrative=self._resolution_text),
            )
            return

        yield StreamEvent(
            type=StreamEventType.COMPLETE,
            content=NarrativeResponse(narrative=self._resolution_text),
        )


class _StubSummarizer(BaseAgent):
    """Summarizer stub used only to satisfy orchestrator interface."""

    def get_required_tools(self) -> list[ToolFunction]:
        return []

    async def summarize_for_combat(self, game_state: GameState) -> str:
        return "combat summary"

    async def summarize_combat_end(self, game_state: GameState) -> str:
        return "combat end summary"

    async def summarize_location_session(
        self,
        game_state: GameState,
        location_id: str,
        messages: Sequence[Message],
    ) -> str:
        return "location summary"

    async def summarize_npc_interactions(
        self,
        game_state: GameState,
        npc: NPCInstance,
        messages: Sequence[Message],
    ) -> str:
        return "npc summary"

    async def summarize_world_update(
        self,
        game_state: GameState,
        event_kind: MemoryEventKind,
        messages: Sequence[Message],
        context: WorldEventContext,
    ) -> str:
        return "world summary"

    async def process(self, prompt: str, game_state: GameState, stream: bool = True) -> AsyncIterator[StreamEvent]:
        if game_state.game_id == "__noop__":
            yield StreamEvent(
                type=StreamEventType.COMPLETE,
                content=NarrativeResponse(narrative=""),
            )
        return


def _scrub_timestamps(events: list[dict[str, object]]) -> list[dict[str, object]]:
    scrubbed: list[dict[str, object]] = []
    for event in events:
        scrubbed_event = dict(event)
        scrubbed_event["timestamp"] = "<timestamp>"
        scrubbed.append(scrubbed_event)
    return scrubbed


def _scrub_history_timestamps(messages: list[dict[str, object]]) -> list[dict[str, object]]:
    scrubbed: list[dict[str, object]] = []
    for message in messages:
        scrubbed_message = dict(message)
        scrubbed_message["timestamp"] = "<timestamp>"
        scrubbed.append(scrubbed_message)
    return scrubbed


@pytest.mark.asyncio
async def test_orchestrator_persists_tool_events(tmp_path: Path) -> None:
    random.seed(1337)

    summarizer_stub = _StubSummarizer()
    container = Container(summarizer_agent=cast(ISummarizerAgent, summarizer_stub))
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    path_resolver = cast(PathResolver, container.path_resolver)
    path_resolver.saves_dir = saves_dir

    target_location = make_location(
        location_id="moonlit-library",
        name="Moonlit Library",
        description="Stacks of ancient tomes glow with soft light.",
        descriptions=LocationDescriptions(
            first_visit="Soft blue flames illuminate the towering shelves.",
            return_visit="The Moonlit Library greets you with silent reverence.",
        ),
    )

    game_state = make_game_state(additional_locations=[target_location.id])
    scenario = game_state.scenario_instance.sheet
    for index, location in enumerate(scenario.locations):
        if location.id == target_location.id:
            scenario.locations[index] = target_location
            break
    updated_target = scenario.get_location(target_location.id)

    quest = make_quest(
        quest_id=QUEST_ID,
        name="Secrets of the Moonlit Library",
        description="Unearth the lore hidden within the radiant stacks.",
    )
    scenario.quests.append(quest)
    first_act = scenario.progression.acts[0]
    if QUEST_ID not in first_act.quests:
        first_act.quests.append(QUEST_ID)
    assert updated_target is not None

    start_location_id = scenario.starting_location_id
    start_location = scenario.get_location(start_location_id)
    assert start_location is not None
    start_location.connections.append(
        make_location_connection(
            to_location_id=updated_target.id,
            description="A lantern-lit path winds toward a moonlit archway.",
        )
    )
    game_state.scenario_instance.location_states[start_location_id].mark_visited()

    repository_provider = container.repository_factory

    def _build_narrative_deps(state: GameState) -> AgentDependencies:
        return AgentDependencies(
            game_state=state,
            event_bus=container.event_bus,
            agent_type=AgentType.NARRATIVE,
            scenario_service=container.scenario_service,
            item_repository=repository_provider.get_item_repository_for(state),
            monster_repository=repository_provider.get_monster_repository_for(state),
            spell_repository=repository_provider.get_spell_repository_for(state),
            conversation_service=container.conversation_service,
            event_manager=container.event_manager,
            metadata_service=container.metadata_service,
            save_manager=container.save_manager,
            action_service=container.action_service,
        )

    def _build_combat_deps(state: GameState) -> AgentDependencies:
        return AgentDependencies(
            game_state=state,
            event_bus=container.event_bus,
            agent_type=AgentType.COMBAT,
            scenario_service=container.scenario_service,
            item_repository=repository_provider.get_item_repository_for(state),
            monster_repository=repository_provider.get_monster_repository_for(state),
            spell_repository=repository_provider.get_spell_repository_for(state),
            conversation_service=container.conversation_service,
            event_manager=container.event_manager,
            metadata_service=container.metadata_service,
            save_manager=container.save_manager,
            action_service=container.action_service,
        )

    container.game_state_manager.store_game(game_state)
    container.save_manager.save_game(game_state)

    shared: SharedState = {
        "monster_id": "",
        "monster_name": "",
        "ability_total": 0,
        "fireball_total": 0,
        "attack_total": 0,
        "player_damage_total": 0,
        "quest_id": "",
        "objective_id": "",
    }

    narrative_agent = _NarrativeScriptAgent(
        _build_narrative_deps,
        tool_kwargs={"location_id": updated_target.id},
        response_text="The heroes arrive at the Moonlit Library.",
        aftermath_text="Calm returns as the Moonlit Library settles after the clash.",
        shared_state=shared,
    )
    combat_agent = _CombatScriptAgent(
        _build_combat_deps,
        shared_state=shared,
        opening_text="A roaring fireball engulfs the ogre in lunar light.",
        resolution_text="With a final blast, the ogre falls and the spoils are claimed.",
    )
    orchestrator = AgentOrchestrator(
        narrative_agent=narrative_agent,
        combat_agent=combat_agent,
        summarizer_agent=summarizer_stub,
        combat_service=container.combat_service,
        event_bus=container.event_bus,
        game_service=container.game_service,
        metadata_service=container.metadata_service,
        conversation_service=container.conversation_service,
        agent_lifecycle_service=container.agent_lifecycle_service,
    )
    ai_service = AIService(orchestrator)

    initial_player_hp = game_state.character.state.hit_points.current
    initial_currency = game_state.character.state.currency.model_copy()

    responses_turn_one = [response async for response in ai_service.generate_response("Travel east", game_state)]
    await container.event_bus.wait_for_completion()

    responses_turn_two = [response async for response in ai_service.generate_response("Press the attack", game_state)]
    await container.event_bus.wait_for_completion()

    responses = responses_turn_one + responses_turn_two

    assert len(responses) == 4
    assert all(isinstance(response, CompleteResponse) for response in responses)
    complete_responses = cast(list[CompleteResponse], responses)

    assert [response.narrative for response in complete_responses] == [
        "The heroes arrive at the Moonlit Library.",
        "A roaring fireball engulfs the ogre in lunar light.",
        "With a final blast, the ogre falls and the spoils are claimed.",
        "Calm returns as the Moonlit Library settles after the clash.",
    ]
    assert game_state.location == updated_target.name
    assert game_state.scenario_instance.current_location_id == updated_target.id
    assert game_state.description == updated_target.get_description("first_visit")
    assert game_state.story_notes[-1].endswith(updated_target.name)

    location_state = game_state.scenario_instance.location_states[updated_target.id]
    assert location_state.discovered_secrets == ["moonlit-archive"]
    assert location_state.danger_level is DangerLevel.LOW
    assert "soothing-luminescence" in location_state.active_effects

    assert isinstance(shared["ability_total"], int) and shared["ability_total"] > 0
    assert isinstance(shared["monster_id"], str) and shared["monster_id"]
    assert isinstance(shared["monster_name"], str) and shared["monster_name"]
    assert isinstance(shared["fireball_total"], int) and shared["fireball_total"] > 0
    assert isinstance(shared["attack_total"], int) and shared["attack_total"] > 0
    assert isinstance(shared["player_damage_total"], int) and shared["player_damage_total"] > 0
    assert not any(mon.instance_id == shared["monster_id"] for mon in game_state.monsters)
    assert game_state.combat.is_active is False

    player_damage = shared["player_damage_total"]
    final_player_hp = game_state.character.state.hit_points.current
    assert final_player_hp == max(0, initial_player_hp - player_damage)

    inventory_by_index = {item.index: item for item in game_state.character.state.inventory}
    potion = inventory_by_index.get("potion-of-healing")
    assert potion is not None and potion.quantity == 1

    final_currency = game_state.character.state.currency
    assert final_currency.gold == initial_currency.gold + 5
    assert final_currency.silver == initial_currency.silver
    assert final_currency.copper == initial_currency.copper

    active_quest_ids = {quest.id for quest in game_state.scenario_instance.active_quests}
    assert QUEST_ID not in active_quest_ids
    assert QUEST_ID in game_state.scenario_instance.completed_quest_ids

    expected_conversation = [
        (MessageRole.DM, "The heroes arrive at the Moonlit Library.", AgentType.NARRATIVE, None, None),
        (MessageRole.DM, "[Summary: combat summary]", AgentType.COMBAT, 1, 1),
        (
            MessageRole.DM,
            "A roaring fireball engulfs the ogre in lunar light.",
            AgentType.COMBAT,
            1,
            1,
        ),
        (
            MessageRole.DM,
            "With a final blast, the ogre falls and the spoils are claimed.",
            AgentType.COMBAT,
            2,
            1,
        ),
        (MessageRole.DM, "[Summary: combat end summary]", AgentType.NARRATIVE, None, None),
        (
            MessageRole.DM,
            "Calm returns as the Moonlit Library settles after the clash.",
            AgentType.NARRATIVE,
            None,
            None,
        ),
    ]

    actual_conversation = [
        (msg.role, msg.content, msg.agent_type, msg.combat_round, msg.combat_occurrence)
        for msg in game_state.conversation_history
    ]
    assert actual_conversation == expected_conversation

    tool_sequence = [event.tool_name for event in game_state.game_events if event.event_type is GameEventType.TOOL_CALL]
    assert tool_sequence == [
        "change_location",
        "discover_secret",
        "update_location_state",
        "start_quest",
        "roll_dice",
        "spawn_monsters",
        "start_combat",
        "roll_dice",
        "roll_dice",
        "update_hp",
        "next_turn",
        "roll_dice",
        "update_hp",
        "next_turn",
        "update_hp",
        "end_combat",
        "modify_inventory",
        "modify_currency",
        "complete_objective",
    ]

    save_dir = saves_dir / game_state.scenario_id / game_state.game_id
    events_path = save_dir / "game_events.json"
    assert events_path.exists()

    container.save_manager.save_game(game_state)

    with events_path.open(encoding="utf-8") as fh:
        persisted_events = json.load(fh)

    scrubbed_events = _scrub_timestamps(persisted_events)
    events_golden_path = Path(__file__).parent / "goldens" / "orchestrator_multi_tool_flow_events.json"
    with events_golden_path.open(encoding="utf-8") as fh:
        golden_events = json.load(fh)

    assert scrubbed_events == golden_events

    conversation_path = save_dir / "conversation_history.json"
    assert conversation_path.exists()

    with conversation_path.open(encoding="utf-8") as fh:
        persisted_history = json.load(fh)

    scrubbed_history = _scrub_history_timestamps(persisted_history)
    history_golden_path = Path(__file__).parent / "goldens" / "orchestrator_multi_tool_flow_conversation_history.json"
    with history_golden_path.open(encoding="utf-8") as fh:
        golden_history = json.load(fh)

    assert scrubbed_history == golden_history
