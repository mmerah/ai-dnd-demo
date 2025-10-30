"""Unit tests for combat_loop ally suggestion generation."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.agents.core.base import BaseAgent, ToolFunction
from app.events.commands.broadcast_commands import BroadcastCombatSuggestionCommand
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IAgentLifecycleService
from app.models.ai_response import NarrativeResponse, StreamEvent, StreamEventType
from app.models.attributes import EntityType
from app.models.combat import CombatFaction, CombatParticipant, CombatState
from app.models.instances.npc_instance import NPCInstance
from app.services.ai.orchestrator import combat_loop
from tests.factories import make_game_state, make_npc_instance, make_npc_sheet


class TestCombatParticipantFactions:
    """Test that combat participants can be properly categorized by faction."""

    def test_ally_faction_detection(self) -> None:
        """Test that ALLY faction is properly set and detected."""
        ally = CombatParticipant(
            entity_id="npc-ally-1",
            entity_type=EntityType.NPC,
            faction=CombatFaction.ALLY,
            name="Eldrin the Wise",
            initiative=14,
            is_player=False,
            is_active=True,
        )

        assert ally.faction == CombatFaction.ALLY
        assert not ally.is_player
        assert ally.entity_type == EntityType.NPC

    def test_enemy_faction_detection(self) -> None:
        """Test that ENEMY faction is properly set and detected."""
        enemy = CombatParticipant(
            entity_id="monster-1",
            entity_type=EntityType.MONSTER,
            faction=CombatFaction.ENEMY,
            name="Goblin",
            initiative=12,
            is_player=False,
            is_active=True,
        )

        assert enemy.faction == CombatFaction.ENEMY
        assert enemy.entity_type == EntityType.MONSTER

    def test_player_faction_detection(self) -> None:
        """Test that PLAYER faction is properly set and detected."""
        player = CombatParticipant(
            entity_id="player",
            entity_type=EntityType.PLAYER,
            faction=CombatFaction.PLAYER,
            name="Aldric",
            initiative=15,
            is_player=True,
            is_active=True,
        )

        assert player.faction == CombatFaction.PLAYER
        assert player.is_player
        assert player.entity_type == EntityType.PLAYER


class TestCombatStateCurrentTurn:
    """Test combat state's current turn detection."""

    def test_get_current_turn_with_ally(self) -> None:
        """Test getting current turn when it's an ally's turn."""
        combat = CombatState(
            is_active=True,
            round_number=1,
            turn_index=1,  # Second participant (ally)
            participants=[
                CombatParticipant(
                    entity_id="player",
                    entity_type=EntityType.PLAYER,
                    faction=CombatFaction.PLAYER,
                    name="Aldric",
                    initiative=15,
                    is_player=True,
                ),
                CombatParticipant(
                    entity_id="npc-ally-1",
                    entity_type=EntityType.NPC,
                    faction=CombatFaction.ALLY,
                    name="Eldrin",
                    initiative=14,
                ),
                CombatParticipant(
                    entity_id="monster-1",
                    entity_type=EntityType.MONSTER,
                    faction=CombatFaction.ENEMY,
                    name="Goblin",
                    initiative=12,
                ),
            ],
        )

        current = combat.get_current_turn()
        assert current is not None
        assert current.faction == CombatFaction.ALLY
        assert current.entity_id == "npc-ally-1"
        assert current.entity_type == EntityType.NPC

    def test_get_current_turn_with_enemy(self) -> None:
        """Test getting current turn when it's an enemy's turn."""
        combat = CombatState(
            is_active=True,
            round_number=1,
            turn_index=2,  # Third participant (enemy)
            participants=[
                CombatParticipant(
                    entity_id="player",
                    entity_type=EntityType.PLAYER,
                    faction=CombatFaction.PLAYER,
                    name="Aldric",
                    initiative=15,
                    is_player=True,
                ),
                CombatParticipant(
                    entity_id="npc-ally-1",
                    entity_type=EntityType.NPC,
                    faction=CombatFaction.ALLY,
                    name="Eldrin",
                    initiative=14,
                ),
                CombatParticipant(
                    entity_id="monster-1",
                    entity_type=EntityType.MONSTER,
                    faction=CombatFaction.ENEMY,
                    name="Goblin",
                    initiative=12,
                ),
            ],
        )

        current = combat.get_current_turn()
        assert current is not None
        assert current.faction == CombatFaction.ENEMY
        assert current.entity_id == "monster-1"

    def test_get_current_turn_skips_inactive(self) -> None:
        """Test that inactive participants are skipped."""
        combat = CombatState(
            is_active=True,
            round_number=1,
            turn_index=0,  # First active participant
            participants=[
                CombatParticipant(
                    entity_id="player",
                    entity_type=EntityType.PLAYER,
                    faction=CombatFaction.PLAYER,
                    name="Aldric",
                    initiative=15,
                    is_player=True,
                    is_active=False,  # Inactive
                ),
                CombatParticipant(
                    entity_id="npc-ally-1",
                    entity_type=EntityType.NPC,
                    faction=CombatFaction.ALLY,
                    name="Eldrin",
                    initiative=14,
                    is_active=True,  # Active
                ),
            ],
        )

        current = combat.get_current_turn()
        assert current is not None
        assert current.entity_id == "npc-ally-1"
        assert current.is_active


