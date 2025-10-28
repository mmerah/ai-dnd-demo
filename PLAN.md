# Implementation Plan: Tool Usage Verification System

## Executive Summary

Implement a general tool verification system to improve consistency in tool calling across all agents (Narrative, Combat, NPC). The system uses a **pre-flight advisory ToolSuggestorAgent** that analyzes context and suggests appropriate tools before agent execution, combined with **enhanced system prompts** and **party-aware context sharing**.

**Primary Issues Addressed:**
- Missing tool calls (most common)
- Wrong tool arguments (occasional)
- Inconsistent tool usage across all agents
- NPC agents lack narrative context when appropriate

**Solution Components:**
1. **ToolSuggestorAgent** - Pre-flight heuristic-based agent suggesting tools
2. **Enhanced System Prompts** - Concrete examples of tool usage patterns
3. **Party-Aware Context Sharing** - NPCs in party see narrative messages
4. **Model Upgrade** - PuppeteerAgent uses 120B model for consistency

---

## Architecture Overview

### Current Flow
```
User Input
    ↓
[Orchestrator] → determines agent type
    ↓
[Agent] → processes with tools
    ↓
Response
```

### New Flow
```
User Input
    ↓
[Orchestrator] → determines agent type
    ↓
[ToolSuggestorAgent] → analyzes context, suggests tools (advisory)
    ↓ (suggestions added to context)
[Agent] → processes with tools + suggestions
    ↓
Response
```

### Design Principles Alignment

**SOLID:**
- Single Responsibility: ToolSuggestorAgent only suggests, doesn't execute
- Open/Closed: Heuristic rules extensible via inheritance
- Liskov: Agent implements BaseAgent interface
- Interface Segregation: Uses IToolSuggestor protocol
- Dependency Inversion: Services injected via container

**Fail Fast:**
- Suggestions happen before agent runs (prevent issues)
- Invalid suggestions logged but don't block execution
- Type-safe suggestion models

**Tool-Driven:**
- Agent orchestrates heuristics, doesn't contain business logic
- Heuristic rules are composable services

---

## Phase 1: Core Infrastructure (Days 1-3)

### 1.1 Create Agent Type and Interface

**File:** `app/agents/core/types.py`
```python
class AgentType(str, Enum):
    NARRATIVE = "narrative"
    COMBAT = "combat"
    NPC = "npc"
    SUMMARIZER = "summarizer"
    TOOL_SUGGESTOR = "tool_suggestor"  # NEW
```

**File:** `app/interfaces/tool_suggestor.py` (NEW)
```python
"""Protocol for tool suggestion services."""

from typing import Protocol

from app.models.game_state import GameState
from app.models.tool_suggestion import ToolSuggestions


class IToolSuggestor(Protocol):
    """Interface for tool suggestion services."""

    async def suggest_tools(
        self,
        game_state: GameState,
        user_message: str,
        agent_type: AgentType,
    ) -> ToolSuggestions:
        """
        Analyze context and suggest tools for the agent.

        Args:
            game_state: Current game state
            user_message: User's input message
            agent_type: Type of agent that will execute

        Returns:
            ToolSuggestions with recommended tools and reasoning
        """
        ...
```

### 1.2 Create Tool Suggestion Models

**File:** `app/models/tool_suggestion.py` (NEW)
```python
"""Models for tool suggestions."""

from pydantic import BaseModel, Field


class ToolSuggestion(BaseModel):
    """A single tool suggestion."""

    tool_name: str = Field(..., description="Name of the suggested tool")
    reason: str = Field(..., description="Why this tool might be needed")
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)",
    )
    arguments: dict[str, str] | None = Field(
        default=None,
        description="Suggested argument values",
    )


class ToolSuggestions(BaseModel):
    """Collection of tool suggestions for an agent."""

    suggestions: list[ToolSuggestion] = Field(
        default_factory=list,
        description="List of suggested tools",
    )
    context_notes: list[str] = Field(
        default_factory=list,
        description="Additional contextual notes for the agent",
    )

    def format_for_prompt(self) -> str:
        """Format suggestions for inclusion in agent prompt."""
        if not self.suggestions:
            return ""

        parts = ["## Suggested Tools\n"]
        parts.append(
            "Based on the current context, you might want to consider these tools:\n"
        )

        for suggestion in self.suggestions:
            confidence_label = (
                "highly recommended" if suggestion.confidence >= 0.8
                else "recommended" if suggestion.confidence >= 0.5
                else "optional"
            )
            parts.append(f"- `{suggestion.tool_name}` ({confidence_label})")
            parts.append(f"  - Reason: {suggestion.reason}")
            if suggestion.arguments:
                args_str = ", ".join(f"{k}={v}" for k, v in suggestion.arguments.items())
                parts.append(f"  - Suggested args: {args_str}")

        if self.context_notes:
            parts.append("\n## Context Notes\n")
            for note in self.context_notes:
                parts.append(f"- {note}")

        parts.append("\nThese are suggestions only. Use your judgment to decide which tools are appropriate.")

        return "\n".join(parts)
```

### 1.3 Create Heuristic Rules System

