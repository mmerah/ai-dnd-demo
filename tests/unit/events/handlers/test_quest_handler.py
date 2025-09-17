import pytest

from app.events.commands.quest_commands import (
    CompleteObjectiveCommand,
    CompleteQuestCommand,
    ProgressActCommand,
    StartQuestCommand,
)
from app.events.handlers.quest_handler import QuestHandler
from app.models.quest import ObjectiveStatus, Quest, QuestObjective
from app.models.scenario import ScenarioAct
from app.models.tool_results import CompleteObjectiveResult, CompleteQuestResult
from tests.factories import make_game_state
from tests.factories.scenario import make_scenario


class TestQuestHandler:
    def setup_method(self) -> None:
        self.handler = QuestHandler()
        self.game_state = make_game_state()
        locations = self.game_state.scenario_instance.sheet.locations
        location_ids = [loc.id for loc in locations]

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
                    name="Act 1",
                    locations=location_ids,
                    objectives=[],
                    quests=[self.quest_intro.id],
                ),
                ScenarioAct(
                    id="act2",
                    name="Act 2",
                    locations=location_ids,
                    objectives=[],
                    quests=[self.quest_finale.id],
                ),
            ],
        )

        instance = self.game_state.scenario_instance
        instance.sheet = scenario
        instance.current_act_id = "act1"
        instance.active_quests.clear()
        instance.completed_quest_ids.clear()

    @pytest.mark.asyncio
    async def test_start_quest(self) -> None:
        gs = self.game_state

        command = StartQuestCommand(game_id=gs.game_id, quest_id=self.quest_intro.id)
        result = await self.handler.handle(command, gs)

        assert result.mutated
        quest = gs.get_active_quest(self.quest_intro.id)
        assert quest is not None
        assert quest.id == self.quest_intro.id
        assert quest.objectives[0].status == ObjectiveStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_cannot_start_quest_with_unmet_prerequisites(self) -> None:
        gs = self.game_state

        command = StartQuestCommand(game_id=gs.game_id, quest_id=self.quest_finale.id)

        with pytest.raises(ValueError, match="prerequisites"):
            await self.handler.handle(command, gs)

    @pytest.mark.asyncio
    async def test_complete_objective(self) -> None:
        gs = self.game_state
        # Start the quest first
        await self.handler.handle(StartQuestCommand(game_id=gs.game_id, quest_id=self.quest_intro.id), gs)

        command = CompleteObjectiveCommand(
            game_id=gs.game_id,
            quest_id=self.quest_intro.id,
            objective_id="track",
        )
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, CompleteObjectiveResult)
        assert not result.data.quest_complete
        quest = gs.get_active_quest(self.quest_intro.id)
        assert quest is not None
        objective = next(o for o in quest.objectives if o.id == "track")
        assert objective.status == ObjectiveStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_complete_all_objectives_completes_quest(self) -> None:
        gs = self.game_state
        # Start the quest
        await self.handler.handle(StartQuestCommand(game_id=gs.game_id, quest_id=self.quest_intro.id), gs)

        # Complete all objectives
        quest = gs.get_active_quest(self.quest_intro.id)
        assert quest is not None
        for objective in quest.objectives:
            result = await self.handler.handle(
                CompleteObjectiveCommand(
                    game_id=gs.game_id,
                    quest_id=self.quest_intro.id,
                    objective_id=objective.id,
                ),
                gs,
            )

        assert isinstance(result.data, CompleteObjectiveResult)
        assert result.data.quest_complete
        assert self.quest_intro.id in gs.scenario_instance.completed_quest_ids

    @pytest.mark.asyncio
    async def test_complete_quest_directly(self) -> None:
        gs = self.game_state
        # Start and complete intro quest first
        await self.handler.handle(StartQuestCommand(game_id=gs.game_id, quest_id=self.quest_intro.id), gs)
        await self.handler.handle(CompleteQuestCommand(game_id=gs.game_id, quest_id=self.quest_intro.id), gs)

        # Progress to act 2
        await self.handler.handle(ProgressActCommand(game_id=gs.game_id), gs)

        # Start finale quest
        await self.handler.handle(StartQuestCommand(game_id=gs.game_id, quest_id=self.quest_finale.id), gs)

        command = CompleteQuestCommand(game_id=gs.game_id, quest_id=self.quest_finale.id)
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, CompleteQuestResult)
        assert result.data.quest_name == self.quest_finale.name
        assert self.quest_finale.id in gs.scenario_instance.completed_quest_ids

    @pytest.mark.asyncio
    async def test_progress_act(self) -> None:
        gs = self.game_state
        assert gs.scenario_instance.current_act_id == "act1"

        # Complete intro quest to unlock act progression
        await self.handler.handle(StartQuestCommand(game_id=gs.game_id, quest_id=self.quest_intro.id), gs)
        await self.handler.handle(CompleteQuestCommand(game_id=gs.game_id, quest_id=self.quest_intro.id), gs)

        command = ProgressActCommand(game_id=gs.game_id)
        result = await self.handler.handle(command, gs)

        assert result.mutated
        assert gs.scenario_instance.current_act_id == "act2"

    @pytest.mark.asyncio
    async def test_cannot_complete_nonexistent_quest(self) -> None:
        gs = self.game_state

        command = CompleteQuestCommand(game_id=gs.game_id, quest_id="nonexistent")

        with pytest.raises(ValueError, match="Quest .* not found in active"):
            await self.handler.handle(command, gs)
