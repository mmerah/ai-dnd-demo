Of course! Here is a detailed analysis and a set of recommendations to streamline your application's logging, apply the DRY principle, and remove unused code.

---

# Code Refactoring and Cleanup Plan

This document provides a detailed plan for improving the maintainability, readability, and efficiency of the D&D AI Dungeon Master application. The recommendations are based on an analysis of the provided codebase and logs.

## 1. Log Streamlining

The current logging at the `DEBUG` level is very verbose and contains redundant information, making it difficult to trace a single request. The goal is to make `INFO` logs a high-level summary of the application flow and `DEBUG` logs detailed but concise.

### Recommendations

#### Redundant Tool Call Logging (`app/agents/narrative_agent.py`)

The `event_stream_handler` logs the same tool call multiple times due to `pydantic-ai` emitting several event types (`PartStartEvent`, `FunctionToolCallEvent`).

-   **Log Message to Consolidate:**
    -   `[TOOL_CALL] roll_ability_check: {'ability': 'WIS', ...}` (from `PartStartEvent`)
    -   `[TOOL_CALL] roll_ability_check: {'raw_args': '{\n  "ability": "WIS", ...}` (from `FunctionToolCallEvent`)

-   **Suggestion:** Modify `event_stream_handler` to log a tool call only once. Track tool call IDs and log only the first time an ID is seen.

    ```python
    # In app/agents/narrative_agent.py, inside event_stream_handler
    
    # ...
    tool_calls_by_id: dict[str, str] = {}
    processed_tool_calls: set[str] = set() # Add this set
    
    async for event in event_stream:
        # ...
        if isinstance(event.part, ToolCallPart):
            tool_call_id = getattr(event.part, "tool_call_id", None)
            if tool_call_id and tool_call_id in processed_tool_calls:
                continue # Skip if already processed
            
            # ... process and log the tool call ...
            
            if tool_call_id:
                processed_tool_calls.add(tool_call_id)
    ```

#### Overly Verbose `INFO` Logs

Certain logs at the `INFO` level are better suited for `DEBUG`.

-   **Log Message to Re-level (`app/services/broadcast_service.py`):**
    -   `INFO: Publishing event 'tool_call' to 1 subscribers...`
    -   `INFO: Tool event data: {'tool_name': 'roll_ability_check', ...}`
-   **Reasoning:** The fact that a tool call occurred is important, but the number of subscribers and the full data payload are debugging details. The high-level action is the tool call itself, which is already logged by the `EventLoggerService`.
-   **Suggestion:** Change these log levels from `INFO` to `DEBUG`.

-   **Log Message to Re-level (`app/agents/narrative_agent.py`):**
    -   `INFO: Response generated: You glance around the bustling tavern...`
-   **Reasoning:** Logging the first 100 characters of the response is useful for debugging but clutters the `INFO` logs.
-   **Suggestion:** Change this log level to `DEBUG`.

#### Repetitive HTTP Request/Response Logs

The logs show detailed HTTP connection and header information from `httpcore` and `httpx`.

-   **Log Message to Tame:**
    -   `DEBUG - connect_tcp.started...`
    -   `DEBUG - start_tls.started...`
    -   `INFO - HTTP Request: POST ...`
-   **Reasoning:** This is library-level logging. While useful for network debugging, it's often too noisy for application-level tracing.
-   **Suggestion:** Configure logging in `app/main.py` to set the log level for third-party libraries like `httpx` and `httpcore` to `WARNING` unless a specific debug flag is enabled.

    ```python
    # In app/main.py
    logging.basicConfig(...)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    ```

## 2. Applying DRY (Don't Repeat Yourself)

Several parts of the codebase contain repetitive boilerplate logic that can be abstracted.

### Backend: Tool Implementation Boilerplate

All tool functions in `app/tools/*.py` follow the exact same pattern:
1.  Get `game_state` and `event_bus` from `ctx`.
2.  Submit a `BroadcastToolCallCommand`.
3.  Execute a domain-specific command.
4.  Return the result or a fallback dictionary.

