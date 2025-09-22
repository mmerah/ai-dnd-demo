# Architecture Improvement & Refactoring Plan

This document outlines a plan to update documentation, enforce core architectural principles (Fail-Fast, SOLID, DRY), and simplify the existing codebase for the AI DnD project.

## Status: Implementation In Progress

### Code Analysis Findings (2025-09-22)
After thorough code analysis, the following findings and decisions were made:

---

## 1. Fail-Fast Principle Enforcement

### **Context**
The principle of "Fail-Fast" dictates that errors should be reported as early as possible. Overusing optional parameters (`| None`) can hide bugs, where a `None` value is passed down through several layers before causing a `NoneType` error. We will enforce stricter contracts by making parameters non-optional where a value is always expected.

### **Action Items**

1.  **`app.tools.location_tools.change_location`**
    *   **Issue:** `location_name` and `description` are optional. If the `location_id` is for a new, ad-hoc location (not defined in a scenario), the system has no way to name or describe it, leading to a poor user experience or potential errors downstream.
    *   **Finding:** The validation already exists in `LocationService.move_entity()` (lines 81-87), which raises errors if name/description are missing for non-scenario locations. However, this happens at the service layer rather than the handler layer.
    *   **Decision:** Keep current implementation as it already enforces fail-fast at the service layer. The service correctly validates and raises `ValueError` when required fields are missing.

2.  **`app.services.character.character_service.update_hp`**
    *   **Issue:** The `entity_id` parameter is `str | None`, where `None` is implicitly treated as the player. This is not explicit and can be confusing.
    *   **Finding:** Tools already require non-optional `entity_id: str`. The service layer `_resolve_entity()` (lines 197-224) still accepts `None` and maps it to player.
    *   **Decision:** Remove `None` → player mapping entirely. Make `entity_id` strictly required everywhere. All callers must explicitly pass `game_state.character.instance_id` when targeting the player.
    *   **Implementation:**
        1.  Refactor `update_hp` and other state modification methods (`add_condition`, `remove_condition`, `modify_currency`, `equip_item`) to require non-optional `entity_id: str`.
        2.  Remove the `None` → player mapping logic from `_resolve_entity()`.
        3.  Update all callers to explicitly pass player's instance_id.

3.  **`app.tools.combat_tools.start_combat`**
    *   **Issue:** The `entity_ids` list could be empty, leading to a combat scenario starting with no participants other than the player.
    *   **Finding:** No validation exists in `CombatHandler` (lines 75-114) to prevent empty `entity_ids` list.
    *   **Decision:** Add validation to ensure at least one entity is provided.
    *   **Implementation:** In the `CombatHandler` for `StartCombatCommand`, add a check: `if not command.entity_ids: raise ValueError("start_combat requires at least one entity_id.")`. This ensures combat is always initiated with a clear opponent.

---

## 2. SOLID & DRY Principles Refactoring

### **Context**
Adherence to SOLID and DRY principles is critical for long-term maintainability. This involves ensuring classes have a single responsibility, centralizing duplicated logic, and depending on abstractions, not concretions.

### **Action Items**

#### 2.1. Refactor `CharacterService` (Single Responsibility Principle)
*   **Issue:** `CharacterService` currently handles three distinct responsibilities:
    1.  **Loading/Validation:** Loading character sheets from files and validating their references against repositories.
    2.  **State Computation:** Calculating derived stats (`ICharacterComputeService` is a good abstraction, but the implementation is inside the service).
    3.  **Runtime State Mutation:** Modifying HP, conditions, inventory, and currency.
*   **Finding:** Confirmed - `CharacterService` has methods spanning lines 78-195 (loading/validation), 226-229 (computation delegation), and 197-393 (runtime mutations).
*   **Decision:** Split into two services with clear responsibilities.
*   **Implementation:**
    1.  Rename `CharacterService` to `CharacterSheetService` - focus **only on loading and validation** of `CharacterSheet` templates.
    2.  Create a new `EntityStateService` that implements `IEntityStateService` (a new interface). This service will contain the methods for runtime mutations: `update_hp`, `add_condition`, `remove_condition`, `modify_currency`, `modify_inventory`, and `equip_item`.
    3.  Update `ICharacterService` interface to only include loading/validation methods.
    4.  The `CharacterHandler`, `InventoryHandler`, etc., will now depend on `IEntityStateService` instead of `ICharacterService` for state mutations.
    5.  This change better separates the concerns of static data management from dynamic runtime state management.