**File:** `app/services/ai/tool_suggestion/heuristic_rules.py` (NEW)
```python
"""Heuristic rules for tool suggestion."""

import re
from abc import ABC, abstractmethod

from app.agents.core.types import AgentType
from app.models.game_state import GameState
from app.models.tool_suggestion import ToolSuggestion


class HeuristicRule(ABC):
    """Base class for heuristic rules."""

    @abstractmethod
    def evaluate(
        self,
        game_state: GameState,
        user_message: str,
        agent_type: AgentType,
    ) -> list[ToolSuggestion]:
        """
        Evaluate rule and return suggestions.

        Returns:
            List of tool suggestions (empty if rule doesn't apply)
        """
        ...


class QuestAcceptanceRule(HeuristicRule):
    """Suggest start_quest when user accepts a quest."""

    PATTERNS = [
        r"\b(accept|take|start|begin)\b.*\b(quest|mission|task|job)\b",
        r"\b(yes|ok|sure|fine)\b",  # After quest offer from NPC
        r"\b(i'?ll do it|i'?ll help|count me in)\b",
    ]

    def evaluate(
        self,
        game_state: GameState,
        user_message: str,
        agent_type: AgentType,
    ) -> list[ToolSuggestion]:
        """Check if user is accepting a quest."""
        # Only relevant for narrative and NPC agents
        if agent_type not in {AgentType.NARRATIVE, AgentType.NPC}:
            return []

        message_lower = user_message.lower()

        # Check patterns
        for pattern in self.PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                # Higher confidence if "quest" explicitly mentioned
                confidence = 0.8 if "quest" in message_lower else 0.6

                return [
                    ToolSuggestion(
                        tool_name="start_quest",
                        reason="User appears to be accepting a quest or mission",
                        confidence=confidence,
                    )
                ]

        return []


class ItemTransferRule(HeuristicRule):
    """Suggest modify_inventory when items are being given/taken."""

    GIVE_PATTERNS = [
        r"\b(give|hand|offer|present)\b.*\b(you|player)\b",
        r"\bhere'?s?\b.*\b(item|gold|coin|sword|armor|potion)\b",
        r"\btake this\b",
    ]

    TAKE_PATTERNS = [
        r"\b(take|grab|pick up|loot|get)\b.*\b(item|gold|coin|sword|armor|potion)\b",
        r"\bi (take|grab|pick up|loot) (the |it|them)\b",
    ]

    def evaluate(
        self,
        game_state: GameState,
        user_message: str,
        agent_type: AgentType,
    ) -> list[ToolSuggestion]:
        """Check if items are being transferred."""
        message_lower = user_message.lower()
        suggestions = []

        # Check for giving items (NPC agents)
        if agent_type == AgentType.NPC:
            for pattern in self.GIVE_PATTERNS:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    suggestions.append(
                        ToolSuggestion(
                            tool_name="modify_inventory",
                            reason="NPC appears to be giving an item to the player",
                            confidence=0.75,
                            arguments={"quantity": "1"},
                        )
                    )
                    break

        # Check for taking items (Narrative agent)
        if agent_type == AgentType.NARRATIVE:
            for pattern in self.TAKE_PATTERNS:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    suggestions.append(
                        ToolSuggestion(
                            tool_name="modify_inventory",
                            reason="Player appears to be taking an item",
                            confidence=0.7,
                            arguments={"quantity": "1"},
                        )
                    )
                    break

        return suggestions


class CombatEndRule(HeuristicRule):
    """Suggest end_combat when all enemies defeated."""

    def evaluate(
        self,
        game_state: GameState,
        user_message: str,
        agent_type: AgentType,
    ) -> list[ToolSuggestion]:
        """Check if combat should end."""
        # Only relevant for combat agent
        if agent_type != AgentType.COMBAT:
            return []

        # Check if combat is active
        if not game_state.combat.is_active:
            return []

        # Check if all enemies are defeated
        from app.models.combat import CombatFaction

        enemies_alive = any(
            p.current_hp > 0 and p.faction == CombatFaction.ENEMY
            for p in game_state.combat.participants
        )

        if not enemies_alive:
            return [
                ToolSuggestion(
                    tool_name="end_combat",
                    reason="All enemies have been defeated",
                    confidence=0.95,
                )
            ]

        return []


class NextTurnRule(HeuristicRule):
    """Suggest next_turn after any combat action."""

    def evaluate(
        self,
        game_state: GameState,
        user_message: str,
        agent_type: AgentType,
    ) -> list[ToolSuggestion]:
        """Check if next_turn should be called."""
        # Only relevant for combat agent
        if agent_type != AgentType.COMBAT:
            return []

        # If combat is active, next_turn is almost always needed
        if game_state.combat.is_active:
            return [
                ToolSuggestion(
                    tool_name="next_turn",
                    reason="Combat is active - next_turn should be called after each action",
                    confidence=0.9,
                )
            ]

        return []


class DamageApplicationRule(HeuristicRule):
    """Suggest update_hp after damage is dealt."""

    DAMAGE_PATTERNS = [
        r"\b(attack|hit|strike|slash|stab|shoot)\b",
        r"\b(\d+)\s*(damage|hp)\b",
        r"\b(deal|dealt|inflict)\b.*\b(damage)\b",
    ]

    def evaluate(
        self,
        game_state: GameState,
        user_message: str,
        agent_type: AgentType,
    ) -> list[ToolSuggestion]:
        """Check if damage needs to be applied."""
        # Relevant for narrative and combat agents
        if agent_type not in {AgentType.NARRATIVE, AgentType.COMBAT}:
            return []

        message_lower = user_message.lower()

        for pattern in self.DAMAGE_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return [
                    ToolSuggestion(
                        tool_name="update_hp",
                        reason="Damage appears to be dealt - HP should be updated",
                        confidence=0.8,
                    )
                ]

        return []


class LocationChangeRule(HeuristicRule):
    """Suggest change_location when traveling to named locations."""

    TRAVEL_PATTERNS = [
        r"\b(go to|travel to|head to|walk to|move to)\b.*\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",
        r"\b(enter|leave|exit)\b.*\b(town|city|village|tavern|dungeon|forest|cave)\b",
    ]

    def evaluate(
        self,
        game_state: GameState,
        user_message: str,
        agent_type: AgentType,
    ) -> list[ToolSuggestion]:
        """Check if player is traveling to a location."""
        # Only relevant for narrative agent
        if agent_type != AgentType.NARRATIVE:
            return []

        for pattern in self.TRAVEL_PATTERNS:
            if re.search(pattern, user_message, re.IGNORECASE):
                return [
                    ToolSuggestion(
                        tool_name="change_location",
                        reason="Player appears to be traveling to a new location",
                        confidence=0.7,
                    )
                ]

        return []


class RestRule(HeuristicRule):
    """Suggest rest tools when player wants to rest."""

    SHORT_REST_PATTERNS = [
        r"\b(short rest|take a break|rest for an hour|quick rest)\b",
    ]

    LONG_REST_PATTERNS = [
        r"\b(long rest|sleep|camp|rest for the night|take a nap)\b",
    ]

    def evaluate(
        self,
        game_state: GameState,
        user_message: str,
        agent_type: AgentType,
    ) -> list[ToolSuggestion]:
        """Check if player wants to rest."""
        # Only relevant for narrative agent
        if agent_type != AgentType.NARRATIVE:
            return []

        message_lower = user_message.lower()
        suggestions = []

        # Check for short rest
        for pattern in self.SHORT_REST_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                suggestions.append(
                    ToolSuggestion(
                        tool_name="short_rest",
                        reason="Player wants to take a short rest",
                        confidence=0.85,
                    )
                )
                break

        # Check for long rest
        for pattern in self.LONG_REST_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                suggestions.append(
                    ToolSuggestion(
                        tool_name="long_rest",
                        reason="Player wants to take a long rest",
                        confidence=0.85,
                    )
                )
                break

        return suggestions


# Registry of all heuristic rules
ALL_RULES: list[HeuristicRule] = [
    QuestAcceptanceRule(),
    ItemTransferRule(),
    CombatEndRule(),
    NextTurnRule(),
    DamageApplicationRule(),
    LocationChangeRule(),
    RestRule(),
]
```

**File:** `app/services/ai/tool_suggestion/__init__.py` (NEW)
```python
"""Tool suggestion services."""

from app.services.ai.tool_suggestion.heuristic_rules import ALL_RULES, HeuristicRule
from app.services.ai.tool_suggestion.tool_suggestion_service import ToolSuggestionService

__all__ = ["HeuristicRule", "ALL_RULES", "ToolSuggestionService"]
```

### 1.4 Create Tool Suggestion Service

