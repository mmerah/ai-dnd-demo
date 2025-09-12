"""Factory service for creating new game instances."""

from datetime import datetime

from app.agents.core.types import AgentType
from app.interfaces.services.character import ICharacterComputeService
from app.interfaces.services.game import IGameFactory, ILocationService
from app.interfaces.services.scenario import IScenarioService
from app.models.character import CharacterSheet
from app.models.game_state import GameState, GameTime, Message, MessageRole
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.npc_instance import NPCInstance
from app.models.instances.scenario_instance import ScenarioInstance
from app.models.quest import QuestStatus
from app.utils.id_generator import generate_instance_id


class GameFactory(IGameFactory):
    """Factory for creating new game instances.

    Implements IGameFactory following Dependency Inversion Principle.
    """

    def __init__(
        self,
        scenario_service: IScenarioService,
        compute_service: ICharacterComputeService,
        location_service: ILocationService,
    ) -> None:
        """
        Initialize the game factory.

        Args:
            scenario_service: Service for managing scenarios
            compute_service: Service for computing derived character values
            location_service: Service for managing location state
        """
        self.scenario_service = scenario_service
        self.compute_service = compute_service
        self.location_service = location_service

    def generate_game_id(self, character_name: str) -> str:
        """
        Generate a human-readable game ID.

        Args:
            character_name: Name of the player character

        Returns:
            Human-readable game ID
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        clean_name = character_name.lower().replace(" ", "-")
        suffix = datetime.now().microsecond % 10000
        return f"{clean_name}-{timestamp}-{suffix:04d}"

    def initialize_game(
        self,
        character: CharacterSheet,
        scenario_id: str,
    ) -> GameState:
        game_id = self.generate_game_id(character.name)

        initial_time = GameTime(
            day=1,
            hour=9,
            minute=0,
        )

        # Load scenario
        scenario = self.scenario_service.get_scenario(scenario_id)
        if not scenario:
            raise RuntimeError(
                "No scenario available for game initialization. At least one scenario must be available."
            )

        # Set initial location and message based on scenario
        starting_loc = scenario.get_starting_location()
        initial_location = starting_loc.name
        initial_location_id = scenario.starting_location_id
        initial_narrative = scenario.get_initial_narrative()
        scenario_title = scenario.title
        scenario_id = scenario.id

        initial_message = Message(
            role=MessageRole.DM,
            content=initial_narrative,
            timestamp=datetime.now(),
            agent_type=AgentType.NARRATIVE,
            location=initial_location,
            npcs_mentioned=[],
            combat_round=None,
        )

        # Create instances
        char_inst = CharacterInstance(
            instance_id=generate_instance_id(character.name),
            template_id=character.id,
            sheet=character,
            state=self.compute_service.initialize_entity_state(character),
        )

        scen_inst = ScenarioInstance(
            instance_id=generate_instance_id(scenario.title),
            template_id=scenario_id,
            sheet=scenario,
            current_location_id=initial_location_id,
            current_act_id=scenario.progression.acts[0].id,
        )

        game_state = GameState(
            game_id=game_id,
            character=char_inst,
            npcs=[],
            location=initial_location,
            scenario_id=scenario_id,
            scenario_title=scenario_title,
            scenario_instance=scen_inst,
            game_time=initial_time,
            conversation_history=[initial_message],
        )

        # Initialize quests from scenario
        if scenario.quests:
            # Add the first act's quests as active
            first_act = scenario.progression.get_current_act()
            if first_act:
                for quest_id in first_act.quests:
                    quest = scenario.get_quest(quest_id)
                    if quest and quest.is_available([]):
                        quest.status = QuestStatus.ACTIVE
                        game_state.add_quest(quest)

        # Initialize all NPCs from the scenario
        self._initialize_all_npcs(game_state)

        # Initialize starting location
        if initial_location_id:
            location = scenario.get_location(initial_location_id)
            if location:
                # Player starts here, so initialize and mark as visited
                self.location_service.initialize_location_from_scenario(game_state, location)
                game_state.get_location_state(initial_location_id).mark_visited()

        return game_state

    def _initialize_all_npcs(self, game_state: GameState) -> None:
        """
        Initialize all NPCInstances from the scenario at game start.

        Creates NPCInstance objects for all NPCs defined in the scenario,
        setting their initial locations.

        Args:
            game_state: The game state to update
        """
        if not game_state.scenario_id:
            return

        # Load all NPCs from the scenario directory
        npc_sheets = self.scenario_service.list_scenario_npcs(game_state.scenario_id)

        # Create an instance for each NPC in the scenario
        # NOTE: For MVP1, all NPCs are loaded at game start regardless of location.
        # TODO(MVP2): Future enhancement could implement lazy loading based on location proximity.
        for npc_sheet in npc_sheets:
            # Create NPCInstance with initial location
            npc_instance = NPCInstance(
                instance_id=generate_instance_id(npc_sheet.display_name),
                scenario_npc_id=npc_sheet.id,
                sheet=npc_sheet,
                state=self.compute_service.initialize_entity_state(npc_sheet.character),
                current_location_id=npc_sheet.initial_location_id,
                attitude=npc_sheet.initial_attitude,
                notes=list(npc_sheet.initial_notes) if npc_sheet.initial_notes else [],
            )

            game_state.npcs.append(npc_instance)
