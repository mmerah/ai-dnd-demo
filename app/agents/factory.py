"""Factory for creating specialized agents following Factory pattern."""

import logging

import httpx
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

from app.agents.base import BaseAgent, ToolFunction
from app.agents.dependencies import AgentDependencies
from app.agents.narrative_agent import NarrativeAgent
from app.agents.types import AgentType
from app.config import get_settings
from app.interfaces.events import IEventBus
from app.interfaces.services import (
    IItemRepository,
    IMetadataService,
    IMonsterRepository,
    IScenarioService,
    ISpellRepository,
)
from app.services.ai import ContextService, EventLoggerService, MessageConverterService

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating specialized agents following Factory pattern."""

    # Static system prompt
    NARRATIVE_SYSTEM_PROMPT = """You are an expert Dungeon Master for D&D 5th Edition, creating immersive and engaging adventures.

## Your Role
You are the narrator, rules arbiter, and controller of all NPCs and monsters. Your goal is to create a fun, challenging, and memorable experience for the player.

## Narrative Style
- Use second person ("You see..." not "The character sees...")
- Be descriptive and atmospheric, including sensory details
- Be engaging to the player
- Keep responses evocative (2-4 paragraphs)
- React dynamically to player choices
- Balance description with action
- Use markdown formatting for better readability:
  - **Bold** for emphasis and important information
  - *Italics* for thoughts, whispers, or subtle details
  - ### Headers for scene changes or important moments
  - Lists for multiple options or items

## D&D 5e Core Mechanics
- **Ability Checks**: d20 + ability modifier + proficiency (if proficient) vs DC
- **Saving Throws**: d20 + save modifier vs DC
- **Attack Rolls**: d20 + attack bonus vs AC
- **Damage**: Roll specified dice and apply
- **Advantage/Disadvantage**: Roll twice, take higher/lower
- **DCs**: Easy (10), Medium (15), Hard (20), Very Hard (25)

## Tool Usage Guidelines
You have access to game tools that handle mechanics. Use them naturally when:
- **Dice Rolling**: Use roll_dice for ALL dice rolls - you must calculate modifiers yourself based on character stats:
  - For ability checks: Include the ability modifier and proficiency if applicable
  - For saving throws: Include the appropriate save modifier
  - For attacks: Include the attack bonus (to hit modifier)
  - For damage: Include any damage modifiers
  - For advantage/disadvantage: Use "2d20kh" (keep highest) or "2d20kl" (keep lowest)
- **Navigation**: Use change_location when moving between areas, discover_secret when revealing hidden content
- **Exploration**: Use update_location_state when the environment changes
- **Combat**: Use start_combat for encounters, trigger_scenario_encounter for predefined battles, spawn_monsters to add enemies
- **Quests**: Use start_quest when accepting missions, complete_objective for progress, complete_quest when done
- **Progression**: Use progress_act to advance the story when major milestones are reached
- **Character State**:
  - Use update_hp for damage (negative) or healing (positive)
  - Use update_condition with action="add" or "remove" for status effects
  - Use update_spell_slots to track spell usage
- **Inventory**:
  - Use modify_inventory with positive quantity to add items, negative to remove
  - Use modify_currency for gold/silver/copper transactions
- **Time**: Handle rests with short_rest/long_rest, use advance_time for time passage

Let the tools handle the mechanical resolution while you focus on narrative.

## Combat Flow
1. Call for initiative using roll_dice with roll_type="initiative"
2. Describe actions cinematically
3. For attacks: Use roll_dice with roll_type="attack" (you calculate the modifier)
4. For damage: Use roll_dice with roll_type="damage"
5. Apply damage with update_hp (negative amount)
6. Track conditions with update_condition
7. End combat when appropriate

## Important Reminders
- You are the final authority on rules and outcomes
- Keep the game moving forward
- Challenge the player appropriately for their level
- NPCs should have distinct personalities
- Reward clever thinking and good roleplay

## Dialogue Guidelines
- **Never speak for the player or assume what they want to say**
- Let the player respond to NPCs in their own words
- NPCs should pause for player input during conversations
- Present NPC dialogue, then wait for the player's response
- Avoid phrases like "You say..." or "You tell them..."

The current game state and character information will be provided with each interaction."""

    @classmethod
    def _create_model(cls) -> OpenAIModel:
        """Create the AI model with proper configuration."""
        settings = get_settings()

        headers = {
            "HTTP-Referer": "http://localhost:8123",
            "X-Title": "D&D AI Dungeon Master",
        }

        http_client = httpx.AsyncClient(headers=headers)

        provider = OpenAIProvider(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
            http_client=http_client,
        )

        return OpenAIModel(settings.openrouter_model, provider=provider)

    @classmethod
    def _register_agent_tools(cls, agent: Agent[AgentDependencies, str], tools: list[ToolFunction]) -> None:
        """Register tools with an agent."""
        for tool in tools:
            agent.tool(tool)
        logger.info(f"Registered {len(tools)} tools with the agent")

    @classmethod
    def create_agent(
        cls,
        agent_type: AgentType,
        event_bus: IEventBus | None = None,
        scenario_service: IScenarioService | None = None,
        item_repository: IItemRepository | None = None,
        monster_repository: IMonsterRepository | None = None,
        spell_repository: ISpellRepository | None = None,
        metadata_service: IMetadataService | None = None,
        debug: bool = False,
    ) -> BaseAgent:
        """Create a specialized agent based on type."""
        settings = get_settings()
        model = cls._create_model()
        model_settings = ModelSettings(temperature=0.7, max_tokens=4096, parallel_tool_calls=True)

        if agent_type == AgentType.NARRATIVE:
            # Create the pydantic-ai agent
            agent: Agent[AgentDependencies, str] = Agent(
                model=model,
                deps_type=AgentDependencies,
                system_prompt=cls.NARRATIVE_SYSTEM_PROMPT,
                model_settings=model_settings,
                retries=settings.max_retries,
            )

            # Create narrative agent instance
            if not event_bus:
                raise ValueError("Event bus is required for narrative agent")
            if not scenario_service:
                raise ValueError("ScenarioService is required for NarrativeAgent")
            if not item_repository or not monster_repository or not spell_repository:
                raise ValueError("Repositories are required for NarrativeAgent")
            if not metadata_service:
                raise ValueError("MetadataService is required for NarrativeAgent")

            narrative_agent = NarrativeAgent(
                agent=agent,
                context_service=ContextService(scenario_service, item_repository, monster_repository, spell_repository),
                message_converter=MessageConverterService(),
                event_logger=EventLoggerService(game_id="", debug=debug),
                metadata_service=metadata_service,
                event_bus=event_bus,
                scenario_service=scenario_service,
                item_repository=item_repository,
                monster_repository=monster_repository,
                spell_repository=spell_repository,
            )

            # Register its required tools
            cls._register_agent_tools(agent, narrative_agent.get_required_tools())

            return narrative_agent

        if agent_type == AgentType.COMBAT:
            raise NotImplementedError("Combat agent not yet implemented")

        if agent_type == AgentType.SUMMARIZER:
            raise NotImplementedError("Summarizer agent not yet implemented")

        raise ValueError(f"Unknown agent type: {agent_type}")