**File:** `app/services/ai/tool_suggestion/tool_suggestion_service.py` (NEW)
```python
"""Service for generating tool suggestions using heuristic rules."""

import logging

from app.agents.core.types import AgentType
from app.models.game_state import GameState
from app.models.tool_suggestion import ToolSuggestions
from app.services.ai.tool_suggestion.heuristic_rules import ALL_RULES, HeuristicRule

logger = logging.getLogger(__name__)


class ToolSuggestionService:
    """Service for generating tool suggestions."""

    def __init__(self, rules: list[HeuristicRule] | None = None) -> None:
        """
        Initialize the service.

        Args:
            rules: List of heuristic rules to use. If None, uses ALL_RULES.
        """
        self.rules = rules or ALL_RULES

    async def suggest_tools(
        self,
        game_state: GameState,
        user_message: str,
        agent_type: AgentType,
    ) -> ToolSuggestions:
        """
        Generate tool suggestions based on heuristic rules.

        Args:
            game_state: Current game state
            user_message: User's input message
            agent_type: Type of agent that will execute

        Returns:
            ToolSuggestions with recommended tools
        """
        all_suggestions = []
        context_notes = []

        # Evaluate all rules
        for rule in self.rules:
            try:
                suggestions = rule.evaluate(game_state, user_message, agent_type)
                all_suggestions.extend(suggestions)
            except Exception as e:
                # Log but don't fail - suggestions are advisory only
                logger.warning(
                    f"Heuristic rule {rule.__class__.__name__} failed: {e}",
                    exc_info=True,
                )

        # Add context notes based on game state
        if game_state.combat.is_active and agent_type == AgentType.COMBAT:
            context_notes.append(
                f"Combat is active. Current turn: {game_state.combat.current_turn_entity_id}"
            )

        if agent_type == AgentType.NPC:
            # Add note about NPC capabilities
            context_notes.append(
                "As an NPC, you can use quest, inventory, and location tools."
            )

        # Deduplicate suggestions by tool_name (keep highest confidence)
        unique_suggestions = {}
        for suggestion in all_suggestions:
            existing = unique_suggestions.get(suggestion.tool_name)
            if existing is None or suggestion.confidence > existing.confidence:
                unique_suggestions[suggestion.tool_name] = suggestion

        # Sort by confidence (highest first)
        sorted_suggestions = sorted(
            unique_suggestions.values(),
            key=lambda s: s.confidence,
            reverse=True,
        )

        return ToolSuggestions(
            suggestions=sorted_suggestions,
            context_notes=context_notes,
        )
```

---

## Phase 2: Agent Implementation (Days 4-5)

### 2.1 Create ToolSuggestorAgent

**File:** `app/agents/tool_suggestor/__init__.py` (NEW)
```python
"""Tool suggestor agent."""

from app.agents.tool_suggestor.agent import ToolSuggestorAgent

__all__ = ["ToolSuggestorAgent"]
```

**File:** `app/agents/tool_suggestor/agent.py` (NEW)
```python
"""Agent for suggesting tools based on context."""

import logging

from app.agents.core.base import BaseAgent
from app.agents.core.dependencies import AgentDependencies
from app.agents.core.types import AgentType
from app.models.game_state import GameState
from app.models.tool_suggestion import ToolSuggestions
from app.services.ai.tool_suggestion.tool_suggestion_service import ToolSuggestionService

logger = logging.getLogger(__name__)


class ToolSuggestorAgent(BaseAgent):
    """
    Agent that suggests tools based on heuristic analysis.

    This agent does not use LLM calls - it's a lightweight rule-based system.
    Future versions may incorporate LLM-based analysis if needed.
    """

    def __init__(
        self,
        suggestion_service: ToolSuggestionService,
    ) -> None:
        """
        Initialize the agent.

        Args:
            suggestion_service: Service for generating suggestions
        """
        super().__init__()
        self.suggestion_service = suggestion_service

    async def suggest_tools_for_agent(
        self,
        game_state: GameState,
        user_message: str,
        target_agent_type: AgentType,
    ) -> ToolSuggestions:
        """
        Generate tool suggestions for another agent.

        Args:
            game_state: Current game state
            user_message: User's input message
            target_agent_type: Type of agent that will execute

        Returns:
            ToolSuggestions for the target agent
        """
        logger.debug(
            f"Generating tool suggestions for {target_agent_type.value} agent"
        )

        suggestions = await self.suggestion_service.suggest_tools(
            game_state=game_state,
            user_message=user_message,
            agent_type=target_agent_type,
        )

        if suggestions.suggestions:
            tool_names = [s.tool_name for s in suggestions.suggestions]
            logger.info(
                f"Suggested {len(tool_names)} tools for {target_agent_type.value}: {tool_names}"
            )
        else:
            logger.debug(f"No tool suggestions for {target_agent_type.value}")

        return suggestions
```

### 2.2 Update Agent Factory

**File:** `app/agents/factory.py`

Add ToolSuggestorAgent creation:

```python
from app.agents.tool_suggestor import ToolSuggestorAgent
from app.services.ai.tool_suggestion import ToolSuggestionService

class AgentFactory:
    # ... existing code ...

    def __init__(
        self,
        # ... existing params ...
        tool_suggestion_service: ToolSuggestionService,  # NEW
    ) -> None:
        # ... existing assignments ...
        self.tool_suggestion_service = tool_suggestion_service

        # Create tool suggestor agent (stateless, single instance)
        self._tool_suggestor_agent = ToolSuggestorAgent(
            suggestion_service=tool_suggestion_service,
        )

    def get_tool_suggestor_agent(self) -> ToolSuggestorAgent:
        """Get the tool suggestor agent."""
        return self._tool_suggestor_agent
```

### 2.3 Update Container

**File:** `app/container.py`

Register ToolSuggestionService:

```python
from app.services.ai.tool_suggestion import ToolSuggestionService

class Container:
    # ... existing code ...

    def __init__(self) -> None:
        # ... existing initialization ...

        # Tool suggestion service (NEW)
        self._tool_suggestion_service = ToolSuggestionService()

    @property
    def tool_suggestion_service(self) -> ToolSuggestionService:
        """Get the tool suggestion service."""
        return self._tool_suggestion_service

    # Update agent_factory property to include tool_suggestion_service
    @property
    def agent_factory(self) -> AgentFactory:
        """Get the agent factory."""
        if self._agent_factory is None:
            self._agent_factory = AgentFactory(
                # ... existing params ...
                tool_suggestion_service=self.tool_suggestion_service,  # NEW
            )
        return self._agent_factory
```

---

## Phase 3: Integration with Orchestrator (Day 6)

### 3.1 Update Context Builders

**File:** `app/services/ai/context_builders/base_context_builder.py`

Add method to include tool suggestions:

```python
from app.models.tool_suggestion import ToolSuggestions

class BaseContextBuilder:
    # ... existing code ...

    def with_tool_suggestions(self, suggestions: ToolSuggestions) -> str:
        """
        Build context section with tool suggestions.

        Args:
            suggestions: Tool suggestions to include

        Returns:
            Formatted suggestions section
        """
        return suggestions.format_for_prompt()
```

### 3.2 Update Orchestrator Service

**File:** `app/services/ai/orchestrator_service.py`

Integrate ToolSuggestorAgent into the flow:

