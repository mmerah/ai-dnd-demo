# TYPE-SAFETY-PLAN.md

## 1. Overview & Guiding Principles

The primary goal of this refactoring is to achieve end-to-end type safety using Pydantic `BaseModel`. The codebase currently relies on `dict[str, Any]`, `TypedDict`, and `JSONSerializable` in several key areas, which undermines the benefits of a typed language.

**Guiding Principles:**
1.  **Model as the Source of Truth**: Core Pydantic models defined in `app/models/` should be used throughout the application. Data should exist as a `dict` only at the boundaries (API requests/responses, reading from files).
2.  **Eliminate `Any` and Generic `dict`**: Replace all occurrences of `Any` and generic dictionaries like `dict[str, Any]` with specific `BaseModel` definitions.
3.  **DRY (Don't Repeat Yourself)**: Remove redundant models. API response models that are subsets of core models (`GameState`, `CharacterSheet`) should be eliminated. Use the core models directly.
4.  **Strongly-Typed Boundaries**: Functions, services, and API endpoints should explicitly declare `BaseModel` types in their signatures for inputs and outputs.
5.  **SOLID**: Changes should reinforce the Single Responsibility Principle. For instance, models define data structure, services handle business logic, and APIs handle communication.

## 2. Refactoring Plan by Module

### 2.1. Core Models (`app/models/`)

#### Issue: Redundant API and AI Response Models

-   **Files**: `app/models/ai_response.py`, `app/models/api_responses.py`
-   **Problem**: `AIResponse` is a `TypedDict`, which is less powerful than `BaseModel`. `api_responses.py` contains many models (`SavedGameSummary`, `ItemDetailResponse`, `SpellDetailResponse`) that are either subsets of or duplicates of core models. This violates DRY.
-   **Solution**:
    1.  **Remove `app/models/api_responses.py`**:
        -   Delete the file entirely.
        -   Update API routes in `app/api/routes.py` to use core models directly. For example:
            -   `list_saved_games` should return `list[SavedGameSummary]` where `SavedGameSummary` is a new, lean `BaseModel` defined in `app/models/game_state.py`.
            -   `get_item_details` should return `app.models.item.ItemDefinition`.
            -   `get_spell_details` should return `app.models.spell.SpellDefinition`.
    2.  **Refactor `app/models/ai_response.py`**:
        -   The `AIResponse` `TypedDict` should be removed. The `AIService` already yields `StreamEvent`, which is a `BaseModel`. The background task in `app/api/tasks.py` should be updated to handle these events directly instead of expecting dictionaries.

#### Issue: Overuse of `JSONSerializable`

-   **File**: `app/models/game_state.py`
-   **Problem**: The `JSONSerializable` type alias is a workaround for a lack of specific types, particularly in `GameEvent` for `parameters` and `result`.
-   **Solution**:
    1.  **Make `GameEvent` Generic**: While powerful, this can add complexity. A more pragmatic approach is to define a union of all possible tool parameter and result models.
    2.  **Pragmatic Solution**: The `parameters` and `result` fields will remain `dict` and `Any` for now, but their population will be strictly controlled. The `add_game_event` service method will be the *only* place that accepts a `BaseModel` and converts it to a `dict` for storage, ensuring the rest of the application deals with models.

    ```python
    # app/services/game_service.py

    # The service method signature enforces that a BaseModel must be passed
    def add_game_event(
        self,
        game_id: str,
        event_type: GameEventType,
        tool_name: str | None = None,
        parameters: BaseModel | None = None, # Changed from dict
        result: BaseModel | None = None, # Changed from JSONSerializable
        metadata: dict[str, JSONSerializable] | None = None,
    ) -> GameState:
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        game_state.add_game_event(
            event_type=event_type,
            tool_name=tool_name,
            # Convert to dict only at the boundary
            parameters=parameters.model_dump(mode="json") if parameters else None,
            result=result.model_dump(mode="json") if result else None,
            metadata=metadata,
        )
        self.save_game(game_state)
        return game_state
    ```

### 2.2. Services (`app/services/`)

#### Issue: Services Returning Dictionaries Instead of Models

-   **Files**: `app/services/game_service.py`, `app/services/character_service.py`
-   **Problem**: `game_service.list_saved_games()` and `character_service.list_characters()` return `list[dict]`, forcing the API layer to handle raw data.
-   **Solution**:
    1.  **Define Summary Models**: Create new, lean `BaseModel`s for summaries.
        ```python
        # app/models/game_state.py
        class SavedGameSummary(BaseModel):
            game_id: str
            character_name: str
            location: str
            last_played: datetime
            scenario_title: str | None = None

        # app/models/character.py
        class CharacterSummary(BaseModel):
            id: str
            name: str
            race: str
            class_name: str # Renamed from 'class' to avoid keyword conflict
            level: int
        ```
    2.  **Update Service Methods**: Refactor the service methods to return lists of these new models.

        ```python
        # app/services/game_service.py
        def list_saved_games(self) -> list[SavedGameSummary]: # Return type changed
            games = []
            for save_file in self.save_directory.glob("*.json"):
                # ... (logic to load and parse)
                games.append(
                    SavedGameSummary( # Create model instance
                        game_id=data["game_id"],
                        character_name=data["character"]["name"],
                        # ... other fields
                    )
                )
            # ... (sorting logic)
            return games

        # app/services/character_service.py
        def list_characters(self) -> list[CharacterSummary]: # Return type changed
            characters = []
            for char_id, character in self._characters.items():
                characters.append(
                    CharacterSummary( # Create model instance
                        id=char_id,
                        name=character.name,
                        race=character.race,
                        class_name=character.class_name,
                        level=character.level,
                    )
                )
            return characters
        ```
    3.  **Update API Routes**: The corresponding API routes will now seamlessly work with these typed lists.

### 2.3. Event & Command System (`app/events/`)

#### Issue: Loosely Typed Command Payloads and Results

-   **Files**: `app/events/base.py`, `app/events/event_bus.py`, various command files and handlers.
-   **Problem**:
    -   `StartCombatCommand` and `SpawnMonstersCommand` use `list[dict]`.
    -   `CommandResult.data` is `dict[str, Any] | None`. This is the central point of type ambiguity.
    -   Handlers manually construct dictionaries for results.
-   **Solution**:
    1.  **Create Models for Command Payloads**:
        ```python
        # In a new file app/models/combat.py or similar
        class CombatantInfo(BaseModel):
            name: str
            initiative: int | None = None

        class MonsterSpawnInfo(BaseModel):
            monster_name: str
            quantity: int = 1

        # app/events/commands/combat_commands.py
        @dataclass
        class StartCombatCommand(BaseCommand):
            npcs: list[CombatantInfo] = field(default_factory=list) # Changed from dict
        
        @dataclass
        class SpawnMonstersCommand(BaseCommand):
            monsters: list[MonsterSpawnInfo] = field(default_factory=list) # Changed from dict
        ```
    2.  **Make `CommandResult` Use `BaseModel`**: The `data` field should store a `BaseModel` instance directly. The `.model_dump()` conversion should happen at the last possible moment (in the Event Bus).

        ```python
        # app/events/base.py
        class CommandResult:
            def __init__(self, success: bool, data: BaseModel | None = None, error: str | None = None): # Changed type to BaseModel
                self.success = success
                self.data = data # Store the model instance
                self.error = error
                self.follow_up_commands: list[BaseCommand] = []
        ```
    3.  **Refactor Event Handlers**: Handlers must now instantiate result models from `app/models/tool_results.py` instead of creating dictionaries.

        ```python
        # app/events/handlers/character_handler.py (example for UpdateHPCommand)
        # ...
        result_model = UpdateHPResult( # Create a Pydantic model instance
            target=command.target,
            old_hp=old_hp,
            new_hp=new_hp,
            # ... all other fields
        )
        result.data = result_model # Assign the model to result.data
        # ...
        ```
    4.  **Update Event Bus**: The event bus will now handle the model-to-dict conversion.

        ```python
        # app/events/event_bus.py
        async def execute_command(self, command: BaseCommand) -> dict[str, Any] | None:
            # ... (handler execution logic) ...
            result = await handler.handle(command, game_state)

            # ... (error and follow-up command logic) ...

            # Convert model to dict at the very end before returning
            return result.data.model_dump(mode="json") if result.data else None
        ```

### 2.4. Tools (`app/tools/`)

#### Issue: Tool Functions Return `dict[str, Any]`

-   **Files**: All files in `app/tools/`.
-   **Problem**: Tool function signatures and the `@tool_handler` decorator are typed to return `dict[str, Any]`, which defeats the purpose of static typing.
-   **Solution**:
    1.  **Update Tool Signatures**: Change the return type hint of every tool function to its corresponding `BaseModel` from `app/models/tool_results.py`.
    2.  **Refactor `@tool_handler`**: Modify the decorator to correctly handle the `BaseModel` returned by the command execution.

        ```python
        # app/tools/decorators.py
        def tool_handler(command_class: type[BaseCommand]) -> Callable[..., Callable[..., Coroutine[Any, Any, BaseModel]]]: # Return BaseModel
            def decorator(
                func: Callable[..., Coroutine[Any, Any, BaseModel]], # Expect BaseModel
            ) -> Callable[..., Coroutine[Any, Any, BaseModel]]: # Return BaseModel
                @wraps(func)
                async def wrapper(ctx: RunContext[AgentDependencies], **kwargs: Any) -> BaseModel: # Return BaseModel
                    # ... (broadcast and command creation logic)
                    
                    # execute_command now returns a dict, but the original command result contains the model.
                    # We need to adjust this flow. Let's make execute_command return the model.
                    # OR, even better, the CommandResult object itself.

                    # New plan for the handler:
                    command = command_class(game_id=game_state.game_id, **kwargs)
                    
                    # Event bus should return the model instance, not the dict
                    result_model = await event_bus.execute_command(command)

                    if not isinstance(result_model, BaseModel):
                        raise RuntimeError(f"Command for tool {func.__name__} did not return a Pydantic model.")
                    
                    return result_model # Return the model directly
        ```
    3.  **Adjust `EventBus.execute_command`**: To support the decorator change, `execute_command` must return the `BaseModel` instance, not a `dict`.

        ```python
        # app/events/event_bus.py
        async def execute_command(self, command: BaseCommand) -> BaseModel | None: # Return type changed
            # ... (handler execution)
            result = await handler.handle(command, game_state)
            # ... (error handling)
            return result.data # Return the BaseModel instance from CommandResult
        ```

### 2.5. API Layer (`app/api/`)

#### Issue: Unnecessary Model Duplication and Manual Broadcasting

-   **Files**: `app/api/routes.py`, `app/api/tasks.py`
-   **Problem**:
    -   As mentioned, routes use custom `api_responses` models instead of core models.
    -   The `process_ai_and_broadcast` task manually sends update events (`send_character_update`, `send_game_update`, etc.). This is brittle and duplicates logic. The `EventBus` and `Handlers` should be the *only* source of broadcasts.
-   **Solution**:
    1.  **Update Route Signatures**:
        -   Change `response_model` to point to core `BaseModel`s or the new `Summary` models.
        -   Example: `GET /characters` should have `response_model=list[CharacterSummary]`.
    2.  **Simplify the Background Task**: The `process_ai_and_broadcast` task should be significantly simplified. Its only job is to call the `AIService`, which triggers tools, which trigger commands, which are handled by `Handlers`, which in turn trigger broadcast commands handled by the `BroadcastHandler`. This creates a clean, unidirectional data flow.

        ```python
        # app/api/tasks.py
        async def process_ai_and_broadcast(game_id: str, message: str) -> None:
            # ... (setup)
            try:
                # ... (load game_state)

                # The AIService.generate_response will trigger the entire event flow.
                # The event bus will process all commands, including broadcasts, sequentially.
                async for chunk in ai_service.generate_response(...):
                    # We only need to consume the generator to drive the process.
                    # All broadcasting is now handled by the BroadcastHandler via the event bus.
                    if chunk["type"] == "error":
                        # Handle final error if AI process fails completely
                        await message_service.send_error(game_id, chunk["message"])
                
                # Signal completion
                complete_data = CompleteData(status="success")
                await broadcast_service.publish(game_id, SSEEventType.COMPLETE, complete_data)
            
            except Exception as e:
                # ... (error handling)
        ```
    This change dramatically improves adherence to the Single Responsibility Principle. The API task is only responsible for orchestrating the AI call, not for knowing *what* to broadcast.

## 3. Summary of Benefits

-   **Full Type Safety**: Eliminates a major source of runtime bugs and improves code quality.
-   **Reduced Complexity**: Fewer models to maintain and reason about.
-   **Improved Maintainability**: Clear, unidirectional data flow makes the system easier to debug and extend.
-   **Enhanced Developer Experience**: Static analysis and autocompletion will be far more effective.
-   **Stronger Adherence to Principles**: Reinforces DRY, SOLID, and KISS across the entire application.