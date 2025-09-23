"""Unit tests for CombatService."""

from unittest.mock import create_autospec, patch

from app.interfaces.services.data import IRepository, IRepositoryProvider
from app.interfaces.services.game import IMonsterManagerService
from app.interfaces.services.scenario import IScenarioService
from app.models.attributes import EntityType
from app.models.combat import CombatParticipant
from app.models.entity import IEntity
from app.models.instances.entity_state import EntityState
from app.models.location import EncounterParticipantSpawn, SpawnType
from app.services.game.combat_service import CombatService
from tests.factories import make_game_state, make_monster_instance, make_monster_sheet


class TestCombatService:
    """Test CombatService functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.scenario_service = create_autospec(IScenarioService, instance=True)
        self.monster_manager_service = create_autospec(IMonsterManagerService, instance=True)
        self.repository_provider = create_autospec(IRepositoryProvider, instance=True)
        self.service = CombatService(
            self.scenario_service,
            self.monster_manager_service,
            self.repository_provider,
        )
        self.game_state = make_game_state()

    def test_roll_initiative(self) -> None:
        """Test initiative rolling."""
        entity = create_autospec(IEntity, instance=True)
        # Attach a typed state with initiative_bonus
        entity.state = create_autospec(EntityState, instance=True)
        entity.state.initiative_bonus = 3

        with patch("random.randint", return_value=15):
            result = self.service.roll_initiative(entity)

        assert result == 18  # 15 + 3

    def test_add_participant(self) -> None:
        """Test adding participant."""
        combat = self.game_state.combat
        character = self.game_state.character

        with patch.object(self.service, "roll_initiative", return_value=16):
            participant = self.service.add_participant(combat, character)

        assert participant.name == character.display_name
        assert participant.initiative == 16
        assert participant.is_player
        assert participant.entity_id == character.instance_id
        assert len(combat.participants) == 1

    def test_realize_spawns_with_probability(self) -> None:
        """Test spawning with probability."""
        spawns = [
            EncounterParticipantSpawn(
                entity_id="goblin",
                entity_type=EntityType.MONSTER,
                spawn_type=SpawnType.REPOSITORY,
                quantity_min=2,
                quantity_max=2,
                probability=1.0,
            ),
            EncounterParticipantSpawn(
                entity_id="wolf",
                entity_type=EntityType.MONSTER,
                spawn_type=SpawnType.REPOSITORY,
                quantity_min=1,
                quantity_max=1,
                probability=0.0,
            ),
        ]

        monster_repo = create_autospec(IRepository, instance=True)
        goblin_sheet = make_monster_sheet(index="goblin", name="Goblin")
        monster_repo.get.return_value = goblin_sheet
        self.repository_provider.get_monster_repository_for.return_value = monster_repo

        goblin_instance = make_monster_instance(
            sheet=goblin_sheet, current_location_id=self.game_state.scenario_instance.current_location_id
        )
        self.monster_manager_service.create.return_value = goblin_instance

        realized = self.service.realize_spawns(self.game_state, spawns)

        assert len(realized) == 2
        assert all(e == goblin_instance for e in realized)
        assert self.monster_manager_service.create.call_count == 2

    def test_generate_combat_prompt_player_turn(self) -> None:
        """Test combat prompt for player turn."""
        self.game_state.combat.is_active = True
        round_number = 2
        self.game_state.combat.round_number = round_number
        player = CombatParticipant(
            name="Hero",
            initiative=16,
            is_player=True,
            entity_id="player-1",
            entity_type=EntityType.PLAYER,
        )
        self.game_state.combat.participants = [player]

        # Set up turn index so the player is the current turn
        self.game_state.combat.turn_index = 0
        prompt = self.service.generate_combat_prompt(self.game_state)

        assert f"Round {round_number}" in prompt
        assert player.name in prompt
        assert "Ask them what they want to do" in prompt

    def test_should_auto_end_combat(self) -> None:
        """Test combat auto-end detection."""
        self.game_state.combat.is_active = True
        self.game_state.combat.participants = [
            CombatParticipant(
                name="Hero",
                initiative=16,
                is_player=True,
                entity_id="player-1",
                entity_type=EntityType.PLAYER,
                is_active=True,
            ),
            CombatParticipant(
                name="Goblin",
                initiative=14,
                is_player=False,
                entity_id="goblin-1",
                entity_type=EntityType.MONSTER,
                is_active=False,
            ),
        ]

        assert self.service.should_auto_end_combat(self.game_state)

        # Make enemy active
        self.game_state.combat.participants[1].is_active = True
        assert not self.service.should_auto_end_combat(self.game_state)

    def test_spawn_free_monster(self) -> None:
        """Test spawning free monster."""
        monster_repo = create_autospec(IRepository, instance=True)
        monster_index = "wolf"
        monster_sheet = make_monster_sheet(index=monster_index, name="Wolf")
        monster_repo.get.return_value = monster_sheet
        self.repository_provider.get_monster_repository_for.return_value = monster_repo

        monster_instance = make_monster_instance(
            sheet=monster_sheet, current_location_id=self.game_state.scenario_instance.current_location_id
        )
        self.monster_manager_service.create.return_value = monster_instance

        result = self.service.spawn_free_monster(self.game_state, monster_index)

        assert result == monster_instance
        monster_repo.get.assert_called_once_with(monster_index)

    def test_ensure_player_in_combat(self) -> None:
        """Test ensuring player is in combat."""
        self.game_state.combat.is_active = True

        with patch.object(self.service, "roll_initiative", return_value=16):
            participant = self.service.ensure_player_in_combat(self.game_state)

        assert participant is not None
        assert participant.is_player
        assert participant.entity_id == self.game_state.character.instance_id

        # Already in combat
        participant2 = self.service.ensure_player_in_combat(self.game_state)
        assert participant2 is None