```python
class OrchestratorService:
    # ... existing code ...

    async def _build_context_with_suggestions(
        self,
        game_state: GameState,
        user_message: str,
        agent_type: AgentType,
    ) -> str:
        """
        Build context including tool suggestions.

        Args:
            game_state: Current game state
            user_message: User's input
            agent_type: Type of agent that will execute

        Returns:
            Context string with suggestions appended
        """
        # Build base context
        base_context = await self.context_service.build_context_for_agent(
            game_state=game_state,
            agent_type=agent_type,
        )

        # Get tool suggestions
        tool_suggestor = self.agent_factory.get_tool_suggestor_agent()
        suggestions = await tool_suggestor.suggest_tools_for_agent(
            game_state=game_state,
            user_message=user_message,
            target_agent_type=agent_type,
        )

        # Append suggestions if any
        if suggestions.suggestions or suggestions.context_notes:
            suggestions_text = suggestions.format_for_prompt()
            return f"{base_context}\n\n{suggestions_text}"

        return base_context

    async def process_turn(
        self,
        user_message: str,
        game_state: GameState,
        stream: bool = True,
    ) -> AsyncIterator[dict[str, Any]]:
        """Process a turn with tool suggestions."""
        # Determine agent type
        agent_type = self._determine_agent_type(game_state, user_message)

        # Build context WITH suggestions
        context = await self._build_context_with_suggestions(
            game_state=game_state,
            user_message=user_message,
            agent_type=agent_type,
        )

        # Get appropriate agent
        agent = self._get_agent_for_type(agent_type)

        # Process with agent (pass context through dependencies)
        # ... rest of existing flow ...
```

**Note:** The exact integration point depends on how context is currently passed to agents. We'll need to modify either:
- The `prepare_for_*` methods to accept additional context, OR
- The context builders to automatically fetch suggestions

**Preferred approach:** Modify context builders to automatically include suggestions:

```python
# In ContextService
async def build_context_for_agent(
    self,
    game_state: GameState,
    agent_type: AgentType,
    user_message: str = "",  # NEW parameter
) -> str:
    """Build context including tool suggestions."""
    # Build base context via builders
    base_context = self._build_base_context(game_state, agent_type)

    # Get tool suggestions if user message provided
    if user_message:
        tool_suggestor = self.agent_factory.get_tool_suggestor_agent()
        suggestions = await tool_suggestor.suggest_tools_for_agent(
            game_state=game_state,
            user_message=user_message,
            target_agent_type=agent_type,
        )

        if suggestions.suggestions or suggestions.context_notes:
            suggestions_text = suggestions.format_for_prompt()
            return f"{base_context}\n\n{suggestions_text}"

    return base_context
```

---

## Phase 4: System Prompt Improvements (Day 7)

### 4.1 Enhance NPC System Prompts

**File:** `app/agents/core/prompts.py`

Update `NPC_SYSTEM_PROMPT`:

```python
NPC_SYSTEM_PROMPT = """You are role-playing a single non-player character (NPC) in a Dungeons & Dragons 5th Edition campaign.

## Your Role
- Stay strictly in character for the NPC described in the persona context.
- Speak in first-person as that NPC ("I", "me").
- Keep responses concise (1-3 paragraphs unless otherwise requested).
- Reveal information only if the NPC reasonably knows it.
- Ask clarifying questions when the player's intent is ambiguous.

## Table Stakes
- Maintain continuity with the NPC's memories, goals, relationships, and current attitude.
- Reference recent events from the conversation history and memories when relevant.
- Never narrate the player's actions or internal thoughts.
- Avoid advancing the global narrative; focus on this NPC's perspective.

## Tool Usage - IMPORTANT
You have access to tools that affect the game world. Use them when your NPC takes concrete actions:

### Quest Tools
- **start_quest**: When you assign a quest to the player
  - Example: "I need you to retrieve the stolen amulet from the bandits. Will you help?"
  - Action: Call start_quest with quest details
- **complete_objective**: When the player fulfills a quest step
  - Example: Player shows you the retrieved amulet
  - Action: Call complete_objective for that quest step
- **complete_quest**: When all objectives are done and you give the reward
  - Example: "You've done well! Here's your reward."
  - Action: Call complete_quest AND modify_inventory for the reward

### Inventory Tools
- **modify_inventory**: When you give/take items or currency to/from the player
  - Example: "Here, take this healing potion" → Call modify_inventory
  - Example: "That'll be 50 gold pieces" → Call modify_inventory with negative gold
  - ALWAYS use this when you say you're giving or receiving items/gold

### Location Tools
- **update_location_state**: When you cause environmental changes
  - Example: You unlock a door, reveal a mechanism, change the environment
- **discover_secret**: When you reveal hidden information about the location
  - Example: "Behind this tapestry is a secret passage"
- **move_npc_to_location**: When you move to a different location
  - Example: "I'm heading to the tavern now"

## Tool Usage Examples

### Example 1: Giving a Quest
```
Player: "Is there anything I can help with?"
You: "Actually, yes. The bandits have stolen a precious amulet from our temple. If you can retrieve it, I'll reward you handsomely."
[Call start_quest with name="Retrieve the Stolen Amulet", description="...", objectives=[...]]
```

### Example 2: Giving an Item
```
Player: "Do you have anything that could help me?"
You: "Take this potion. It's not much, but it might save your life."
[Call modify_inventory with item_type="consumable", item_id="healing-potion-common", quantity=1]
```

### Example 3: Completing a Quest
```
Player: [shows you the retrieved amulet]
You: "You found it! You have my eternal gratitude. Here's your reward as promised."
[Call complete_quest with quest_id="...", reason="Player returned the amulet"]
[Call modify_inventory with currency_type="gp", quantity=100]
```

### Example 4: Just Talking (No Tools Needed)
```
Player: "What do you think of the local lord?"
You: "He's a fair man, but the taxes have been heavy this year. Still, better him than the bandits running things."
[No tools called - just conversation]
```

## Tool Guidelines
- **When to use**: When your NPC takes a concrete action that changes the game state
- **When NOT to use**: When just talking, describing, or giving information
- **Multiple tools**: You can call multiple tools in one response if the action requires it
- **Tool suggestions**: If tool suggestions appear in the context, consider them carefully but use your judgment
- Never call combat tools or start combat; escalate to the DM instead

Remember: Use tools naturally as part of your NPC's actions. The game world updates based on your tool calls."""
```

Update `PUPPETEER_SYSTEM_PROMPT` similarly with examples.

### 4.2 Add Tool Suggestion Section to Narrative Prompt

**File:** `app/agents/core/prompts.py`

Add section to `NARRATIVE_SYSTEM_PROMPT`:

```python
## Tool Suggestions
If tool suggestions appear below, they are advisory hints based on the current context. Review them carefully and use your judgment to decide which tools are appropriate for the situation. The suggestions are meant to help, not constrain your decisions.
```

Add similar section to `COMBAT_SYSTEM_PROMPT`.

---

## Phase 5: Party-Aware Context Sharing (Day 8)

### 5.1 Update Message Converter Service