class TestAllySuggestionGeneration:
    """Test ally combat suggestion generation."""

    @pytest.mark.asyncio
    async def test_generate_ally_suggestion_success(self) -> None:
        """Test successful ally suggestion generation and broadcast."""
        game_state = make_game_state()
        game_state.combat.is_active = True

        # Create NPC and add to party
        npc_sheet = make_npc_sheet(npc_id="ally-1", display_name="Eldrin the Wise")
        npc = make_npc_instance(instance_id="npc-ally-1", scenario_npc_id="ally-1", npc_sheet=npc_sheet)
        game_state.npcs.append(npc)
        game_state.party.member_ids.append(npc.instance_id)

        # Create combat participant
        current_turn = CombatParticipant(
            entity_id=npc.instance_id,
            entity_type=EntityType.NPC,
            faction=CombatFaction.ALLY,
            name=npc.display_name,
            initiative=15,
            is_player=False,
            is_active=True,
        )

        # Mock NPC agent
        class _MockNPCAgent(BaseAgent):
            def __init__(self) -> None:
                self.prepared_npc: NPCInstance | None = None

            def get_required_tools(self) -> list[ToolFunction]:
                return []

            def prepare_for_npc(self, npc: NPCInstance) -> None:
                self.prepared_npc = npc

            async def process(
                self, prompt: str, game_state: object, context: str, stream: bool = True
            ) -> AsyncIterator[StreamEvent]:
                yield StreamEvent(
                    type=StreamEventType.COMPLETE,
                    content=NarrativeResponse(narrative="I'll cast Fireball at the goblin!"),
                )

        mock_npc_agent = _MockNPCAgent()
        agent_lifecycle = create_autospec(IAgentLifecycleService, instance=True)
        agent_lifecycle.get_npc_agent.return_value = mock_npc_agent

        # Mock event bus
        event_bus = create_autospec(IEventBus, instance=True)
        event_bus.submit_and_wait = AsyncMock()

        # Generate suggestion
        await combat_loop._generate_ally_suggestion(
            game_state=game_state,
            current_turn=current_turn,
            agent_lifecycle_service=agent_lifecycle,
            event_bus=event_bus,
        )

        # Verify NPC agent was prepared
        assert mock_npc_agent.prepared_npc is npc

        # Verify broadcast was called
        event_bus.submit_and_wait.assert_awaited_once()
        commands = event_bus.submit_and_wait.call_args[0][0]
        assert len(commands) == 1
        assert isinstance(commands[0], BroadcastCombatSuggestionCommand)
        assert commands[0].npc_id == npc.instance_id
        assert commands[0].npc_name == npc.display_name
        assert commands[0].action_text == "I'll cast Fireball at the goblin!"

    @pytest.mark.asyncio
    async def test_generate_ally_suggestion_raises_for_non_npc(self) -> None:
        """Test that non-NPC entities raise ValueError."""
        game_state = make_game_state()
        game_state.combat.is_active = True

        # Create combat participant that is NOT an NPC
        current_turn = CombatParticipant(
            entity_id="player",
            entity_type=EntityType.PLAYER,  # Not an NPC!
            faction=CombatFaction.ALLY,
            name="Player",
            initiative=15,
            is_player=True,
            is_active=True,
        )

        agent_lifecycle = create_autospec(IAgentLifecycleService, instance=True)
        event_bus = create_autospec(IEventBus, instance=True)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Cannot generate combat suggestion for non-NPC entity"):
            await combat_loop._generate_ally_suggestion(
                game_state=game_state,
                current_turn=current_turn,
                agent_lifecycle_service=agent_lifecycle,
                event_bus=event_bus,
            )

    @pytest.mark.asyncio
    async def test_generate_ally_suggestion_raises_for_missing_npc(self) -> None:
        """Test that missing NPC raises ValueError."""
        game_state = make_game_state()
        game_state.combat.is_active = True

        # Create combat participant for NPC that doesn't exist
        current_turn = CombatParticipant(
            entity_id="nonexistent-npc",
            entity_type=EntityType.NPC,
            faction=CombatFaction.ALLY,
            name="Ghost NPC",
            initiative=15,
            is_player=False,
            is_active=True,
        )

        agent_lifecycle = create_autospec(IAgentLifecycleService, instance=True)
        event_bus = create_autospec(IEventBus, instance=True)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Allied NPC nonexistent-npc not found"):
            await combat_loop._generate_ally_suggestion(
                game_state=game_state,
                current_turn=current_turn,
                agent_lifecycle_service=agent_lifecycle,
                event_bus=event_bus,
            )

    @pytest.mark.asyncio
    async def test_generate_ally_suggestion_raises_for_npc_not_in_party(self) -> None:
        """Test that NPC not in party raises ValueError."""
        game_state = make_game_state()
        game_state.combat.is_active = True

        # Create NPC but DON'T add to party
        npc_sheet = make_npc_sheet(npc_id="ally-1", display_name="Eldrin the Wise")
        npc = make_npc_instance(instance_id="npc-ally-1", scenario_npc_id="ally-1", npc_sheet=npc_sheet)
        game_state.npcs.append(npc)
        # Note: NOT added to party!

        current_turn = CombatParticipant(
            entity_id=npc.instance_id,
            entity_type=EntityType.NPC,
            faction=CombatFaction.ALLY,
            name=npc.display_name,
            initiative=15,
            is_player=False,
            is_active=True,
        )

        agent_lifecycle = create_autospec(IAgentLifecycleService, instance=True)
        event_bus = create_autospec(IEventBus, instance=True)

        # Should raise ValueError
        with pytest.raises(ValueError, match="has ALLY faction in combat but is not in the party"):
            await combat_loop._generate_ally_suggestion(
                game_state=game_state,
                current_turn=current_turn,
                agent_lifecycle_service=agent_lifecycle,
                event_bus=event_bus,
            )

    @pytest.mark.asyncio
    async def test_npc_agent_prepared_with_correct_npc(self) -> None:
        """Test that prepare_for_npc is called with the correct NPC instance."""
        game_state = make_game_state()
        game_state.combat.is_active = True

        # Create NPC and add to party
        npc_sheet = make_npc_sheet(npc_id="ally-1", display_name="Thrain the Bold")
        npc = make_npc_instance(instance_id="npc-ally-1", scenario_npc_id="ally-1", npc_sheet=npc_sheet)
        game_state.npcs.append(npc)
        game_state.party.member_ids.append(npc.instance_id)

        current_turn = CombatParticipant(
            entity_id=npc.instance_id,
            entity_type=EntityType.NPC,
            faction=CombatFaction.ALLY,
            name=npc.display_name,
            initiative=15,
            is_player=False,
            is_active=True,
        )

        # Track prepare_for_npc calls
        prepared_npcs: list[NPCInstance] = []

        class _TrackingNPCAgent(BaseAgent):
            def get_required_tools(self) -> list[ToolFunction]:
                return []

            def prepare_for_npc(self, npc: NPCInstance) -> None:
                prepared_npcs.append(npc)

            async def process(
                self, prompt: str, game_state: object, context: str, stream: bool = True
            ) -> AsyncIterator[StreamEvent]:
                yield StreamEvent(
                    type=StreamEventType.COMPLETE,
                    content=NarrativeResponse(narrative="I attack!"),
                )

        mock_npc_agent = _TrackingNPCAgent()
        agent_lifecycle = create_autospec(IAgentLifecycleService, instance=True)
        agent_lifecycle.get_npc_agent.return_value = mock_npc_agent

        event_bus = create_autospec(IEventBus, instance=True)
        event_bus.submit_and_wait = AsyncMock()

        await combat_loop._generate_ally_suggestion(
            game_state=game_state,
            current_turn=current_turn,
            agent_lifecycle_service=agent_lifecycle,
            event_bus=event_bus,
        )

        # Verify prepare_for_npc was called with the correct NPC
        assert len(prepared_npcs) == 1
        assert prepared_npcs[0] is npc
        assert prepared_npcs[0].instance_id == "npc-ally-1"
