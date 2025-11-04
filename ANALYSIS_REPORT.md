# Comprehensive Analysis Report: Combat Context & Flow Issues

**Date:** 2025-11-04
**Analyzed By:** Claude Code
**Codebase:** AI D&D Demo (refactor/orchestration branch)

---

## Executive Summary

This report analyzes four related issues in the combat and context building system:

1. **Combat Context Visibility - Spells**: Party member spells missing from Combat agent context
2. **Combat Context Visibility - Attacks**: Entity attacks/actions completely missing from all agents
3. **Spell Description Truncation**: Spell descriptions limited to 100 characters, missing critical mechanics
4. **next_turn Flow Issues**: Two problems:
   - Agents can skip calling `next_turn`, causing stuck combat
   - Agents can call `next_turn` multiple times in one response, skipping turns

All issues share a common theme: **information asymmetry** between what agents need to perform their roles and what they currently receive.

---

## Issue #1: Combat Context Missing Attacks/Actions

### Problem Statement

**Entity attacks are completely invisible to AI agents.** The system stores detailed `AttackAction` objects for every entity (attack bonus, damage, range, properties) but never includes them in agent context.

### Current State

**Attack Data Model** ([app/models/attributes.py:64-116](app/models/attributes.py#L64-L116)):
```python
class AttackAction(BaseModel):
    name: str                           # e.g., "Longsword", "Bite"
    attack_roll_bonus: int              # +5 to hit
    damage: str                         # "1d8+3"
    damage_type: str                    # "slashing", "piercing", etc.
    range: str = "melee"                # "melee" or "ranged"
    properties: list[str]               # ["Finesse", "Light", "Two-Handed"]
    type: str = "Melee"                 # Attack type
    reach: str = "5 ft."                # Reach distance
    special: str = ""                   # Special effects
```

**Storage Location:**
- Player: `game_state.character.state.attacks: list[AttackAction]`
- NPCs: `game_state.get_npc_by_id(id).state.attacks: list[AttackAction]`
- Monsters: `game_state.get_entity_by_id(EntityType.MONSTER, id).state.attacks: list[AttackAction]`

**Attack Computation** ([app/services/character/compute_service.py:389-446](app/services/character/compute_service.py#L389-L446)):
- For characters/NPCs: Computed from equipped weapons in `main_hand`/`off_hand` slots
- Calculates `attack_roll_bonus = ability_mod + proficiency_bonus`
- Formats damage as `base_dice + modifier` (e.g., "1d8+3")
- Determines ability mod based on weapon properties (Finesse uses higher of STR/DEX)
- Fallback: Unarmed Strike (1+STR mod bludgeoning) if no weapons equipped
- For monsters: Copied directly from `MonsterSheet.attacks` ([monster_manager_service.py:62-68](app/services/game/monster_manager_service.py#L62-L68))

**Context Gap:**
- ❌ No `ActionsContextBuilder` exists
- ❌ Combat Agent doesn't see any entity's attacks
- ❌ Narrative Agent doesn't see any entity's attacks
- ❌ NPC Agents don't see their own attacks

**Example - What Combat Agent SHOULD See But Doesn't:**
```
Available Actions (Goblin Scout):
  • Scimitar: +4 to hit, 1d6+2 slashing, Melee, Finesse, Light
  • Shortbow: +4 to hit, 1d6+2 piercing, Ranged (80/320 ft.), Ammunition

Available Actions (Aldric Swiftarrow):
  • Longsword: +5 to hit, 1d8+3 slashing, Melee, Versatile
  • Longbow: +6 to hit, 1d8+4 piercing, Ranged (150/600 ft.), Ammunition, Heavy
```

### Impact

**Severity: HIGH**

**Consequences:**
- 🔴 Combat Agent cannot reference actual attack bonuses when narrating attacks
- 🔴 Agents improvise damage formulas instead of using computed values
- 🔴 Cannot accurately describe weapon properties (Finesse, Heavy, Reach, etc.)
- 🔴 Monster special attacks (Bite, Claw, Breath Weapon) completely hidden
- 🔴 NPCs responding during combat (@npc_name) can't reference their own capabilities
- 🔴 Tactical suggestions become generic ("attack the goblin") instead of specific ("use your Longbow since you have +6 to hit at range")

### Recommended Solution: Create ActionsContextBuilder

**Implementation:**

**File 1:** Create [app/services/ai/context/builders/actions_builder.py](app/services/ai/context/builders/actions_builder.py)

```python
"""Build available actions/attacks context for entities."""

from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.npc_instance import NPCInstance

from .base import BuildContext, EntityContextBuilder


class ActionsContextBuilder(EntityContextBuilder):
    """Build available actions/attacks for any entity.

    Shows computed attacks with bonuses, damage, range, and properties.
    Critical for combat agents to understand entity capabilities.
    """

    MAX_ACTIONS = 10

    def build(
        self,
        game_state: GameState,
        context: BuildContext,
        entity: CharacterInstance | NPCInstance,
    ) -> str | None:
        # Extract entity name based on type
        entity_name = entity.display_name if isinstance(entity, NPCInstance) else entity.sheet.name

        entity_state = entity.state
        if not entity_state.attacks:
            return None

        context_parts = [f"Available Actions ({entity_name}):"]

        for attack in entity_state.attacks[: self.MAX_ACTIONS]:
            # Format: "• Name: +X to hit, damage damage_type, range, [properties]"
            parts = [
                f"  • {attack.name}: +{attack.attack_roll_bonus} to hit",
                f"{attack.damage} {attack.damage_type}",
                attack.range.capitalize(),
            ]

            if attack.reach and attack.reach != "5 ft.":
                parts.append(f"Reach {attack.reach}")

            if attack.properties:
                parts.append(f"[{', '.join(attack.properties)}]")

            if attack.special:
                parts.append(f"({attack.special})")

            context_parts.append(", ".join(parts))

        return "\n".join(context_parts)
```

**File 2:** Update [app/services/ai/context/context_service.py](app/services/ai/context/context_service.py)

```python
# Line 9-24: Add import
from app.services.ai.context.builders import (
    ActionsContextBuilder,  # ← Add this
    CombatContextBuilder,
    # ... rest of imports
)

# Line 46-67: Add to _create_builders()
def _create_builders(self) -> BuilderRegistry:
    return BuilderRegistry(
        scenario=ScenarioContextBuilder(),
        combat=CombatContextBuilder(),
        party_full=PartyOverviewBuilder(detail_level=DetailLevel.FULL),
        party_summary=PartyOverviewBuilder(detail_level=DetailLevel.SUMMARY),
        location=LocationContextBuilder(),
        location_memory=LocationMemoryContextBuilder(),
        world_memory=WorldMemoryContextBuilder(),
        npc_location=NPCLocationContextBuilder(),
        monsters_location=MonstersAtLocationContextBuilder(),
        quests=QuestContextBuilder(),
        spells=SpellContextBuilder(),
        inventory=InventoryContextBuilder(),
        roleplay=RoleplayInfoBuilder(),
        npc_persona=NPCPersonaContextBuilder(),
        actions=ActionsContextBuilder(),  # ← Add this
    )

# Line 106-118: Update COMBAT composition
AgentType.COMBAT: (
    ContextComposition()
    # Combat state and turn order
    .add(b.combat)
    .add(b.party_full)
    # Player character abilities
    .add_for_entities(b.actions, lambda gs: [gs.character])       # ← Add this
    .add_for_entities(b.spells, lambda gs: [gs.character])
    .add_for_entities(b.inventory, lambda gs: [gs.character])
    # Party member abilities (actions, spells, inventory - no roleplay)
    .add_for_entities(b.actions, self._get_party_members)         # ← Add this
    .add_for_entities(b.spells, self._get_party_members)
    .add_for_entities(b.inventory, self._get_party_members)
)

# Line 128-157: Update NPC composition
def build_context_for_npc(self, game_state: GameState, npc: NPCInstance) -> str:
    build_ctx = self._create_build_context(game_state)
    b = self._builders

    is_party_member = game_state.party.has_member(npc.instance_id)
    party_builder = b.party_full if is_party_member else b.party_summary

    composition = (
        ContextComposition()
        .add(party_builder)
        .add(b.combat)                               # ← Add combat context (Issue #1 part 1)
        # NPC's own details
        .add_for_entity(b.roleplay, npc)
        .add_for_entity(b.actions, npc)              # ← Add this
        .add_for_entity(b.spells, npc)
        .add_for_entity(b.inventory, npc)
        # World and scenario context
        .add(b.scenario)
        .add(b.location)
        .add(b.location_memory)
        .add(b.world_memory)
        .add(b.npc_location)
        .add(b.monsters_location)
        .add(b.quests)
    )

    return composition.build(game_state, build_ctx)
```

**File 3:** Update [app/services/ai/context/builders/__init__.py](app/services/ai/context/builders/__init__.py)

```python
from .actions_builder import ActionsContextBuilder  # ← Add this
from .combat_builder import CombatContextBuilder
# ... rest of imports

__all__ = [
    "ActionsContextBuilder",  # ← Add this
    "CombatContextBuilder",
    # ... rest of exports
]
```

**File 4:** Update [app/services/ai/context/composition.py](app/services/ai/context/composition.py) BuilderRegistry

```python
@dataclass(frozen=True)
class BuilderRegistry:
    """Registry of all available context builders."""
    scenario: ContextBuilder
    combat: ContextBuilder
    party_full: ContextBuilder
    party_summary: ContextBuilder
    location: ContextBuilder
    location_memory: ContextBuilder
    world_memory: ContextBuilder
    npc_location: ContextBuilder
    monsters_location: ContextBuilder
    quests: ContextBuilder
    spells: EntityContextBuilder
    inventory: EntityContextBuilder
    roleplay: EntityContextBuilder
    npc_persona: EntityContextBuilder
    actions: EntityContextBuilder  # ← Add this
```

### Benefits
- ✅ Combat Agent sees all available attacks for current combatant
- ✅ Accurate attack bonuses and damage formulas
- ✅ Weapon properties visible (Finesse, Heavy, Reach, Versatile)
- ✅ Monster special attacks visible
- ✅ NPC agents can reference their own capabilities
- ✅ Minimal code (~50 lines for builder + 10 lines for registration)
- ✅ Follows existing pattern (identical to SpellContextBuilder)
- ✅ Token cost: ~200-400 tokens per entity (acceptable)

### Testing
```python
# Test: Combat agent narrates attack using actual attack data
# Setup: Character with Longsword (+5 to hit, 1d8+3 slashing)
# Action: Combat agent processes monster turn attacking player
# Expected: Agent references actual attack bonus and damage formula
# Example: "The goblin swings its scimitar (+4 to hit) at Aldric..."
```

---

## Issue #2: Combat Context Missing Party NPCs' Spells

### Problem Statement

Combat Agent composition already includes party member spells ([context_service.py:116](app/services/ai/context/context_service.py#L116)), but NPC agents don't receive combat context (turn order, initiative).

### Current State

**Combat Agent** ([context_service.py:106-118](app/services/ai/context/context_service.py#L106-L118)):
```python
AgentType.COMBAT: (
    ContextComposition()
    .add(b.combat)                                    # ✅ Has combat context
    .add(b.party_full)
    .add_for_entities(b.spells, lambda gs: [gs.character])
    .add_for_entities(b.inventory, lambda gs: [gs.character])
    .add_for_entities(b.spells, self._get_party_members)        # ✅ Already included
    .add_for_entities(b.inventory, self._get_party_members)     # ✅ Already included
)
```

**NPC Agent** ([context_service.py:128-157](app/services/ai/context/context_service.py#L128-L157)):
```python
composition = (
    ContextComposition()
    .add(party_builder)
    # ❌ NO .add(b.combat) - missing turn order, initiative, combat state
    .add_for_entity(b.roleplay, npc)
    .add_for_entity(b.spells, npc)      # Only NPC's own spells
    # ... rest
)
```

### Impact

**Severity: MODERATE**

When player addresses NPC during combat (`@elara what should we do?`), the NPC lacks:
- ❌ Turn order and initiative
- ❌ Current round number
- ❌ Which entities are active/defeated
- ❌ Combat phase awareness

This leads to contextually inappropriate responses (suggesting attacks on distant enemies, not knowing turn order).

### Recommended Solution

**Already included in Issue #1 solution above** - see line with comment `# ← Add combat context (Issue #1 part 1)` in the NPC composition.

Adding `.add(b.combat)` to NPC composition gives NPCs full tactical awareness during combat.

---

## Issue #3: Spell Description Truncation

### Problem Statement

Spell descriptions are truncated to 100 characters ([spell_builder.py:40](app/services/ai/context/builders/spell_builder.py#L40)), losing critical mechanics like AoE, damage dice, save types, and duration.

### Current State

**Spell Model** ([app/models/spell.py:68-69](app/models/spell.py#L68-L69)):
```python
class SpellDefinition(BaseModel):
    description: str                           # ✅ Full description available
    higher_levels: str | None = None           # ✅ Upcast info available
```

**Data Quality:**
- ✅ All 319/319 spells have full descriptions in [data/spells.json](data/spells.json)
- ✅ Descriptions average 200-400 characters

**Current Truncation** ([spell_builder.py:37-40](app/services/ai/context/builders/spell_builder.py#L37-L40)):
```python
for spell_name in spells[: self.MAX_SPELLS]:
    try:
        spell_def = context.spell_repository.get(spell_name)
        context_parts.append(f"  • {spell_name} (Lvl {spell_def.level}): {spell_def.description[:100]}...")
        #                                                                 ^^^^^^^^^^^^^^^^ Only 100 chars
```

**Example Loss:**
```
Fireball (Full):
  "A bright streak flashes from your pointing finger to a point you choose within range
   and then blossoms with a low roar into an explosion of flame. Each creature in a
   20-foot-radius sphere centered on that point must make a Dexterity saving throw.
   A target takes 8d6 fire damage on a failed save, or half as much damage on a successful one."

Fireball (Truncated to 100 chars):
  "A bright streak flashes from your pointing finger to a point you choose within range
   and then blossom..."

Missing:
  - Area of Effect: 20-foot radius sphere
  - Save Type: Dexterity
  - Damage: 8d6 fire
  - Save Effect: Half damage on success
```

### Impact

**Severity: MODERATE**

**Consequences:**
- ⚠️ Complex utility spells lose mechanics (Leomund's Tiny Hut, Glyph of Warding)
- ⚠️ Spells with conditions unclear (Hold Person - humanoid only)
- ⚠️ Variable effects from upcasting (`higher_levels` field) not shown
- ⚠️ Duration and concentration requirements often cut off

**Mitigating Factors:**
- ✅ Agents can improvise based on spell name
- ✅ Combat Agent primarily executes player intent, not spell mechanics

### Recommended Solution: Increase Truncation to 200 Characters

**Implementation:**

**File:** [app/services/ai/context/builders/spell_builder.py](app/services/ai/context/builders/spell_builder.py)

```python
class SpellContextBuilder(EntityContextBuilder):
    """Build known spells context using the spell repository."""

    MAX_SPELLS = 10
    MAX_DESCRIPTION_LENGTH = 200  # ← Add this constant (was implicit 100)

    def build(
        self,
        game_state: GameState,
        context: BuildContext,
        entity: CharacterInstance | NPCInstance,
    ) -> str | None:
        # ... existing code ...

        for spell_name in spells[: self.MAX_SPELLS]:
            try:
                spell_def = context.spell_repository.get(spell_name)
                # Use the constant instead of hardcoded 100
                context_parts.append(
                    f"  • {spell_name} (Lvl {spell_def.level}): {spell_def.description[:self.MAX_DESCRIPTION_LENGTH]}..."
                )
            except RepositoryNotFoundError:
                logger.warning(f"Spell '{spell_name}' not found in spell repository")
                context_parts.append(f"  • {spell_name} [NOT IN REPOSITORY - Improvise mechanics as needed]")

        return "\n".join(context_parts)
```

### Benefits
- ✅ Captures most spell mechanics (AoE, damage, save type, duration)
- ✅ Still optimizes token usage (50% reduction vs full descriptions)
- ✅ Configurable via class constant
- ✅ Token increase: ~1,250 additional tokens (acceptable)

### Token Impact
```
Current (100 chars): 10 spells × 100 chars × 5 entities = 5,000 chars ≈ 1,250 tokens
Proposed (200 chars): 10 spells × 200 chars × 5 entities = 10,000 chars ≈ 2,500 tokens
Increase: +1,250 tokens per context build (well within model limits)
```

---

## Issue #4: next_turn Flow Issues

### Problem Statement - Part A: Missing next_turn Calls

Combat Agent can skip calling `next_turn`, causing combat to get stuck on the same turn. Current enforcement is "soft" (prompt reminders) rather than "hard" (validation).

**Current Enforcement** ([combat_service.py:201-210](app/services/game/combat_service.py#L201-L210)):
```python
# Check for duplicate prompt
if last_entity_id == current_turn.entity_id and last_round == round_num:
    reminder = (
        "\n\nIMPORTANT: You are still processing the same turn. "
        "Did you forget to call next_turn after the previous action? "
        "Remember: You MUST call next_turn after EVERY turn to advance combat."
    )
    logger.warning(f"Same entity prompted twice: {current_turn.name} - likely missing next_turn call")
```

**Issue:** This only adds a reminder to the prompt, doesn't prevent execution or auto-fix.

### Problem Statement - Part B: Multiple next_turn Calls

**New Issue:** LLMs occasionally call `next_turn` multiple times within a single tool call batch. Each call advances the turn index ([combat_handler.py:231](app/events/handlers/combat_handler.py#L231)):

```python
elif isinstance(command, NextTurnCommand):
    # ... validation ...
    game_state.combat.next_turn()  # ← Advances turn index immediately
    # No check for "already advanced this response"
```

**Consequence:** If Combat Agent generates:
```
Tool Calls:
1. update_hp(entity_id="goblin-1", damage=8)
2. next_turn()  # ← Advances from Goblin 1 to Elara
3. next_turn()  # ← Advances from Elara to Player (skipped Elara's turn!)
4. next_turn()  # ← Advances from Player to Goblin 2 (skipped Player's turn!)
```

Result: Multiple turns skipped, combat sequence broken, players/NPCs never get their turns.

### Impact

**Severity: HIGH**

**Part A (Missing next_turn):**
- 🔴 Combat stuck on same turn indefinitely
- 🔴 User must manually intervene or restart combat
- 🔴 Auto-continue loop may hit max iterations (20) and halt

**Part B (Multiple next_turn):**
- 🔴 **Critical:** Skips player turns entirely
- 🔴 Skips ally NPC turns
- 🔴 Breaks turn-based combat contract
- 🔴 Users lose agency over their character

### Recommended Solution: Comprehensive Turn Validation

**Implementation:**

**File:** [app/services/ai/orchestration/steps/execute_combat_agent.py](app/services/ai/orchestration/steps/execute_combat_agent.py)

```python
"""Execute combat agent step with turn progression validation."""

import logging

from app.agents.core.base import BaseAgent
from app.agents.core.types import AgentType
from app.events.commands.broadcast_commands import BroadcastSystemMessageCommand
from app.events.commands.combat_commands import NextTurnCommand
from app.interfaces.services.ai import IContextService
from app.models.ai_response import StreamEvent
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class ExecuteCombatAgent:
    """Execute the combat agent with comprehensive turn progression validation.

    Validates:
    1. Pre-execution: Detect duplicate prompts, auto-advance if needed
    2. During execution: Track next_turn calls, prevent multiple calls
    3. Post-execution: Ensure turn advanced exactly once
    """

    def __init__(
        self,
        combat_agent: BaseAgent,
        context_service: IContextService,
    ) -> None:
        """Initialize with combat agent and context service."""
        self.combat_agent = combat_agent
        self.context_service = context_service

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute the combat agent with turn validation."""
        if not ctx.current_prompt:
            logger.warning("No current_prompt for combat agent")
            return StepResult.continue_with(ctx)

        if not ctx.game_state.combat.is_active:
            logger.debug("Combat not active, skipping combat agent")
            return StepResult.continue_with(ctx)

        # ===== PRE-EXECUTION: Detect duplicate prompt =====
        current_turn = ctx.game_state.combat.get_current_turn()
        if current_turn and (
            ctx.flags.last_prompted_entity_id == current_turn.entity_id
            and ctx.flags.last_prompted_round == ctx.game_state.combat.round_number
        ):
            logger.warning(
                f"[COMBAT] Duplicate turn detected: {current_turn.name} (Round {ctx.game_state.combat.round_number}). "
                f"Previous action did not call next_turn. Auto-advancing to prevent stuck combat."
            )

            # Broadcast system message to user
            await ctx.dependencies.event_bus.submit_and_wait([
                BroadcastSystemMessageCommand(
                    game_id=ctx.game_state.game_id,
                    message=f"⚠️ Auto-advanced turn for {current_turn.name} (agent did not call next_turn)",
                    level="warning",
                )
            ])

            # Auto-advance turn
            await ctx.dependencies.event_bus.submit_and_wait([NextTurnCommand(game_id=ctx.game_state.game_id)])

            # Reload state and update context
            game_state = await ctx.dependencies.game_service.load_game(ctx.game_state.game_id)
            ctx = ctx.replace(game_state=game_state)
            current_turn = ctx.game_state.combat.get_current_turn()

        # Store pre-execution state for validation
        entity_id_before = current_turn.entity_id if current_turn else None
        round_before = ctx.game_state.combat.round_number

        # Build combat context
        combat_context = self.context_service.build_context(
            ctx.game_state,
            AgentType.COMBAT,
        )

        logger.debug("Executing combat agent: prompt='%s...'", ctx.current_prompt[:80])

        # ===== EXECUTE COMBAT AGENT =====
        events: list[StreamEvent] = []
        next_turn_count = 0  # Track next_turn calls during execution

        async for event in self.combat_agent.process(
            ctx.current_prompt,
            ctx.game_state,
            combat_context,
            stream=True,
        ):
            events.append(event)

            # ===== DURING EXECUTION: Track next_turn calls =====
            # Check if this event is a tool call for next_turn
            if hasattr(event, 'tool_name') and event.tool_name == 'next_turn':
                next_turn_count += 1

                if next_turn_count > 1:
                    logger.error(
                        f"[COMBAT] Agent called next_turn {next_turn_count} times in single response! "
                        f"This will skip turns. Only the first call should be honored."
                    )

                    # Broadcast critical error
                    await ctx.dependencies.event_bus.submit_and_wait([
                        BroadcastSystemMessageCommand(
                            game_id=ctx.game_state.game_id,
                            message=f"🔴 CRITICAL: Agent called next_turn {next_turn_count} times. Only first call honored.",
                            level="error",
                        )
                    ])

                    # NOTE: We can't prevent the tool call here since it's already dispatched
                    # The best we can do is log and alert. Prevention must happen in tool handler.

        logger.debug(f"Combat agent completed: {len(events)} events, {next_turn_count} next_turn calls")

        # ===== POST-EXECUTION: Validate turn advancement =====
        game_state = await ctx.dependencies.game_service.load_game(ctx.game_state.game_id)

        if game_state.combat.is_active:
            current_turn_after = game_state.combat.get_current_turn()
            round_after = game_state.combat.round_number

            if current_turn_after and entity_id_before:
                # Check if turn didn't advance at all
                if (current_turn_after.entity_id == entity_id_before and round_after == round_before):
                    logger.warning(
                        f"[COMBAT] Combat agent did not call next_turn for {current_turn_after.name} (Round {round_after}). "
                        f"Auto-advancing to prevent stuck combat."
                    )

                    await ctx.dependencies.event_bus.submit_and_wait([
                        BroadcastSystemMessageCommand(
                            game_id=ctx.game_state.game_id,
                            message=f"⚠️ Auto-advanced turn (agent forgot next_turn)",
                            level="warning",
                        )
                    ])

                    await ctx.dependencies.event_bus.submit_and_wait([NextTurnCommand(game_id=ctx.game_state.game_id)])
                    game_state = await ctx.dependencies.game_service.load_game(ctx.game_state.game_id)

        # Update orchestration flags for next iteration
        current_turn_final = game_state.combat.get_current_turn()
        updated_flags = ctx.flags.replace(
            last_prompted_entity_id=current_turn_final.entity_id if current_turn_final else None,
            last_prompted_round=game_state.combat.round_number,
        )

        # Update context with accumulated events
        updated_ctx = ctx.replace(game_state=game_state, flags=updated_flags).add_events(events)
        return StepResult.continue_with(updated_ctx)
```

**Part B Solution:** Prevent multiple next_turn calls using SOLID-compliant guard service

**Important:** Initial handler-based batch tracking approaches were found to be flawed (see [TOOL_EXECUTION_ANALYSIS.md](TOOL_EXECUTION_ANALYSIS.md) for detailed flow analysis). The correct solution uses the `AgentDependencies` lifecycle to track execution state.

**Implementation:** See [SOLID_TOOL_EXECUTION_SOLUTION.md](SOLID_TOOL_EXECUTION_SOLUTION.md) for complete SOLID-compliant architecture.

**Summary:**

Create two new classes following Single Responsibility Principle:

1. **`ToolExecutionContext`** (data holder) - Tracks tool call counts per execution
2. **`ToolExecutionGuard`** (service) - Validates tool execution rules

Add both to `AgentDependencies` as separate, clearly-defined dependencies:

```python
@dataclass
class AgentDependencies:
    # ... existing fields ...

    # Tool Execution Tracking (new)
    tool_execution_context: ToolExecutionContext  # Mutable state (per-execution)
    tool_execution_guard: ToolExecutionGuard      # Validation service (singleton)
```

**In tool decorator** ([app/tools/decorators.py](app/tools/decorators.py)):

```python
@wraps(func)
async def wrapper(ctx: RunContext[AgentDependencies], **kwargs: Any) -> BaseModel:
    tool_name = func.__name__

    # Validate using guard service
    guard = ctx.deps.tool_execution_guard
    execution_ctx = ctx.deps.tool_execution_context

    validation_error = guard.validate_tool_call(tool_name, execution_ctx)
    if validation_error:
        return validation_error  # Block duplicate next_turn calls

    # Record the call
    guard.record_tool_call(tool_name, execution_ctx)

    # ... continue with existing command execution ...
```

**Why this works:**
- ✅ `AgentDependencies` lifetime = one agent execution
- ✅ Fresh `ToolExecutionContext` per execution (automatic reset)
- ✅ Blocks duplicate calls BEFORE they reach command handler
- ✅ SOLID compliant (SRP, OCP, DIP all satisfied)
- ✅ No concurrency issues (each agent has own context)

**Files to create:**
- `app/services/common/tool_execution_context.py` (~30 lines)
- `app/services/common/tool_execution_guard.py` (~70 lines)

### Benefits
- ✅ **Part A (Missing next_turn):** Auto-advances to prevent stuck combat
- ✅ **Part B (Multiple next_turn):** Detects and prevents turn skipping
- ✅ **Observable:** Logs warnings/errors for monitoring
- ✅ **User-friendly:** System messages explain what happened
- ✅ **Self-healing:** Combat continues smoothly even with agent errors
- ✅ **Non-breaking:** No changes to agent contract

### Testing

**Test A: Missing next_turn**
```python
# Test: Auto-advance prevents stuck combat
# Setup: Mock combat agent that "forgets" next_turn
# Action: Execute combat turn
# Expected: Orchestration logs warning, auto-advances, combat continues
# Verify: Turn index increments, no infinite loop
```

**Test B: Multiple next_turn**
```python
# Test: Prevent turn skipping from multiple next_turn calls
# Setup: Mock combat agent that calls next_turn 3 times
# Action: Execute combat turn
# Expected:
#   - First next_turn call passes validation, executes successfully
#   - Second next_turn call blocked by ToolExecutionGuard at tool decorator level
#   - Third next_turn call also blocked
#   - Agent receives ToolErrorResult for 2nd and 3rd calls
#   - Turn advances exactly once (only first call executed)
# Verify: Turn index increments by 1, player turn not skipped
```

---

## Summary of All Fixes

| Issue | Severity | Changes Required | Files to Modify | Est. Time |
|-------|----------|------------------|-----------------|-----------|
| **#1: Missing Attacks Context** | HIGH | Create ActionsContextBuilder + register in compositions | 4 files (~100 lines) | 1-2 hours |
| **#2: NPC Combat Context** | MODERATE | Add `.add(b.combat)` to NPC composition | 1 file (1 line) | 5 minutes |
| **#3: Spell Descriptions** | MODERATE | Add MAX_DESCRIPTION_LENGTH constant, use it | 1 file (2 lines) | 5 minutes |
| **#4A: Missing next_turn** | HIGH | Pre/post validation in execute_combat_agent | 1 file (~40 lines) | 1 hour |
| **#4B: Multiple next_turn** | HIGH | SOLID guard service + context (see SOLID_TOOL_EXECUTION_SOLUTION.md) | 6 files (~120 lines) | 1.5 hours |

**Total Estimated Time:** 4-5 hours including testing

---

## Implementation Priority

**Recommended Order:**
1. **Issue #4** (next_turn validation) - Prevents critical combat flow failures
2. **Issue #1** (Actions context) - Provides accurate combat capabilities
3. **Issue #2** (NPC combat context) - Improves tactical NPC dialogue
4. **Issue #3** (Spell descriptions) - Polish for better spell understanding

---

## Files to Modify

### Issue #1: Actions Context
- **NEW:** [app/services/ai/context/builders/actions_builder.py](app/services/ai/context/builders/actions_builder.py)
- [app/services/ai/context/builders/__init__.py](app/services/ai/context/builders/__init__.py)
- [app/services/ai/context/context_service.py](app/services/ai/context/context_service.py)
- [app/services/ai/context/composition.py](app/services/ai/context/composition.py)

### Issue #2: NPC Combat Context
- [app/services/ai/context/context_service.py](app/services/ai/context/context_service.py) (Line 128-157)

### Issue #3: Spell Descriptions
- [app/services/ai/context/builders/spell_builder.py](app/services/ai/context/builders/spell_builder.py) (Lines 19, 40)

### Issue #4A: Missing next_turn Validation
- [app/services/ai/orchestration/steps/execute_combat_agent.py](app/services/ai/orchestration/steps/execute_combat_agent.py) (Pre/post validation)
- [app/services/ai/orchestration/context.py](app/services/ai/orchestration/context.py) (Ensure OrchestrationFlags.replace() exists)

### Issue #4B: Multiple next_turn Prevention
- **NEW:** [app/services/common/tool_execution_context.py](app/services/common/tool_execution_context.py)
- **NEW:** [app/services/common/tool_execution_guard.py](app/services/common/tool_execution_guard.py)
- [app/agents/core/dependencies.py](app/agents/core/dependencies.py) (Add 2 fields)
- [app/tools/decorators.py](app/tools/decorators.py) (Add validation logic)
- [app/agents/combat/agent.py](app/agents/combat/agent.py) (Add context/guard to deps)
- [app/agents/narrative/agent.py](app/agents/narrative/agent.py) (Add context/guard to deps)
- [app/agents/npc/base.py](app/agents/npc/base.py) (Add context/guard to deps)

---

## Implementation Checklist

### Issue #1: Actions Context
- [ ] Create [actions_builder.py](app/services/ai/context/builders/actions_builder.py) following spell_builder pattern
- [ ] Add to [__init__.py](app/services/ai/context/builders/__init__.py) imports
- [ ] Register in [context_service.py](app/services/ai/context/context_service.py) BuilderRegistry
- [ ] Add to [composition.py](app/services/ai/context/composition.py) BuilderRegistry type
- [ ] Add to COMBAT composition (player + party members)
- [ ] Add to NPC composition (own actions)
- [ ] Test with character with equipped weapon
- [ ] Test with monster with multiple attacks
- [ ] Run `mypy --strict app tests`
- [ ] Run `pytest`

### Issue #2: NPC Combat Context
- [ ] Add `.add(b.combat)` to NPC composition in [context_service.py:140](app/services/ai/context/context_service.py#L140)
- [ ] Test NPC dialogue during combat (`@npc_name what should we do?`)
- [ ] Verify NPC response references turn order/initiative
- [ ] Monitor context size in logs

### Issue #3: Spell Descriptions
- [ ] Add `MAX_DESCRIPTION_LENGTH = 200` constant to [spell_builder.py:19](app/services/ai/context/builders/spell_builder.py#L19)
- [ ] Update truncation at line 40 to use constant
- [ ] Test with spell-heavy character (10+ spells)
- [ ] Verify spell mechanics visible in context

### Issue #4A: Missing next_turn Validation
- [ ] Update [execute_combat_agent.py](app/services/ai/orchestration/steps/execute_combat_agent.py) with pre/post validation
- [ ] Create `BroadcastSystemMessageCommand` if not exists
- [ ] Test missing next_turn scenario (should auto-advance)
- [ ] Verify OrchestrationFlags.replace() method exists
- [ ] Monitor warning logs for frequency

### Issue #4B: Multiple next_turn Prevention (SOLID Solution)
- [ ] Create [tool_execution_context.py](app/services/common/tool_execution_context.py) data holder
- [ ] Create [tool_execution_guard.py](app/services/common/tool_execution_guard.py) service
- [ ] Add fields to [dependencies.py](app/agents/core/dependencies.py)
- [ ] Add validation logic to [decorators.py](app/tools/decorators.py)
- [ ] Update [combat/agent.py](app/agents/combat/agent.py) deps creation
- [ ] Update [narrative/agent.py](app/agents/narrative/agent.py) deps creation
- [ ] Update [npc/base.py](app/agents/npc/base.py) deps creation
- [ ] Test multiple next_turn scenario (should block 2nd+ calls at tool level)
- [ ] Test guard service in isolation (unit tests)
- [ ] Verify ToolErrorResult is returned to agent
- [ ] Run `mypy --strict app tests`

---

## Conclusion

All four issues have clear, implementable solutions that align with the codebase's principles:

✅ **Type Safety:** No new `Any` types, all models strongly typed
✅ **SOLID:** Single responsibility builders, dependency injection via composition
✅ **DRY:** Reuses existing patterns (actions follows spells, validation follows guards)
✅ **Fail Fast:** Validation catches issues immediately with auto-healing
✅ **Explicit:** Clear what each agent receives via declarative composition

The combined implementation addresses critical combat flow issues while improving tactical awareness for all agents.