**File:** `app/services/ai/message_converter_service.py`

```python
class MessageConverterService:
    """Service for converting between message formats."""

    @staticmethod
    def to_pydantic_messages(
        messages: list[Message],
        agent_type: AgentType,
        npc_id: str | None = None,  # NEW parameter
        game_state: GameState | None = None,  # NEW parameter
    ) -> list[ModelMessage]:
        """
        Convert internal Message format to PydanticAI's ModelMessage format.

        Args:
            messages: List of messages to convert
            agent_type: Agent type requesting messages
            npc_id: If agent_type is NPC, the ID of the NPC
            game_state: Current game state (for party membership checks)

        Returns:
            List of ModelMessage objects for PydanticAI
        """
        pydantic_messages: list[ModelMessage] = []

        allowed_agent_types = {agent_type}

        if agent_type is AgentType.NARRATIVE:
            # Narrative agent needs to hear NPC conversations
            allowed_agent_types.add(AgentType.NPC)
        elif agent_type is AgentType.NPC:
            # NEW: If NPC is in party, allow them to see narrative messages
            if game_state is not None and npc_id is not None:
                if npc_id in game_state.party.member_ids:
                    allowed_agent_types.add(AgentType.NARRATIVE)
                    logger.debug(f"NPC {npc_id} is in party - including narrative messages")

        for msg in messages:
            if msg.agent_type not in allowed_agent_types:
                continue

            # ... rest of existing conversion logic ...

        return pydantic_messages
```

### 5.2 Update NPC Agent Base

**File:** `app/agents/npc/base.py`

Update the `_build_message_history` call to pass NPC ID and game state:

```python
async def process(
    self,
    player_message: str,
    game_state: GameState,
    stream: bool = True,
) -> AsyncIterator[dict[str, Any]]:
    """Process NPC dialogue with party-aware context."""
    # ... existing code ...

    # Build message history with NPC ID and game state
    message_history = message_converter.to_pydantic_messages(
        messages=recent_messages,
        agent_type=AgentType.NPC,
        npc_id=self._current_npc_id,  # NEW
        game_state=game_state,  # NEW
    )

    # ... rest of existing code ...
```

---

## Phase 6: Model Configuration Update (Day 9)

### 6.1 Update PuppeteerAgent Model

**File:** `app/agents/npc/puppeteer_agent.py`

```python
def __init__(
    self,
    # ... existing params ...
) -> None:
    """Initialize puppeteer agent."""
    super().__init__(
        # ... existing params ...
    )

    # Initialize pydantic-ai agent with larger model
    self._agent = Agent(
        model=self.model_name,  # Now uses PUPPETEER_NPC_MODEL (120B)
        system_prompt=PUPPETEER_SYSTEM_PROMPT,
        tools=self.get_required_tools(),
        deps_type=AgentDependencies,
    )

    # Configure with lower temperature for consistency
    self._agent.model_settings = {
        "max_tokens": 2048,
        "temperature": 0.7,  # Changed from 0.8 to 0.7
        "reasoning_effort": "medium",
    }
```

### 6.2 Update Config

**File:** `app/config.py`

Update default for `PUPPETEER_NPC_MODEL`:

```python
class Config(BaseSettings):
    # ... existing fields ...

    PUPPETEER_NPC_MODEL: str = Field(
        default="openrouter/meta-llama/llama-3.3-120b-instruct",  # Changed from 20B
        description="Model for puppeteer NPC agent (minor NPCs)",
    )
```

**File:** `.env.example`

```bash
# Update example
PUPPETEER_NPC_MODEL=openrouter/meta-llama/llama-3.3-120b-instruct
```

---

## Phase 7: Testing & Validation (Days 10-12)

### 7.1 Unit Tests

**File:** `tests/unit/services/ai/tool_suggestion/test_heuristic_rules.py` (NEW)

```python
"""Tests for heuristic rules."""

import pytest

from app.agents.core.types import AgentType
from app.models.game_state import GameState
from app.services.ai.tool_suggestion.heuristic_rules import (
    CombatEndRule,
    ItemTransferRule,
    QuestAcceptanceRule,
)
from tests.factories.game_state_factory import GameStateFactory


class TestQuestAcceptanceRule:
    """Tests for QuestAcceptanceRule."""

    def test_accept_quest_pattern(self) -> None:
        """Test that 'accept quest' triggers suggestion."""
        rule = QuestAcceptanceRule()
        game_state = GameStateFactory.create()

        suggestions = rule.evaluate(
            game_state=game_state,
            user_message="I'll accept the quest",
            agent_type=AgentType.NARRATIVE,
        )

        assert len(suggestions) == 1
        assert suggestions[0].tool_name == "start_quest"
        assert suggestions[0].confidence >= 0.6

    def test_no_quest_pattern(self) -> None:
        """Test that unrelated messages don't trigger suggestion."""
        rule = QuestAcceptanceRule()
        game_state = GameStateFactory.create()

        suggestions = rule.evaluate(
            game_state=game_state,
            user_message="What's the weather like?",
            agent_type=AgentType.NARRATIVE,
        )

        assert len(suggestions) == 0


class TestItemTransferRule:
    """Tests for ItemTransferRule."""

    def test_npc_giving_item(self) -> None:
        """Test NPC giving item to player."""
        rule = ItemTransferRule()
        game_state = GameStateFactory.create()

        suggestions = rule.evaluate(
            game_state=game_state,
            user_message="Here's a healing potion for you",
            agent_type=AgentType.NPC,
        )

        assert len(suggestions) == 1
        assert suggestions[0].tool_name == "modify_inventory"


class TestCombatEndRule:
    """Tests for CombatEndRule."""

    def test_all_enemies_defeated(self) -> None:
        """Test suggestion when all enemies defeated."""
        rule = CombatEndRule()
        game_state = GameStateFactory.create_with_combat(all_enemies_defeated=True)

        suggestions = rule.evaluate(
            game_state=game_state,
            user_message="I attack",
            agent_type=AgentType.COMBAT,
        )

        assert len(suggestions) == 1
        assert suggestions[0].tool_name == "end_combat"
        assert suggestions[0].confidence >= 0.9
```

**File:** `tests/unit/services/ai/tool_suggestion/test_tool_suggestion_service.py` (NEW)

```python
"""Tests for ToolSuggestionService."""

import pytest

from app.agents.core.types import AgentType
from app.services.ai.tool_suggestion.tool_suggestion_service import ToolSuggestionService
from tests.factories.game_state_factory import GameStateFactory


@pytest.mark.asyncio
class TestToolSuggestionService:
    """Tests for ToolSuggestionService."""

    async def test_suggest_tools_quest(self) -> None:
        """Test quest-related suggestions."""
        service = ToolSuggestionService()
        game_state = GameStateFactory.create()

        suggestions = await service.suggest_tools(
            game_state=game_state,
            user_message="I accept your quest",
            agent_type=AgentType.NARRATIVE,
        )

        assert len(suggestions.suggestions) > 0
        assert any(s.tool_name == "start_quest" for s in suggestions.suggestions)

    async def test_format_for_prompt(self) -> None:
        """Test prompt formatting."""
        service = ToolSuggestionService()
        game_state = GameStateFactory.create()

        suggestions = await service.suggest_tools(
            game_state=game_state,
            user_message="I'll take the quest",
            agent_type=AgentType.NARRATIVE,
        )

        formatted = suggestions.format_for_prompt()
        assert "## Suggested Tools" in formatted
        assert "start_quest" in formatted
```

