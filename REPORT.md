# Refactoring and Architectural Improvement Plan

## 1. Introduction

This document outlines a strategic plan to refactor the `ai-dnd-demo` codebase. The goal is to enhance the project's long-term maintainability, robustness, and clarity by systematically addressing architectural weaknesses. The proposed changes are guided by the core principles already established in the project's `CLAUDE.md` document, specifically enforcing Fail-Fast, SOLID, and DRY principles more rigorously.

**Implementation Notes:**
- All changes are breaking changes (no backward compatibility)
- Standard exceptions will be used throughout
- Policy violations will raise exceptions
- Partial save corruption will fail entirely

## 2. Guiding Principles

The following principles will guide the refactoring effort:

*   **Fail-Fast and Strictness**: Eliminate ambiguity by removing unnecessary optional types (`| None`). If a value is required for an operation to succeed, it should be a required parameter, causing failure at the earliest possible moment rather than deep within a call stack.
*   **Single Responsibility Principle (SRP)**: Ensure every class and module has one, and only one, reason to change. Responsibilities that are currently misplaced will be moved to more appropriate components.
*   **Don't Repeat Yourself (DRY)**: Abstract and consolidate duplicated code patterns to reduce redundancy, improve consistency, and simplify maintenance.
*   **Clear Responsibility**: Refine the roles of services and components to make their purpose more explicit and their interactions more straightforward.

---

## 3. Refactoring Plan

### Part 1: Enforcing Fail-Fast Principles

This section focuses on removing optional types where they mask required dependencies or lead to complex conditional logic.

#### 1.1. Make Context Builders Stateless

*   **Context**: Several context builders in `app/services/ai/context_builders/` are initialized with optional repository dependencies (e.g., `item_repository: IRepository[ItemDefinition] | None`). These are later injected by the `ContextService` before the `build` method is called. This makes the builders stateful and their initialization incomplete.

*   **Proposed Change**:
    1.  Create a `BuildContext` dataclass to hold all builder dependencies:
        ```python
        # In app/services/ai/context_builders/base.py
        from dataclasses import dataclass
        from app.interfaces.services.data import IRepository
        from app.models.item import ItemDefinition
        from app.models.spell import SpellDefinition

        @dataclass
        class BuildContext:
            """Type-safe container for all context builder dependencies."""
            item_repository: IRepository[ItemDefinition]
            spell_repository: IRepository[SpellDefinition]
            # Add other repositories as needed

        class ContextBuilder(ABC):
            @abstractmethod
            def build(self, game_state: GameState, context: BuildContext) -> str | None:
                # ...
        ```
    2.  Update specific builders to remove repositories from `__init__` and accept `BuildContext` in `build`:
        ```python
        # In app/services/ai/context_builders/location_builder.py
        class LocationContextBuilder(ContextBuilder):
            # No __init__ needed - fully stateless

            def build(self, game_state: GameState, context: BuildContext) -> str | None:
                item_repo = context.item_repository
                # ... use item_repo ...
        ```
    3.  Update `ContextService` to create and pass `BuildContext`:
        ```python
        # In app/services/ai/context_service.py
        class ContextService(IContextService):
            def build_context(self, game_state: GameState, agent_type: AgentType) -> str:
                # ...
                build_context = BuildContext(
                    item_repository=self.repository_provider.get_item_repository_for(game_state),
                    spell_repository=self.repository_provider.get_spell_repository_for(game_state),
                )
                for builder in selected_builders:
                    part = builder.build(game_state, build_context)
                    # ...
        ```

*   **Justification**: This change makes each context builder stateless and self-contained. The `BuildContext` provides type safety and makes dependencies explicit. Breaking change: All existing builder instantiations will need updating.

#### 1.2. Make `SaveManager` Loaders Raise Exceptions Directly

*   **Context**: In `app/services/game/save_manager.py`, the `_load_scenario_instance` method returns `ScenarioInstance | None`. The calling method, `load_game`, checks for `None` and then raises a `ValueError`.

