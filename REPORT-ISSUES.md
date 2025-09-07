## Issue 3: Refactor `ContextService`

### Investigation

The `ContextService` is highly cohesive—all its methods work together to build a single string. However, its `build_context` method is long, and the class itself is tightly coupled to various repositories. The internal structure using private `_build_*` methods is already a step towards modularity.

### Proposed Fix

Refactor the `ContextService` using the **Strategy Pattern**. Each part of the context will be built by a dedicated, single-purpose class.

1.  **Create a `context_builder` Module:**
    *   Create a new directory: `app/services/ai/context_builders/`.
    *   Add a base class: `app/services/ai/context_builders/base.py`:
      ```python
      from abc import ABC, abstractmethod
      from app.models.game_state import GameState

      class ContextBuilder(ABC):
          @abstractmethod
          def build(self, game_state: GameState) -> str | None:
              """Builds a specific part of the context string."""
              pass
      ```
2.  **Implement Strategy Classes:** Create separate builder classes for each context section. Each will have its own specific dependencies, making them explicit.

    *   `location_builder.py`:
      ```python
      class LocationContextBuilder(ContextBuilder):
          # No external dependencies needed, uses game_state.scenario_instance.sheet
          def build(self, game_state: GameState) -> str | None:
              # ... logic from _build_location_context
      ```
    *   `spell_builder.py`:
      ```python
      from app.interfaces.services import ISpellRepository

      class SpellContextBuilder(ContextBuilder):
          def __init__(self, spell_repository: ISpellRepository):
              self.spell_repository = spell_repository

          def build(self, game_state: GameState) -> str | None:
              # ... logic from _build_spell_context
      ```
    *   Create similar builders for `Combat`, `Quests`, `NPCs`, etc.

3.  **Refactor `ContextService`:** The main service now becomes a coordinator that composes the final string from the output of its builders.

    ```python
    # app/services/ai/context_service.py (AFTER)
    from .context_builders import (
        LocationContextBuilder, CombatContextBuilder, # etc.
    )

    class ContextService:
        def __init__(self, item_repository: IItemRepository, ...):
            # Instantiate all builders with their required dependencies
            self.builders = [
                LocationContextBuilder(),
                CombatContextBuilder(),
                QuestContextBuilder(),
                SpellContextBuilder(spell_repository),
                # ... other builders
            ]

        def build_context(self, game_state: GameState) -> str:
            context_parts = [builder.build(game_state) for builder in self.builders]
            return "\n\n".join(part for part in context_parts if part)
    ```

This approach makes the `ContextService` much cleaner, easier to test, and extensible. Adding, removing, or re-ordering context sections becomes trivial.

---

## Issue 4: Re-organize the Code

### Investigation

*   **Routes:** `app/api/routes.py` is over 500 lines long, mixing game actions, saved game management, and a large number of data catalog endpoints. This is a clear candidate for splitting.
*   **Interfaces:** `app/interfaces/services.py` contains all service interfaces in one file. As the number of services grows, this becomes unwieldy. The structure does not mirror the implementation in `app/services/`, which is confusing.

### Proposed Fix

1.  **Split API Routes into Sub-Routers:**
    *   Create a new directory: `app/api/routers/`.
    *   Create separate router files within it: `game.py`, `catalogs.py`, `scenarios.py`, `characters.py`.
    *   Move the relevant endpoints from `routes.py` into these new files. Each file will define its own `APIRouter`.
    *   Update the main `app/api/routes.py` (or a new `app/api/v1.py`) to import and include these sub-routers.

    **Example New Structure:**
    ```
    app/api/
    ├── __init__.py
    ├── routes.py       # Main router that includes others
    └── routers/
        ├── __init__.py
        ├── catalogs.py   # Endpoints for /catalogs/*
        ├── characters.py # Endpoints for /characters
        ├── game.py       # Endpoints for /game/*
        └── scenarios.py  # Endpoints for /scenarios/*
    ```

2.  **Re-organize Service Interfaces:**
    *   Create a directory structure for interfaces that mirrors the services.
    *   **New Structure:**
      ```
      app/interfaces/
      ├── __init__.py
      ├── events.py           # IEventBus
      └── services/
          ├── __init__.py
          ├── ai.py             # IAIService, IMessageService
          ├── character.py      # ICharacterService, ICharacterComputeService
          ├── common.py         # IPathResolver, IBroadcastService
          ├── game.py           # IGameService, IGameStateManager, ISaveManager, etc.
          └── repositories.py   # IRepository, IItemRepository, etc.
      ```
    *   Move each interface definition into the corresponding new file.
    *   Update all import paths across the application to reflect the new locations. This is a mechanical but necessary change for long-term maintainability.

This reorganization will make the project structure highly intuitive and scalable, aligning the interfaces directly with their implementations.