#### 2.2. Centralize Entity Resolution (Don't Repeat Yourself)
*   **Issue:** `CharacterService` has a private `_resolve_entity` method. A more robust, fuzzy-matching implementation already exists in `app/utils/entity_resolver.py`. Logic for finding entities is scattered.
*   **Finding:** Confirmed duplication - `CharacterService._resolve_entity()` (lines 197-224) is a simpler version of what `entity_resolver.py` provides with fuzzy matching support.
*   **Decision:** Use the centralized implementation everywhere.
*   **Implementation:**
    1.  Remove the `_resolve_entity` method from `CharacterService`.
    2.  The new `EntityStateService` will use `resolve_entity_with_fallback()` from `entity_resolver.py`.
    3.  All handlers and services that need to find an entity will exclusively use functions from `app/utils/entity_resolver.py`.
    4.  The `resolve_entity_with_fallback` function becomes the standard way to look up an entity from an AI-provided ID.

---

## 3. General Code Simplification & Review

### **Context**
This section covers smaller, targeted improvements to enhance code clarity, remove redundancy, and improve the developer experience.

### **Action Items**

1.  **Simplify NPC Dialogue Flow in `AgentOrchestrator`**
    *   **Issue:** The logic for handling NPC dialogue is currently inside the main `process` method, making it dense.
    *   **Finding:** Confirmed - NPC dialogue logic spans lines 64-70 and 173-210 in `orchestrator_service.py`. The `_handle_npc_dialogue()` helper method already exists but could be better utilized.
    *   **Decision:** Keep existing extraction, code is already well-organized.
    *   **Implementation:** No changes needed - the code already has `_handle_npc_dialogue()` as a helper method.

2.  **Clarify Combat Auto-Continuation**
    *   **Issue:** The `combat_loop.run` function handles auto-advancing turns for NPCs and monsters. However, the logic for *when* to call this loop is in the `AgentOrchestrator`. This can be confusing.
    *   **Finding:** Combat continuation logic is spread across lines 86-140 in `orchestrator_service.py` with multiple state reloads and conditional checks.
    *   **Decision:** Extract logic into named helper methods for clarity.
    *   **Implementation:** Extract combat-related logic into helper methods like `_handle_combat_start()`, `_handle_combat_continuation()`, and `_handle_combat_end()` to make the flow more readable.

3.  **Deprecate `MessageManager` in favor of `ConversationService`**
    *   **Issue:** Both `MessageManager` and `ConversationService` exist and seem to have overlapping responsibilities related to adding messages to the `GameState`. `ConversationService` is a higher-level abstraction that also handles persistence.
    *   **Finding:** `MessageManager` only adds messages (lines 13-40), while `ConversationService` wraps it and adds metadata extraction + persistence. Clear separation but could be simplified.
    *   **Decision:** Fully merge MessageManager into ConversationService.
    *   **Implementation:**
        1.  Migrate the `add_message` logic from `MessageManager` directly into `ConversationService`.
        2.  Remove `MessageManager` class and its interface (`IMessageManager`).
        3.  Update the `Container` and all dependent services to use `IConversationService` directly. This simplifies the dependency chain and adheres to DRY.

---

## Implementation Priority

Based on complexity and impact, the implementation order will be:

1. **Phase 1 - Fail-Fast (Quick Wins)**
   - Add validation for empty `entity_ids` in `start_combat`
   - Remove `None` → player mapping in CharacterService

2. **Phase 2 - Code Simplification**
   - Extract combat continuation logic in AgentOrchestrator into helper methods
   - Merge MessageManager into ConversationService

3. **Phase 3 - Major Refactoring**
   - Refactor CharacterService to use centralized entity_resolver
   - Split CharacterService into CharacterSheetService and EntityStateService