*   **Proposed Change**: Modify `_load_scenario_instance` and similar private loaders to raise exceptions directly instead of returning `None`.

    ```python
    # In app/services/game/save_manager.py
    def _load_scenario_instance(self, save_dir: Path) -> ScenarioInstance: # Return type is no longer optional
        file_path = save_dir / "instances" / "scenario.json"
        if not file_path.exists():
            # Fail fast with standard exception
            raise FileNotFoundError(f"Missing scenario.json in {save_dir}. Save is corrupted.")
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            return ScenarioInstance(**data)
        except (json.JSONDecodeError, ValueError) as e:
            # Fail entirely on partial corruption
            raise ValueError(f"Corrupted scenario.json in {save_dir}: {e}") from e

    def load_game(self, scenario_id: str, game_id: str) -> GameState:
        # ...
        try:
            scenario_instance = self._load_scenario_instance(save_dir)
            # No more None check needed
        except FileNotFoundError as e:
            # Re-raise with game context
            raise FileNotFoundError(f"Cannot load game {game_id}: {e}") from e
        # ...
    ```

*   **Justification**: This adheres to the fail-fast principle with standard exceptions. Any save corruption causes immediate failure. Breaking change: Exception handling in callers must be updated.

---

### Part 2: Strengthening SOLID and DRY Principles

This section addresses violations of the Single Responsibility Principle (SRP) and instances of duplicated code (DRY).

#### 2.1. SRP: Create a Dedicated `ItemFactory`

*   **Context**: The `CharacterSheetService` is responsible for loading and validating character sheets. However, its `create_placeholder_item` method is responsible for *creating new, dynamic item definitions at runtime*. This is a separate responsibility related to item creation, not character sheet management.

*   **Proposed Change**:
    1.  Create a new interface `IItemFactory` in `app/interfaces/services/game/item_factory.py`.
    2.  Create a concrete implementation `ItemFactory` in `app/services/game/item_factory.py` as a singleton service.
    3.  Move the `create_placeholder_item` method from `CharacterSheetService` to the new `ItemFactory`.
    4.  Register in `container.py` following the existing architecture patterns.
    5.  Update the `InventoryHandler` and any other components to depend on `IItemFactory`.

    ```python
    # In app/interfaces/services/game/item_factory.py
    class IItemFactory(ABC):
        @abstractmethod
        def create_inventory_item(
            self,
            game_state: GameState,
            item_index: str,
            quantity: int = 1
        ) -> InventoryItem:
            """Create or retrieve an inventory item, with placeholder support."""
            ...

    # In app/services/game/item_factory.py
    class ItemFactory(IItemFactory):
        def __init__(self, repository_provider: IRepositoryProvider):
            self.repository_provider = repository_provider

        def create_inventory_item(
            self,
            game_state: GameState,
            item_index: str,
            quantity: int = 1
        ) -> InventoryItem:
            item_repo = self.repository_provider.get_item_repository_for(game_state)

            # Validation stays in repository
            if item_repo.validate_reference(item_index):
                item_def = item_repo.get(item_index)
                return InventoryItem.from_definition(item_def, quantity=quantity)
            else:
                # Create placeholder for AI-invented items
                logger.warning(f"Creating placeholder for dynamic item: {item_index}")
                return self._create_placeholder(item_index, quantity)

        def _create_placeholder(self, item_index: str, quantity: int) -> InventoryItem:
            # Logic moved from CharacterSheetService
            item_name = item_index.replace("-", " ").title()
            item_def = ItemDefinition(
                index=item_index,
                name=item_name,
                type=ItemType.ADVENTURING_GEAR,
                rarity=ItemRarity.COMMON,
                description=f"A unique item: {item_name}",
                weight=0.5,
                value=1,
                content_pack="sandbox",
            )
            return InventoryItem.from_definition(item_def, quantity=quantity)
    ```

