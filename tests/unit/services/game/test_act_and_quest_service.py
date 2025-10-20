"""Unit tests for ActAndQuestService."""

from app.models.quest import Quest, QuestObjective, QuestStatus
from app.models.scenario import ScenarioAct
from app.services.game.act_and_quest_service import ActAndQuestService
from tests.factories import make_game_state
from tests.factories.scenario import make_scenario


class TestActAndQuestService:
    def setup_method(self) -> None:
        self.service = ActAndQuestService()
        self.game_state = make_game_state()
        locations = self.game_state.scenario_instance.sheet.locations
        location_ids = [loc.id for loc in locations]

        # Create test quests
        self.quest_intro = Quest(
            id="rescue",
            name="Rescue the Scout",
            description="Find and rescue the missing scout",
            objectives=[
                QuestObjective(id="track", description="Find trail"),
                QuestObjective(id="rescue", description="Rescue scout"),
            ],
            rewards_description="Gratitude",
        )

        self.quest_finale = Quest(
            id="ambush",
            name="Stop the Ambush",
            description="Prevent the goblin ambush",
            objectives=[QuestObjective(id="foil", description="Foil ambush")],
            rewards_description="Safety",
            prerequisites=[self.quest_intro.id],
        )

        # Create scenario with two acts
        scenario = make_scenario(
            scenario_id="rescue-run",
            title="Rescue Run",
            description="A rescue mission",
            starting_location_id=self.game_state.scenario_instance.sheet.starting_location_id,
            locations=locations,
            quests=[self.quest_intro, self.quest_finale],
            acts=[
                ScenarioAct(
                    id="act1",
                    name="Act 1: The Beginning",
                    locations=location_ids,
                    objectives=[],
                    quests=[self.quest_intro.id],
                ),
                ScenarioAct(
                    id="act2",
                    name="Act 2: The Finale",
                    locations=location_ids,
                    objectives=[],
                    quests=[self.quest_finale.id],
                ),
            ],
        )

        # Set up game state with scenario
        instance = self.game_state.scenario_instance
        instance.sheet = scenario
        instance.current_act_id = "act1"
        instance.active_quests.clear()
        instance.completed_quest_ids.clear()
        self.game_state.story_notes.clear()

    def test_complete_quest_success(self) -> None:
        """Test that completing a quest works correctly."""
        gs = self.game_state

        self.service.add_quest(gs, self.quest_intro)

        result = self.service.complete_quest(gs, self.quest_intro.id)

        assert result is True
        assert self.quest_intro.status == QuestStatus.COMPLETED
        assert self.quest_intro.id in gs.scenario_instance.completed_quest_ids
        assert self.service.get_active_quest(gs, self.quest_intro.id) is None

    def test_complete_quest_not_found(self) -> None:
        """Test that completing a non-existent quest returns False."""
        gs = self.game_state

        result = self.service.complete_quest(gs, "nonexistent-quest")

        assert result is False

    def test_can_progress_act_when_ready(self) -> None:
        """Test that can_progress_act returns True when all quests are completed."""
        gs = self.game_state
        gs.scenario_instance.completed_quest_ids.append(self.quest_intro.id)

        can_progress = self.service.can_progress_act(gs)

        assert can_progress is True

    def test_cannot_progress_act_when_not_ready(self) -> None:
        """Test that can_progress_act returns False when quests are incomplete."""
        gs = self.game_state

        can_progress = self.service.can_progress_act(gs)

        assert can_progress is False

    def test_auto_progress_act_when_ready(self) -> None:
        """Test that act auto-progresses when all quests are completed."""
        gs = self.game_state
        gs.scenario_instance.completed_quest_ids.append(self.quest_intro.id)

        progressed, new_act_id = self.service.auto_progress_act_if_ready(gs)

        assert progressed is True
        assert new_act_id == "act2"
        assert gs.scenario_instance.current_act_id == "act2"
        assert any("Act 2: The Finale" in note for note in gs.story_notes)

    def test_no_auto_progress_when_not_ready(self) -> None:
        """Test that act does not progress when quests are incomplete."""
        gs = self.game_state

        progressed, new_act_id = self.service.auto_progress_act_if_ready(gs)

        assert progressed is False
        assert new_act_id is None
        assert gs.scenario_instance.current_act_id == "act1"

    def test_complete_quest_auto_progresses_act(self) -> None:
        """Test that completing a quest automatically progresses act if ready."""
        gs = self.game_state

        self.service.add_quest(gs, self.quest_intro)

        result = self.service.complete_quest(gs, self.quest_intro.id)

        assert result is True
        assert gs.scenario_instance.current_act_id == "act2"
        assert any("Act 2: The Finale" in note for note in gs.story_notes)

    def test_get_available_quests_for_current_act(self) -> None:
        """Test that get_available_quests returns quests for the current act."""
        gs = self.game_state

        available = self.service.get_available_quests(gs)

        assert len(available) == 1
        assert available[0].id == self.quest_intro.id

    def test_get_available_quests_excludes_active(self) -> None:
        """Test that active quests are not returned as available."""
        gs = self.game_state

        self.service.add_quest(gs, self.quest_intro)

        available = self.service.get_available_quests(gs)

        assert available == []

    def test_get_available_quests_excludes_completed(self) -> None:
        """Test that completed quests are not returned as available."""
        gs = self.game_state
        gs.scenario_instance.completed_quest_ids.append(self.quest_intro.id)

        available = self.service.get_available_quests(gs)

        assert available == []

    def test_get_available_quests_respects_prerequisites(self) -> None:
        """Test that quests with unmet prerequisites are not available."""
        gs = self.game_state

        gs.scenario_instance.current_act_id = "act2"
        gs.scenario_instance.sheet.progression.current_act_index = 1

        available = self.service.get_available_quests(gs)
        assert available == []

        gs.scenario_instance.completed_quest_ids.append(self.quest_intro.id)

        available = self.service.get_available_quests(gs)

        assert len(available) == 1
        assert available[0].id == self.quest_finale.id

    def test_add_quest(self) -> None:
        """Test that add_quest tracks quest activation."""
        gs = self.game_state

        self.service.add_quest(gs, self.quest_intro)

        assert self.quest_intro.status == QuestStatus.ACTIVE
        assert self.service.get_active_quest(gs, self.quest_intro.id) is not None

    def test_no_progression_when_no_more_acts(self) -> None:
        """Test that progression stops when there are no more acts."""
        gs = self.game_state

        gs.scenario_instance.current_act_id = "act2"
        gs.scenario_instance.sheet.progression.current_act_index = 1
        gs.scenario_instance.completed_quest_ids.append(self.quest_intro.id)

        self.service.add_quest(gs, self.quest_finale)
        self.service.complete_quest(gs, self.quest_finale.id)

        progressed, new_act_id = self.service.auto_progress_act_if_ready(gs)

        assert progressed is False
        assert new_act_id is None
        assert gs.scenario_instance.current_act_id == "act2"