**File:** `tests/unit/agents/test_tool_suggestor_agent.py` (NEW)

```python
"""Tests for ToolSuggestorAgent."""

import pytest

from app.agents.core.types import AgentType
from app.agents.tool_suggestor.agent import ToolSuggestorAgent
from app.services.ai.tool_suggestion.tool_suggestion_service import ToolSuggestionService
from tests.factories.game_state_factory import GameStateFactory


@pytest.mark.asyncio
class TestToolSuggestorAgent:
    """Tests for ToolSuggestorAgent."""

    async def test_suggest_tools_for_agent(self) -> None:
        """Test agent suggests tools for target agent."""
        service = ToolSuggestionService()
        agent = ToolSuggestorAgent(suggestion_service=service)
        game_state = GameStateFactory.create()

        suggestions = await agent.suggest_tools_for_agent(
            game_state=game_state,
            user_message="I accept the quest",
            target_agent_type=AgentType.NARRATIVE,
        )

        assert suggestions is not None
        assert isinstance(suggestions.suggestions, list)
```

### 7.2 Integration Tests

**File:** `tests/integration/test_tool_suggestions_flow.py` (NEW)

```python
"""Integration tests for tool suggestion flow."""

import pytest

from app.agents.core.types import AgentType
from app.container import Container
from tests.factories.game_state_factory import GameStateFactory


@pytest.mark.asyncio
class TestToolSuggestionsFlow:
    """Test complete flow with tool suggestions."""

    async def test_narrative_agent_with_suggestions(self, container: Container) -> None:
        """Test narrative agent receives and processes suggestions."""
        game_state = GameStateFactory.create()
        orchestrator = container.orchestrator_service

        # User accepts quest
        user_message = "I'll help you with that quest"

        # Process through orchestrator (should include suggestions)
        events = []
        async for event in orchestrator.process_turn(
            user_message=user_message,
            game_state=game_state,
            stream=True,
        ):
            events.append(event)

        # Verify suggestions were generated (check logs or events)
        # Verify agent had access to suggestions in context
        # This requires inspecting debug logs or adding telemetry

        assert len(events) > 0

    async def test_npc_agent_with_suggestions(self, container: Container) -> None:
        """Test NPC agent receives suggestions."""
        game_state = GameStateFactory.create()
        orchestrator = container.orchestrator_service

        # User talks to NPC about quest
        user_message = "@merchant Can I buy that sword?"

        events = []
        async for event in orchestrator.process_turn(
            user_message=user_message,
            game_state=game_state,
            stream=True,
        ):
            events.append(event)

        # Verify modify_inventory suggestion was made
        assert len(events) > 0
```

### 7.3 Manual Testing Protocol

Create a test script for manual validation:

**File:** `scripts/test_tool_suggestions.py` (NEW)

```python
"""Manual testing script for tool suggestions."""

import asyncio

from app.agents.core.types import AgentType
from app.container import Container
from app.services.game.game_service import GameService


async def test_suggestions() -> None:
    """Test tool suggestions with various scenarios."""
    container = Container()
    game_service = container.game_service

    # Create test game
    game_state = await game_service.create_new_game(
        character_id="aldric-swiftarrow",
        scenario_id="shadows-of-evermist",
    )

    # Test scenarios
    test_cases = [
        ("I accept the quest", AgentType.NARRATIVE),
        ("I take the healing potion", AgentType.NARRATIVE),
        ("@merchant Here's 50 gold for the sword", AgentType.NPC),
        ("I attack the goblin", AgentType.COMBAT),
        ("I want to rest for the night", AgentType.NARRATIVE),
    ]

    tool_suggestor = container.agent_factory.get_tool_suggestor_agent()

    for message, agent_type in test_cases:
        print(f"\n{'='*60}")
        print(f"Message: {message}")
        print(f"Agent: {agent_type.value}")
        print(f"{'='*60}")

        suggestions = await tool_suggestor.suggest_tools_for_agent(
            game_state=game_state,
            user_message=message,
            target_agent_type=agent_type,
        )

        if suggestions.suggestions:
            print("\nSuggestions:")
            for suggestion in suggestions.suggestions:
                print(f"  - {suggestion.tool_name} (confidence: {suggestion.confidence:.2f})")
                print(f"    Reason: {suggestion.reason}")
        else:
            print("\nNo suggestions")

        if suggestions.context_notes:
            print("\nContext Notes:")
            for note in suggestions.context_notes:
                print(f"  - {note}")


if __name__ == "__main__":
    asyncio.run(test_suggestions())
```

Run with:
```bash
python scripts/test_tool_suggestions.py
```

---

## Phase 8: Monitoring & Debugging (Days 13-14)

### 8.1 Add Telemetry

**File:** `app/services/ai/tool_suggestion/tool_suggestion_service.py`

Add telemetry tracking:

```python
class ToolSuggestionService:
    """Service for generating tool suggestions."""

    def __init__(self, rules: list[HeuristicRule] | None = None) -> None:
        self.rules = rules or ALL_RULES
        self._telemetry: dict[str, int] = {}  # Track suggestion counts

    async def suggest_tools(
        self,
        game_state: GameState,
        user_message: str,
        agent_type: AgentType,
    ) -> ToolSuggestions:
        """Generate tool suggestions with telemetry."""
        # ... existing logic ...

        # Track telemetry
        for suggestion in sorted_suggestions:
            key = f"{agent_type.value}:{suggestion.tool_name}"
            self._telemetry[key] = self._telemetry.get(key, 0) + 1

        return ToolSuggestions(
            suggestions=sorted_suggestions,
            context_notes=context_notes,
        )

    def get_telemetry(self) -> dict[str, int]:
        """Get telemetry data."""
        return dict(self._telemetry)
```

### 8.2 Add Debug Logging

**File:** `app/services/ai/debug_logger.py`

Add tool suggestion logging:

```python
class DebugLogger:
    """Logger for agent debugging."""

    def log_tool_suggestions(
        self,
        game_id: str,
        agent_type: AgentType,
        suggestions: ToolSuggestions,
        user_message: str,
    ) -> None:
        """Log tool suggestions for debugging."""
        if not self.enabled:
            return

        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "type": "tool_suggestions",
            "agent_type": agent_type.value,
            "user_message": user_message,
            "suggestions": [
                {
                    "tool": s.tool_name,
                    "confidence": s.confidence,
                    "reason": s.reason,
                }
                for s in suggestions.suggestions
            ],
            "context_notes": suggestions.context_notes,
        }

        self._write_log(game_id, "tool_suggestions", log_entry)
```

### 8.3 Create Analysis Tool