*   **Justification**: This follows SRP and matches existing factory patterns (MonsterFactory). The service is a configurable singleton registered in the container. Item validation remains in repositories. Breaking change: All references to `create_placeholder_item` must be updated.

#### 2.2. SRP: Centralize Policy Enforcement from `tool_handler`

*   **Context**: The `@tool_handler` decorator in `app/tools/decorators.py` currently contains complex logic to enforce agent policies (e.g., preventing the Narrative Agent from using combat tools during active combat). This mixes the concern of policy enforcement with the decorator's primary role of command wrapping.

*   **Proposed Change**:
    1.  Move the policy validation logic from the decorator into the `ActionService`.
    2.  The `ActionService.execute_command_as_action` method will perform validation *before* execution.
    3.  Policy violations raise exceptions (fail-fast).
    4.  The decorator becomes a thin wrapper focused only on command transformation.

    ```python
    # In app/services/common/action_service.py
    class ActionService(IActionService):
        # Define policies as class-level constants (not configurable for now)
        COMBAT_ONLY_TOOLS = frozenset([
            "roll_dice", "update_hp", "update_condition",
            "next_turn", "end_combat", "add_combatant", "remove_combatant"
        ])

        NPC_ALLOWED_TOOLS = frozenset([
            "start_quest", "complete_objective", "complete_quest",
            "modify_inventory", "update_location_state",
            "discover_secret", "move_npc_to_location"
        ])

        async def execute_command_as_action(
            self,
            tool_name: str,
            command: BaseCommand,
            game_state: GameState,
            broadcast_parameters: dict[str, JSONSerializable],
        ) -> BaseModel:
            # Validate policy FIRST (fail-fast)
            self._validate_action_policy(tool_name, game_state, command.agent_type)

            # Then proceed with normal execution
            # ... existing broadcast, persistence, execution logic ...

        def _validate_action_policy(
            self,
            tool_name: str,
            game_state: GameState,
            agent_type: AgentType
        ) -> None:
            """Enforce agent tool usage policies. Raises ValueError on violation."""

            # Policy 1: Narrative agent cannot use combat tools during combat
            if game_state.combat.is_active and agent_type == AgentType.NARRATIVE:
                if tool_name in self.COMBAT_ONLY_TOOLS:
                    raise ValueError(
                        f"Policy violation: Narrative agent cannot use '{tool_name}' "
                        f"during active combat. This tool is restricted to combat agent."
                    )

            # Policy 2: NPC agents have restricted tool access
            if agent_type == AgentType.NPC:
                if tool_name not in self.NPC_ALLOWED_TOOLS:
                    raise ValueError(
                        f"Policy violation: NPC agent cannot use '{tool_name}'. "
                        f"Allowed tools: {', '.join(sorted(self.NPC_ALLOWED_TOOLS))}"
                    )

    # In app/tools/decorators.py - simplified decorator
    def tool_handler(...):
        def decorator(...):
            @wraps(func)
            async def wrapper(ctx: RunContext[AgentDependencies], **kwargs: Any) -> BaseModel:
                # Build command (existing logic)
                # ...

                try:
                    # Delegate ALL logic to ActionService
                    result = await ctx.deps.action_service.execute_command_as_action(
                        tool_name=tool_name,
                        command=command,
                        game_state=game_state,
                        broadcast_parameters=broadcast_kwargs,
                    )
                except ValueError as e:
                    # Policy violations and other errors bubble up
                    logger.error(f"Tool {tool_name} failed: {e}")
                    return ToolErrorResult(error=str(e), tool_name=tool_name)

                return result
    ```

*   **Justification**: This centralizes policy enforcement in the service layer with clear, non-configurable policies. Violations raise exceptions (fail-fast). The decorator becomes a simple transformer. Breaking change: Policy enforcement moves to a different layer.

---

### Part 3: Improving Clarity and Responsibility

This section proposes changes to clarify component responsibilities and improve the overall design.

#### 3.1. Make `CombatService` Stateless