-   **Suggestion:** Create a decorator or a higher-order function to abstract this pattern.

    **Example: Creating a `tool_handler` decorator**

    ```python
    # Create a new file: app/tools/decorators.py
    from functools import wraps
    from typing import Any, Callable, Coroutine
    
    from pydantic_ai import RunContext
    
    from app.agents.dependencies import AgentDependencies
    from app.events.base import BaseCommand
    from app.events.commands.broadcast_commands import BroadcastToolCallCommand
    
    def tool_handler(command_class: type[BaseCommand]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
        def decorator(func: Callable[..., Coroutine[Any, Any, dict[str, Any]]]) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
            @wraps(func)
            async def wrapper(ctx: RunContext[AgentDependencies], **kwargs: Any) -> dict[str, Any]:
                game_state = ctx.deps.game_state
                event_bus = ctx.deps.event_bus
                tool_name = func.__name__
    
                # 1. Broadcast tool call
                await event_bus.submit_command(
                    BroadcastToolCallCommand(
                        game_id=game_state.game_id, tool_name=tool_name, parameters=kwargs
                    )
                )
    
                # 2. Execute domain command
                command = command_class(game_id=game_state.game_id, **kwargs)
                result = await event_bus.execute_command(command)
    
                # 3. Return result
                return result if result else {"status": "executed", "tool": tool_name, **kwargs}
    
            return wrapper
        return decorator
    
    # Then refactor tools like app/tools/character_tools.py:
    from .decorators import tool_handler
    
    @tool_handler(UpdateHPCommand)
    async def update_hp(
        ctx: RunContext[AgentDependencies], amount: int, damage_type: str = "untyped", target: str = "player"
    ) -> dict[str, Any]:
        """Update hit points for damage or healing... (docstring remains)"""
        # The entire function body is now handled by the decorator!
        # Pydantic-AI will pass the arguments to the decorator's kwargs.
        # We only need 'pass' if there's no additional logic.
        pass
    ```

### Frontend: Message Creation

In `frontend/app.js`, the `addMessage` function is well-structured, but the creation of system/notification messages in `showError` and `showNotification` repeats DOM creation logic.

-   **Suggestion:** Refactor `showError` and `showNotification` to call the central `addMessage` function.

    ```javascript
    // In frontend/app.js
    
    function showError(message) {
        console.error(`[ERROR] ${message}`);
        // Use the existing addMessage function with a specific class
        addMessage(`❌ Error: ${message}`, 'error');
    }
    
    function showNotification(message) {
        console.log(`[NOTIFICATION] ${message}`);
        const notification = addMessage(`✅ ${message}`, 'success');
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    ```

## 3. Unused Code Removal

The codebase contains several components that are defined but not used, likely from earlier design stages. Removing them will simplify the project.

### Unused `GameService` Methods

The `GameService` has many public methods for direct state manipulation (`update_character_hp`, `add_item`, `modify_currency`, etc.). The current architecture correctly routes all state changes through the `EventBus` and `Handlers`. The handlers then call `save_game` after modifying the state object.

-   **Identified Methods:**
    -   `update_character_hp`
    -   `add_npc` / `remove_npc`
    -   `start_combat` / `end_combat`
    -   `advance_time`
    -   `update_location`
    -   `modify_currency`
    -   `add_item` / `remove_item`
-   **Reasoning:** These methods are superseded by the command-handler pattern, which provides better separation of concerns and centralized state management logic. Keeping them creates a risk of state being modified outside the event-driven flow.
-   **Suggestion:** Remove these methods from `GameService` and its interface `IGameService`. The handlers should modify the `game_state` object directly and then call `game_service.save_game(game_state)`.

### Unused `AgentType` Enum Members

-   **File:** `app/agents/types.py`
-   **Unused Members:** `COMBAT`, `SUMMARIZER`
-   **Reasoning:** The `AgentFactory` only has an implementation for `NARRATIVE`. These other types are not used and can be removed until they are implemented.
-   **Suggestion:** Remove the `COMBAT` and `SUMMARIZER` members from the `AgentType` enum.

### Unused `GameEvent` and Related Logic

-   **File:** `app/models/game_state.py`
-   **Unused Components:** The `GameEvent` model and the `game_events` list within `GameState`.
-   **Reasoning:** The `narrative_agent` captures tool calls and results, but this data is used to yield a `StreamEvent` and is not persisted in the `GameState.game_events` list. The `game_service.add_game_event` method is never called.
-   **Suggestion:** Remove the `GameEvent` model, the `GameEventType` enum, the `game_events` field from `GameState`, and the `add_game_event` method from `GameService`.

### Frontend: Unused Dice Roll Visualization

-   **File:** `frontend/app.js`
-   **Unused Functionality:** The `showDiceRoll` function and the corresponding SSE event listener for `dice_roll`.
-   **Reasoning:** The backend `DiceHandler` broadcasts dice results via the `tool_result` event, not a dedicated `dice_roll` event. Therefore, the `dice_roll` listener in `app.js` is never triggered, and the `diceDisplay` UI element is never shown.
-   **Suggestion:**
    1.  **Option A (Remove):** Remove the `showDiceRoll` function, the `dice_roll` event listener, and the `#diceDisplay` element from `index.html` and `style.css`.
    2.  **Option B (Implement):** Modify `app/events/handlers/dice_handler.py` to also dispatch a `BroadcastDiceRoll` command, create a handler for it, and have it broadcast a `dice_roll` SSE event with the necessary data for the UI animation. This would make the feature functional. Option A is simpler if the feature is not a priority.

---

By implementing these changes, your application will become more robust, easier to debug, and more maintainable for future development.