**File:** `scripts/analyze_tool_suggestions.py` (NEW)

```python
"""Analyze tool suggestion effectiveness from logs."""

import json
from collections import defaultdict
from pathlib import Path


def analyze_suggestions(logs_dir: Path) -> None:
    """Analyze tool suggestion logs."""
    stats = {
        "suggestions_made": 0,
        "tools_suggested": defaultdict(int),
        "by_agent_type": defaultdict(int),
        "high_confidence": 0,
        "medium_confidence": 0,
        "low_confidence": 0,
    }

    for log_file in logs_dir.glob("*tool_suggestions.jsonl"):
        with log_file.open() as f:
            for line in f:
                entry = json.loads(line)

                if entry.get("type") != "tool_suggestions":
                    continue

                stats["suggestions_made"] += 1
                stats["by_agent_type"][entry["agent_type"]] += 1

                for suggestion in entry.get("suggestions", []):
                    tool = suggestion["tool"]
                    confidence = suggestion["confidence"]

                    stats["tools_suggested"][tool] += 1

                    if confidence >= 0.8:
                        stats["high_confidence"] += 1
                    elif confidence >= 0.5:
                        stats["medium_confidence"] += 1
                    else:
                        stats["low_confidence"] += 1

    # Print report
    print("Tool Suggestion Analysis")
    print("=" * 60)
    print(f"Total suggestions made: {stats['suggestions_made']}")
    print(f"\nBy agent type:")
    for agent_type, count in stats["by_agent_type"].items():
        print(f"  {agent_type}: {count}")

    print(f"\nMost suggested tools:")
    for tool, count in sorted(
        stats["tools_suggested"].items(),
        key=lambda x: x[1],
        reverse=True,
    )[:10]:
        print(f"  {tool}: {count}")

    print(f"\nConfidence distribution:")
    print(f"  High (≥0.8): {stats['high_confidence']}")
    print(f"  Medium (0.5-0.8): {stats['medium_confidence']}")
    print(f"  Low (<0.5): {stats['low_confidence']}")


if __name__ == "__main__":
    analyze_suggestions(Path("logs"))
```

---

## Success Metrics

### Quantitative Metrics

1. **Tool Call Coverage**
   - Before: % of interactions where expected tool was called
   - After: Should increase by 30-50%
   - Measure: Parse game event logs for tool calls vs. message patterns

2. **Tool Call Errors**
   - Before: Count of ToolErrorResult returns
   - After: Should decrease by 40-60%
   - Measure: Count error results in logs

3. **Suggestion Accuracy**
   - % of suggestions actually used by agents
   - Target: ≥60% of high-confidence suggestions used
   - Measure: Compare suggestions logged vs. tools called

4. **Latency Impact**
   - Overhead of heuristic evaluation
   - Target: <10ms per request
   - Measure: Time the suggest_tools() call

### Qualitative Metrics

1. **User Experience**
   - NPCs consistently handle item transfers
   - Quests properly initiated and completed
   - Combat flow smoother (next_turn, end_combat)

2. **Code Quality**
   - Heuristic rules are easy to add/modify
   - System is testable and observable
   - Follows SOLID principles

### Monitoring Dashboard (Future)

Create endpoint to expose metrics:

**File:** `app/api/routers/debug.py`

```python
@router.get("/tool-suggestions/stats")
async def get_tool_suggestion_stats(
    container: Container = Depends(get_container),
) -> dict[str, Any]:
    """Get tool suggestion statistics."""
    service = container.tool_suggestion_service

    return {
        "telemetry": service.get_telemetry(),
        "rules_count": len(service.rules),
        "rules": [rule.__class__.__name__ for rule in service.rules],
    }
```

---

## Rollout Strategy

### Phase 0: Pre-Launch (Day 15)

1. **Code Review**
   - Review all changes with team
   - Verify type safety (run mypy)
   - Run full test suite
   - Update documentation

2. **Staging Deployment**
   - Deploy to staging environment
   - Enable DEBUG_AGENT_CONTEXT=true
   - Run manual test scenarios

### Phase 1: Soft Launch (Days 16-20)

1. **Feature Flag** (Optional)
   - Add `ENABLE_TOOL_SUGGESTIONS` config flag
   - Default: true
   - Allows quick rollback if issues

2. **Monitor Metrics**
   - Watch error rates
   - Check latency impact
   - Review debug logs daily

3. **Collect Feedback**
   - Note edge cases where suggestions wrong
   - Track patterns of missed tools

### Phase 2: Tuning (Days 21-30)

1. **Refine Heuristics**
   - Add new rules based on observations
   - Adjust confidence thresholds
   - Improve pattern matching

2. **Optimize Prompts**
   - Refine based on agent behavior
   - Add more examples if needed
   - Clarify ambiguous instructions

### Phase 3: LLM Upgrade (If Needed)

If heuristics plateau at <70% effectiveness:

1. **Implement LLM-Based Suggester**
   - Replace heuristic service with LLM call
   - Use lightweight model (haiku/gpt-4o-mini)
   - Keep heuristics as fallback

**File:** `app/services/ai/tool_suggestion/llm_suggestion_service.py` (FUTURE)

```python
class LLMToolSuggestionService:
    """LLM-based tool suggestion service."""

    async def suggest_tools(
        self,
        game_state: GameState,
        user_message: str,
        agent_type: AgentType,
    ) -> ToolSuggestions:
        """Use LLM to suggest tools."""
        # Build prompt
        prompt = self._build_suggestion_prompt(game_state, user_message, agent_type)

        # Call lightweight model
        response = await self.model.call(prompt)

        # Parse structured output
        suggestions = self._parse_suggestions(response)

        return suggestions
```

---

## Risks & Mitigations

### Risk 1: Suggestion Overhead

**Risk:** Heuristic evaluation adds latency
**Mitigation:**
- Heuristics are O(n) with small n (<10 rules)
- Target <10ms overhead (negligible vs. LLM call)
- Can parallelize rule evaluation if needed
- Can cache suggestions for identical inputs

### Risk 2: Suggestion Accuracy

**Risk:** Heuristics suggest wrong tools
**Mitigation:**
- Suggestions are advisory, not mandatory
- Agents retain full autonomy
- Can tune confidence thresholds
- Fallback to LLM-based if needed

### Risk 3: Context Sharing Info Leak

**Risk:** Party NPCs see information they shouldn't
**Mitigation:**
- Only affects NPCs in party (by design)
- D&D assumption: party shares knowledge
- Can add "memory since join" filter if needed
- Alternative: summarize narrative for NPCs

### Risk 4: Prompt Bloat

**Risk:** Tool suggestions add too much to prompts
**Mitigation:**
- Suggestions only added if non-empty
- Format is concise (~5-10 lines per suggestion)
- Can limit to top N suggestions (e.g., top 3)
- Can skip suggestions for very long contexts

### Risk 5: Model Cost Increase

**Risk:** Upgrading PuppeteerAgent to 120B increases costs
**Mitigation:**
- 120B model is marginal cost vs. quality improvement
- Can revert if costs too high
- Can use 70B as middle ground
- Can keep 20B for truly minor NPCs (guards, shopkeepers)