*   **Context**: The `CombatService` currently holds state (`_last_prompted_entity_id`, `_last_prompted_round`) to track whether the AI has forgotten to call `next_turn`. This makes the service stateful, which can be harder to test and reason about.

*   **Proposed Change**:
    1.  Remove all state from `CombatService` (delete `_last_prompted_entity_id`, `_last_prompted_round`).
    2.  Pass tracking state as parameters to `generate_combat_prompt`.
    3.  Move state management to the `combat_loop` orchestrator where it belongs.

    ```python
    # In app/services/game/combat_service.py
    class CombatService(ICombatService):
        def __init__(...):
            # Remove these lines:
            # self._last_prompted_entity_id: str | None = None
            # self._last_prompted_round: int = 0
            pass

        def generate_combat_prompt(
            self,
            game_state: GameState,
            last_entity_id: str | None = None,
            last_round: int = 0
        ) -> str:
            """Generate combat prompt with optional duplicate detection.

            Args:
                game_state: Current game state
                last_entity_id: Previously prompted entity ID for duplicate detection
                last_round: Previously prompted round number
            """
            if not game_state.combat.is_active:
                return ""

            current_turn = game_state.combat.get_current_turn()
            if not current_turn:
                return "No active participants remain in combat. Use end_combat to conclude."

            round_num = game_state.combat.round_number

            # Check for duplicate prompt (stateless check via parameters)
            reminder = ""
            if last_entity_id == current_turn.entity_id and last_round == round_num:
                reminder = (
                    "\n\nIMPORTANT: You are still processing the same turn. "
                    "Did you forget to call next_turn after the previous action?"
                )

            # Generate prompt without maintaining state
            if current_turn.is_player:
                return f"Round {round_num}: {current_turn.name}'s turn...{reminder}"
            else:
                return f"Round {round_num}: {current_turn.name}'s turn...{reminder}"

    # In app/services/ai/orchestrator/combat_loop.py
    async def run(...):
        # State management in the orchestrator
        last_prompted_entity_id: str | None = None
        last_prompted_round: int = 0

        while iterations < max_iterations:
            current_turn = game_state.combat.get_current_turn()

            # Generate prompt with tracking parameters
            auto_prompt = combat_service.generate_combat_prompt(
                game_state,
                last_entity_id=last_prompted_entity_id,
                last_round=last_prompted_round
            )

            # Update tracking state in orchestrator
            if current_turn:
                last_prompted_entity_id = current_turn.entity_id
                last_prompted_round = game_state.combat.round_number

            # ... continue with agent processing ...
    ```

*   **Justification**: This makes `CombatService` purely stateless and thread-safe. The orchestrator owns the loop state, which is the cleanest separation of concerns. The service provides pure functions without side effects. Breaking change: Method signature changes.

---

## 4. Implementation Order

Based on dependencies and risk, the recommended implementation order is:

1. **Issue 1.2** (SaveManager exceptions) - Low risk, isolated change
2. **Issue 3.1** (CombatService stateless) - Medium risk, affects combat flow
3. **Issue 2.1** (ItemFactory) - Medium risk, new service addition
4. **Issue 1.1** (Context builders) - Higher risk, affects many builders
5. **Issue 2.2** (Policy enforcement) - Highest risk, affects all tool usage

## 5. Summary

All five refactoring proposals have been validated against the codebase and refined based on feedback:

- **Validated Issues**: All issues are confirmed valid and align with CLAUDE.md principles
- **Breaking Changes**: All changes will be implemented as breaking changes
- **Error Handling**: Standard exceptions with fail-fast behavior
- **Architecture**: Consistent with existing patterns (singleton services, DI via container)
- **Type Safety**: Enhanced through BuildContext and explicit interfaces

The refactoring will improve:
- **Testability**: Stateless services and builders
- **Maintainability**: Clear separation of concerns
- **Reliability**: Fail-fast error handling
- **Consistency**: Unified patterns across the codebase