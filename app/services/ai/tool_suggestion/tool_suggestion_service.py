"""Tool suggestion service for generating heuristic-based tool recommendations."""

import logging

from app.interfaces.services.ai import IToolSuggestionService
from app.models.game_state import GameState
from app.models.tool_suggestion import ToolSuggestion, ToolSuggestions
from app.services.ai.config_loader import AgentConfigLoader
from app.services.ai.tool_suggestion.heuristic_rules import RULE_CLASSES, HeuristicRule

logger = logging.getLogger(__name__)


class ToolSuggestionService(IToolSuggestionService):
    """Service for generating tool suggestions based on heuristic rules."""

    def __init__(self, config_loader: AgentConfigLoader):
        """Initialize the tool suggestion service.

        Loads rule configuration and instantiates heuristic rules.

        Args:
            config_loader: Config loader for loading tool suggestion rules

        """
        # Load rules configuration
        rules_config = config_loader.load_tool_suggestion_rules()

        # Instantiate rule objects from config
        self.rules: list[HeuristicRule] = []
        for rule_config in rules_config.rules:
            if not rule_config.enabled:
                continue
            rule_class = RULE_CLASSES.get(rule_config.rule_class)
            if rule_class:
                self.rules.append(rule_class(rule_config))
            else:
                logger.warning(
                    f"Unknown rule_class '{rule_config.rule_class}' in rule '{rule_config.rule_id}' - skipping"
                )

        # Get global settings
        self.min_confidence_threshold = rules_config.global_settings.get("min_confidence_threshold", 0.6)
        self.max_suggestions = rules_config.global_settings.get("max_suggestions_per_turn", 3)

        logger.info(
            f"ToolSuggestionService initialized with {len(self.rules)} rules, "
            f"min_confidence={self.min_confidence_threshold}, max_suggestions={self.max_suggestions}",
        )

    async def suggest_tools(
        self,
        game_state: GameState,
        prompt: str,
        agent_type: str,
    ) -> ToolSuggestions:
        all_suggestions: list[ToolSuggestion] = []

        # Evaluate all rules
        for rule in self.rules:
            try:
                suggestions = rule.evaluate(prompt, game_state, agent_type)
                all_suggestions.extend(suggestions)
            except Exception as e:
                # Log error but don't fail - continue with other rules
                logger.warning(
                    f"Error evaluating rule {rule.config.rule_id}: {e}",
                    exc_info=True,
                )

        # Filter by confidence threshold
        filtered = [s for s in all_suggestions if s.confidence >= self.min_confidence_threshold]

        # Deduplicate by tool_name, keeping highest confidence
        deduped: dict[str, ToolSuggestion] = {}
        for suggestion in filtered:
            if suggestion.tool_name not in deduped or suggestion.confidence > deduped[suggestion.tool_name].confidence:
                deduped[suggestion.tool_name] = suggestion

        # Sort by confidence descending
        sorted_suggestions = sorted(
            deduped.values(),
            key=lambda s: s.confidence,
            reverse=True,
        )

        # Limit to max_suggestions
        final_suggestions = sorted_suggestions[: self.max_suggestions]

        logger.info(
            f"Generated {len(final_suggestions)} suggestions for agent_type={agent_type} "
            f"(from {len(all_suggestions)} raw, {len(filtered)} after filtering)",
        )

        return ToolSuggestions(suggestions=final_suggestions)