---

## Future Enhancements

### Post-Flight Verifier (Phase 4)

Add optional post-flight verification for critical patterns:

**File:** `app/services/ai/tool_verification/verifier_service.py` (FUTURE)

```python
class ToolVerificationService:
    """Post-flight tool verification."""

    def verify_critical_tools(
        self,
        agent_response: str,
        tools_called: list[str],
    ) -> list[str]:
        """
        Check if critical tools were called.

        Returns:
            List of missing critical tools
        """
        missing = []

        # Pattern: "I give you X" but no modify_inventory
        if re.search(r"\b(give|hand|offer) you\b", agent_response, re.I):
            if "modify_inventory" not in tools_called:
                missing.append("modify_inventory")

        # Pattern: "Here's a quest" but no start_quest
        if re.search(r"\bquest\b", agent_response, re.I):
            if "start_quest" not in tools_called:
                missing.append("start_quest")

        return missing
```

### Dynamic Rule Learning (Phase 5)

Learn patterns from successful interactions:

**File:** `app/services/ai/tool_suggestion/learning_service.py` (FUTURE)

```python
class RuleLearningService:
    """Learn new heuristic patterns from successful interactions."""

    def analyze_interaction(
        self,
        user_message: str,
        tools_called: list[str],
        agent_type: AgentType,
    ) -> None:
        """Record successful interaction for pattern learning."""
        # Track: message pattern -> tools called
        # Periodically analyze to suggest new rules
        ...
```

### Multi-Agent Collaboration (Phase 6)

ToolSuggestorAgent could coordinate with other advisory agents:

- **RulesArbiterAgent**: For D&D rules clarifications
- **DirectorAgent**: For pacing suggestions
- Combined suggestions for optimal agent performance

---

## Documentation Updates

### Update CLAUDE.md

Add section:

```markdown
## Tool Usage Verification

The system includes a **ToolSuggestorAgent** that provides advisory tool suggestions to all agents before execution. This improves consistency in tool calling across Narrative, Combat, and NPC agents.

### How It Works
1. User input analyzed by heuristic rules
2. Suggestions added to agent context (advisory only)
3. Agent decides which tools to use
4. System monitors effectiveness via telemetry

### Adding Heuristic Rules
Create a new rule class in `app/services/ai/tool_suggestion/heuristic_rules.py`:

```python
class MyCustomRule(HeuristicRule):
    def evaluate(self, game_state, user_message, agent_type):
        # Pattern matching logic
        if some_pattern_matches:
            return [ToolSuggestion(...)]
        return []

# Add to ALL_RULES registry
```

### Update FUTURE-AGENTS.md

Mark ToolSuggestorAgent as implemented:

```markdown
## ToolSuggestorAgent (IMPLEMENTED)
- ✅ Phase 1: Heuristic-based suggestions
- Purpose: Improve tool calling consistency across all agents
- Integration: Pre-flight advisory system via OrchestratorService
- Status: Production (v2.0)
- Future: LLM-based suggestions if heuristics plateau
```

### Create New Doc

**File:** `docs/TOOL-SUGGESTIONS.md` (NEW)

Complete guide to the tool suggestion system with architecture diagrams, examples, and extension guide.

---

## Dependencies

### New Python Packages

None required - uses existing dependencies.

### Configuration Changes

**File:** `.env`

```bash
# Tool Suggestions (optional)
ENABLE_TOOL_SUGGESTIONS=true  # Feature flag
DEBUG_TOOL_SUGGESTIONS=false  # Extra logging

# Updated model
PUPPETEER_NPC_MODEL=openrouter/meta-llama/llama-3.3-120b-instruct
```

---

## Timeline Summary

| Phase | Days | Tasks | Deliverables |
|-------|------|-------|--------------|
| 1 | 1-3 | Core infrastructure | Models, interfaces, heuristic rules |
| 2 | 4-5 | Agent implementation | ToolSuggestorAgent, factory, container |
| 3 | 6 | Orchestrator integration | Context builders, flow integration |
| 4 | 7 | System prompts | Enhanced NPC/Narrative/Combat prompts |
| 5 | 8 | Context sharing | Party-aware message filtering |
| 6 | 9 | Model config | PuppeteerAgent model upgrade |
| 7 | 10-12 | Testing | Unit, integration, manual tests |
| 8 | 13-14 | Monitoring | Telemetry, debug tools, analysis |
| 9 | 15 | Pre-launch | Code review, staging deployment |
| 10 | 16-20 | Soft launch | Production monitoring, feedback |
| 11 | 21-30 | Tuning | Refine heuristics, optimize prompts |

**Total: ~30 days** (including testing and tuning)
**Minimum viable: ~10 days** (phases 1-6 only)

---

## Acceptance Criteria

### Must Have (MVP)

- ✅ ToolSuggestorAgent implemented with ≥5 heuristic rules
- ✅ Suggestions integrated into all agent types (Narrative, Combat, NPC)
- ✅ Party-aware context sharing for NPC agents
- ✅ Enhanced system prompts with tool usage examples
- ✅ PuppeteerAgent uses 120B model
- ✅ Unit tests covering all heuristic rules
- ✅ Integration tests for full flow
- ✅ Latency overhead <10ms
- ✅ Zero breaking changes to existing API

### Should Have (V1.1)

- ✅ Telemetry tracking for suggestion effectiveness
- ✅ Debug logging for tool suggestions
- ✅ Analysis script for suggestion patterns
- ✅ Manual testing protocol
- ✅ Documentation updates

### Nice to Have (V2.0)

- ⏳ Post-flight verification for critical tools
- ⏳ LLM-based suggester option
- ⏳ Learning system for dynamic rules
- ⏳ Monitoring dashboard endpoint

---

## Questions & Decisions Log

### Decided
1. ✅ ToolSuggestor = Agent (not service)
2. ✅ Heuristics in code (not config)
3. ✅ Suggestions are advisory
4. ✅ Party members see all narrative messages
5. ✅ Pre-flight approach (not post-flight)
6. ✅ Start with heuristics, upgrade to LLM if needed
7. ✅ PuppeteerAgent uses 120B model

### Open Questions
1. Should we add feature flag for gradual rollout?
2. Should we limit suggestions to top N (e.g., 3)?
3. Should we cache suggestions for identical inputs?
4. Should we add per-agent suggestion preferences?

---

## Conclusion

This plan provides a comprehensive, phased approach to improving tool usage consistency across all agents. The solution:

- ✅ Follows SOLID principles
- ✅ Maintains fail-fast behavior
- ✅ Preserves type safety
- ✅ Extends existing architecture
- ✅ Allows iterative improvement
- ✅ Minimizes breaking changes
- ✅ Provides observability

The heuristic-based approach offers quick wins with minimal complexity, while keeping the door open for LLM-based suggestions if needed. The system is fully testable, observable, and maintainable.

**Recommendation:** Proceed with Phase 1-6 (Days 1-9) for MVP, then iterate based on real-world performance.
