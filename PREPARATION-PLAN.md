Based on the provided codebase and the `NPC-PARTY-PLAN.md`, here is a detailed preparation plan to ensure the implementation is smooth, robust, and aligns with the project's core principles of SOLID, DRY, and Fail-Fast.

---

# Preparation Plan for NPC Party System Implementation

This document outlines the necessary preparatory refactoring and foundational work required before implementing the features described in `NPC-PARTY-PLAN.md`. By completing these steps first, we ensure the new party system is built upon a clean, stable, and maintainable architecture, fully aligned with the principles defined in `CLAUDE.md`.

This plan leverages the excellent analysis from `REPORT.md` and identifies additional enhancements that will directly support the upcoming party system features.

## 1. Foundational Enhancements for the Party System

These are new preparatory steps not covered in `REPORT.md` but are crucial for a robust party system.

### 1.1. Unify and Strengthen Entity Resolution (Fail-Fast & Robustness)

**Objective:** Enhance the entity resolver to provide a single, reliable function for finding any entity (Player, NPC, Monster) by its ID, with robust fuzzy matching and clear error handling.

**Why this is critical for the Party Plan:** The `CombatService` will need to resolve entities to determine their `CombatFaction`. The new `PartyService` will need to resolve NPC IDs to add them to the party. The new party-related agent tools will take `npc_id` strings as input. A centralized, powerful resolver makes all these features less brittle and adheres to the DRY principle.

**Action Items:**

1.  **File to Modify:** `app/utils/entity_resolver.py`.
2.  **Enhance `resolve_entity_with_fallback`:**
    *   Ensure this function can reliably find a Player, NPC, or Monster from a given `entity_id` string.
    *   Refine its fallback logic to be deterministic: exact match first, then fuzzy match.
    *   Ensure it returns a clear `(IEntity | None, EntityType | None)` tuple so the caller knows what type of entity was found.
3.  **Integrate the Resolver:**
    *   Update all services that currently perform manual lookups (e.g., `EntityHandler`) to use this new, centralized function. This prepares the codebase for the new services (`PartyService`, `CombatSuggestionService`) to do the same.

### 1.2. Pre-define Core Data Models for Party and Combat Factions

**Objective:** Implement the non-behavioral Pydantic models required by the party plan before implementing the services that use them.

**Why this is critical for the Party Plan:** This "model-first" approach aligns with the project's type-safety principle. It allows the new services (`PartyService`, `CombatService` changes) to be written against concrete, well-defined data structures from day one, reducing integration friction.

**Action Items:**

1.  **Create New File:** `app/models/party.py`
    *   Define the `PartyState` class as specified in the plan:
        ```python
        class PartyState(BaseModel):
            member_ids: list[str] = Field(default_factory=list)
            max_size: int = 4
        ```
2.  **Modify File:** `app/models/game_state.py`
    *   Add the new `party` field: `party: PartyState = Field(default_factory=PartyState)`.
3.  **Modify File:** `app/models/combat.py`
    *   Add the `CombatFaction` enum: `PLAYER | ALLY | ENEMY | NEUTRAL`.
    *   Add the `faction: CombatFaction` field to the `CombatParticipant` model. This field will be populated by `CombatService` later, but defining it now ensures the data contract is clear.

---

## Summary of Benefits and Next Steps

By completing this preparation plan, the codebase will be in a much stronger position for the implementation of the NPC Party System:

*   **SOLID:** `GameState` will be a pure data aggregate, and services will have clear, single responsibilities.
*   **DRY:** Agent logic will be centralized, making the creation and invocation of the NPC suggestion agent much cleaner.
*   **Fail-Fast & Robust:** A unified entity resolver will make services like `PartyService` and `CombatService` more resilient to bad inputs from the AI.

Once these preparatory tasks are complete, the development of the features outlined in `NPC-PARTY-PLAN.md` can begin, following its step-by-step guide on a solid and maintainable foundation.