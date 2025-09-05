"""Game state management service for D&D 5e game sessions."""

import uuid
from datetime import datetime

from app.common.types import JSONSerializable
from app.interfaces.services import (
    ICharacterComputeService,
    IEventManager,
    IGameService,
    IGameStateManager,
    IItemRepository,
    IMessageManager,
    IMetadataService,
    ISaveManager,
    IScenarioService,
)
from app.models.character import CharacterSheet
from app.models.game_state import (
    GameEventType,
    GameState,
    GameTime,
    Message,
    MessageRole,
)
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.entity_state import EntityState, HitDice, HitPoints
from app.models.instances.npc_instance import NPCInstance
from app.models.instances.scenario_instance import ScenarioInstance
from app.models.item import InventoryItem, ItemDefinition, ItemSubtype, ItemType
from app.models.quest import QuestStatus
from app.models.scenario import ScenarioLocation, ScenarioMonster


class GameService(IGameService):
    """Service for managing game state, saves, and updates.

    Refactored to follow SOLID principles by delegating responsibilities
    to specialized managers.
    """

    def __init__(
        self,
        scenario_service: IScenarioService,
        save_manager: ISaveManager,
        game_state_manager: IGameStateManager,
        message_manager: IMessageManager,
        event_manager: IEventManager,
        metadata_service: IMetadataService,
        compute_service: ICharacterComputeService,
        item_repository: IItemRepository,
    ) -> None:
        """
        Initialize the game service.

        Args:
            scenario_service: Service for managing scenarios
            save_manager: Service for managing saves
            game_state_manager: Manager for active game states
            message_manager: Manager for conversation history
            event_manager: Manager for game events
            metadata_service: Service for extracting metadata
            compute_service: Service for computing derived character values
            item_repository: Repository for all items of the game
        """
        self.scenario_service = scenario_service
        self.save_manager = save_manager
        self.game_state_manager = game_state_manager
        self.message_manager = message_manager
        self.event_manager = event_manager
        self.metadata_service = metadata_service
        self.compute_service = compute_service
        self.item_repository = item_repository

    def _build_entity_state_from_sheet(self, character: CharacterSheet) -> EntityState:
        """Create an EntityState from a CharacterSheet's starting_* fields using compute layer."""
        # Base inputs
        abilities = character.starting_abilities
        level = character.starting_level

        # Derived basics
        modifiers = self.compute_service.compute_ability_modifiers(abilities)
        proficiency = self.compute_service.compute_proficiency_bonus(level)
        saving_throws = self.compute_service.compute_saving_throws(character.class_index, modifiers, proficiency)
        skills = self.compute_service.compute_skills(
            character.class_index,
            selected_skills=character.starting_skill_indexes,
            modifiers=modifiers,
            proficiency_bonus=proficiency,
        )
        armor_class = self.compute_service.compute_armor_class(modifiers, character.starting_inventory)
        initiative = self.compute_service.compute_initiative(modifiers)

        # HP / Hit Dice
        max_hp, hit_dice_total, hit_die_type = self.compute_service.compute_hit_points_and_dice(
            character.class_index, level, modifiers.CON
        )

        # Spellcasting copy with computed numbers
        spellcasting = None
        if character.starting_spellcasting is not None:
            sc = character.starting_spellcasting.model_copy(deep=True)
            dc, atk = self.compute_service.compute_spell_numbers(character.class_index, modifiers, proficiency)
            sc.spell_save_dc = dc
            sc.spell_attack_bonus = atk
            spellcasting = sc

        # Speed from race (minimal rule)
        speed = self.compute_service.compute_speed(character.race, character.starting_inventory)

        attacks = self.compute_service.compute_attacks(
            character.class_index,
            character.race,
            character.starting_inventory,
            modifiers,
            proficiency,
        )

        return EntityState(
            abilities=abilities,
            level=level,
            experience_points=character.starting_experience_points,
            hit_points=HitPoints(current=max_hp, maximum=max_hp, temporary=0),
            hit_dice=HitDice(total=hit_dice_total, current=hit_dice_total, type=hit_die_type),
            armor_class=armor_class,
            initiative=initiative,
            speed=speed,
            saving_throws=saving_throws,
            skills=skills,
            attacks=attacks,
            conditions=[],
            exhaustion_level=0,
            inspiration=False,
            inventory=character.starting_inventory,
            currency=character.starting_currency,
            spellcasting=spellcasting,
        )

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
        short_uuid = str(uuid.uuid4())[:8]
        return f"{clean_name}-{timestamp}-{short_uuid}"

    def initialize_game(
        self,
        character: CharacterSheet,
        premise: str | None = None,
        scenario_id: str | None = None,
    ) -> GameState:
        """
        Initialize a new game state.

        Args:
            character: The player's character sheet
            premise: Optional game premise or scenario
            scenario_id: Optional specific scenario to load

        Returns:
            Initialized GameState object
        """
        game_id = self.generate_game_id(character.name)

        initial_time = GameTime(
            day=1,
            hour=9,  # Start at 9 AM
            minute=0,
        )

        # Load scenario if available
        scenario = None
        if scenario_id:
            scenario = self.scenario_service.get_scenario(scenario_id)
        if not scenario:
            scenario = self.scenario_service.get_default_scenario()

        # Set initial location and message based on scenario
        if not scenario:
            raise RuntimeError(
                "No scenario available for game initialization. At least one scenario must be available."
            )

        starting_loc = scenario.get_starting_location()
        initial_location = starting_loc.name
        initial_location_id = scenario.starting_location
        initial_narrative = scenario.get_initial_narrative()
        scenario_title = scenario.title
        scenario_id = scenario.id

        initial_message = Message(
            role=MessageRole.DM,
            content=initial_narrative,
            timestamp=datetime.now(),
            agent_type="narrative",
            location=initial_location,
            npcs_mentioned=[],
            combat_round=None,
        )

        # Create instances
        # Materialize character instance from template starting_* fields
        char_inst = CharacterInstance(
            instance_id=str(uuid.uuid4()),
            template_id=character.id,
            sheet=character,
            state=self._build_entity_state_from_sheet(character),
        )

        scen_inst = ScenarioInstance(
            instance_id=str(uuid.uuid4()),
            template_id=scenario_id,
            sheet=scenario,
            current_location_id=initial_location_id,
            current_act_id=scenario.progression.acts[0].id if scenario and scenario.progression.acts else None,
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
            combat=None,
            conversation_history=[initial_message],
        )

        # Initialize quests from scenario
        if scenario and scenario.quests:
            # Add the first act's quests as active
            first_act = scenario.progression.get_current_act()
            if first_act:
                for quest_id in first_act.quests:
                    quest = scenario.get_quest(quest_id)
                    if quest and quest.is_available([]):
                        quest.status = QuestStatus.ACTIVE
                        game_state.add_quest(quest)

        # Initialize all NPCs from the scenario
        self.initialize_all_npcs(game_state)

        # Initialize starting location
        if scenario and initial_location_id:
            location = scenario.get_location(initial_location_id)
            if location:
                # Player starts here, so initialize and mark as visited
                self.initialize_location_from_scenario(game_state, location)
                game_state.get_location_state(initial_location_id).mark_visited()

        # Store in memory and save to disk
        self.game_state_manager.store_game(game_state)
        self.save_game(game_state)

        return game_state

    def save_game(self, game_state: GameState) -> str:
        """
        Save game state using modular save system.

        Args:
            game_state: Current game state to save

        Returns:
            Path to saved directory

        Raises:
            IOError: If save fails
        """
        try:
            save_dir = self.save_manager.save_game(game_state)
            return str(save_dir)
        except Exception as e:
            raise OSError(f"Failed to save game {game_state.game_id}: {e}") from e

    def load_game(self, game_id: str) -> GameState:
        """
        Load game state from modular save structure.

        Args:
            game_id: ID of the game to load

        Returns:
            Loaded GameState object

        Raises:
            FileNotFoundError: If save file doesn't exist
            ValueError: If save file is corrupted
        """
        # First, try to find the game by searching through saved games
        saved_games = self.save_manager.list_saved_games()

        scenario_id = None
        for saved_scenario_id, saved_game_id, _ in saved_games:
            if saved_game_id == game_id:
                scenario_id = saved_scenario_id
                break

        if scenario_id is None:
            raise FileNotFoundError(f"No save file found for game {game_id}")

        try:
            game_state = self.save_manager.load_game(scenario_id, game_id)
            # Store in memory after loading
            self.game_state_manager.store_game(game_state)
            return game_state
        except Exception as e:
            raise ValueError(f"Failed to load game {game_id}: {e}") from e

    def get_game(self, game_id: str) -> GameState | None:
        """
        Get active game state from memory or load from disk.

        Args:
            game_id: ID of the game

        Returns:
            GameState or None if not found
        """
        # Check in-memory storage first
        game_state = self.game_state_manager.get_game(game_id)
        if game_state:
            return game_state

        # Try loading from disk
        try:
            return self.load_game(game_id)
        except (FileNotFoundError, ValueError):
            return None

    def list_saved_games(self) -> list[GameState]:
        """
        List all saved games.

        Returns:
            List of GameState objects for all saved games
        """
        games = []
        saved_games = self.save_manager.list_saved_games()

        for scenario_id, game_id, _ in saved_games:
            try:
                game_state = self.save_manager.load_game(scenario_id, game_id)
                games.append(game_state)
            except Exception:
                # Skip corrupted save files
                continue

        # Already sorted by last_saved from save_manager
        return games

    def initialize_location_from_scenario(self, game_state: GameState, scenario_location: ScenarioLocation) -> None:
        """
        Initialize a location's state from scenario data on first visit.

        This method copies static scenario data to the dynamic LocationState.
        Should only be called when a location is first encountered.

        Args:
            game_state: The game state containing location states
            scenario_location: The scenario location definition to copy from
        """
        location_state = game_state.get_location_state(scenario_location.id)
        if not location_state.visited:
            location_state.danger_level = scenario_location.danger_level

            # Materialize notable monsters present at this location
            if scenario_location.notable_monsters:
                for sm in scenario_location.notable_monsters:
                    if isinstance(sm, ScenarioMonster):
                        # Add a deep copy so multiple visits don't share state
                        game_state.add_monster(sm.monster.model_copy(deep=True))

    def recompute_character_state(self, game_state: GameState) -> None:
        """Recompute derived values for the player character using the compute service."""
        char = game_state.character
        new_state = self.compute_service.recompute_entity_state(char.sheet, char.state)
        char.state = new_state
        char.touch()

    def set_item_equipped(self, game_id: str, item_name: str, equipped: bool) -> GameState:
        """Equip/unequip a single unit of the named item and persist changes.

        Splits/merges stacks for equippable items and recomputes derived stats.
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        inventory = game_state.character.state.inventory
        # Locate item by name (case-insensitive fallback)
        item = next((it for it in inventory if it.name == item_name), None)
        if not item:
            item = next((it for it in inventory if it.name.lower() == item_name.lower()), None)
        if not item:
            raise ValueError(f"Item '{item_name}' not found in inventory")

        # Validate using item repository
        item_def = self.item_repository.get(item.name)
        if not item_def:
            raise ValueError(f"Unknown item definition for '{item.name}'")
        if item_def.type not in (ItemType.WEAPON, ItemType.ARMOR):
            raise ValueError(f"Item '{item.name}' is not equippable")

        # Single-entry model: adjust equipped_quantity by one
        if equipped:
            # TODO: Future: move to a slot-based equipment system (typed slots, constraints)
            self._enforce_equip_constraints(inventory, item_def)
            if item.equipped_quantity < item.quantity:
                item.equipped_quantity += 1
        else:
            if item.equipped_quantity > 0:
                item.equipped_quantity -= 1

        # Recompute and save
        self.recompute_character_state(game_state)
        self.save_game(game_state)
        return game_state

    def _is_shield(self, idef: ItemDefinition) -> bool:
        return idef.type == ItemType.ARMOR and idef.subtype == ItemSubtype.SHIELD

    def _is_body_armor(self, idef: ItemDefinition) -> bool:
        return idef.type == ItemType.ARMOR and idef.subtype in (
            ItemSubtype.LIGHT,
            ItemSubtype.MEDIUM,
            ItemSubtype.HEAVY,
        )

    def _enforce_equip_constraints(self, inventory: list[InventoryItem], equipping_def: ItemDefinition) -> None:
        """
        Enforce simple equipment constraints.

        - Only one shield may be equipped
        - Only one body armor (light/medium/heavy) may be equipped
        """
        if self._is_shield(equipping_def):
            for it in inventory:
                if (it.equipped_quantity or 0) <= 0:
                    continue
                current_def = self.item_repository.get(it.name)
                if current_def and self._is_shield(current_def):
                    raise ValueError("Cannot equip more than one shield at a time")
        elif self._is_body_armor(equipping_def):
            for it in inventory:
                if (it.equipped_quantity or 0) <= 0:
                    continue
                current_def = self.item_repository.get(it.name)
                if current_def and self._is_body_armor(current_def):
                    raise ValueError("Already wearing body armor; unequip it first")

    def add_game_event(
        self,
        game_id: str,
        event_type: GameEventType,
        tool_name: str | None = None,
        parameters: dict[str, JSONSerializable] | None = None,
        result: dict[str, JSONSerializable] | None = None,
        metadata: dict[str, JSONSerializable] | None = None,
    ) -> GameState:
        """
        Add a game event to the history.

        Args:
            game_id: Game ID
            event_type: Type of event (GameEventType enum)
            tool_name: Name of the tool
            parameters: Tool parameters
            result: Tool result
            metadata: Additional metadata

        Returns:
            Updated GameState
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        # Delegate to event manager
        self.event_manager.add_event(
            game_state=game_state,
            event_type=event_type,
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            metadata=metadata,
        )
        self.save_game(game_state)
        return game_state

    def add_message(
        self,
        game_id: str,
        role: MessageRole,
        content: str,
        agent_type: str = "narrative",
        location: str | None = None,
        npcs_mentioned: list[str] | None = None,
        combat_round: int | None = None,
    ) -> GameState:
        """
        Add a message to conversation history with metadata.

        Args:
            game_id: Game ID
            role: Message role (player/dm)
            content: Message content
            agent_type: Which agent generated this message
            location: Where this message occurred
            npcs_mentioned: NPCs referenced in the message
            combat_round: Combat round if in combat

        Returns:
            Updated GameState

        Raises:
            ValueError: If game not found
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        # Extract metadata if not provided
        if npcs_mentioned is None:
            # Get all NPC names from the game state (both sheet name and display name)
            known_npcs = []
            for npc in game_state.npcs:
                known_npcs.append(npc.sheet.character.name)

            npcs_mentioned = self.metadata_service.extract_npcs_mentioned(content, known_npcs)

        if location is None:
            location = self.metadata_service.extract_location(content, game_state.location)

        if combat_round is None and game_state.combat:
            combat_round = self.metadata_service.extract_combat_round(content, True)

        # Delegate to message manager
        self.message_manager.add_message(
            game_state=game_state,
            role=role,
            content=content,
            agent_type=agent_type,
            location=location,
            npcs_mentioned=npcs_mentioned,
            combat_round=combat_round,
        )
        self.save_game(game_state)
        return game_state

    # TODO: Look unused. GameState has a method with exact same name
    def set_quest_flag(self, game_id: str, flag_name: str, value: JSONSerializable) -> GameState:
        """
        Set a quest flag value.

        Args:
            game_id: Game ID
            flag_name: Name of the quest flag
            value: Value to set

        Returns:
            Updated GameState

        Raises:
            ValueError: If game not found
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        game_state.set_quest_flag(flag_name, value)
        self.save_game(game_state)
        return game_state

    def initialize_all_npcs(self, game_state: GameState) -> None:
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
        # Future enhancement could implement lazy loading based on location proximity.
        for npc_sheet in npc_sheets:
            # Create NPCInstance with initial location
            npc_instance = NPCInstance(
                instance_id=str(uuid.uuid4()),
                scenario_npc_id=npc_sheet.id,
                sheet=npc_sheet,
                state=self._build_entity_state_from_sheet(npc_sheet.character),
                current_location_id=npc_sheet.initial_location_id,
                attitude=npc_sheet.initial_attitude,
                notes=list(npc_sheet.initial_notes) if npc_sheet.initial_notes else [],
            )

            game_state.npcs.append(npc_instance)
