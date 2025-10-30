"""Heuristic rules for tool suggestion system."""

import logging
import re
from abc import ABC, abstractmethod

from app.models.game_state import GameState
from app.models.tool_suggestion import ToolSuggestion
from app.models.tool_suggestion_config import RuleConfig

logger = logging.getLogger(__name__)


class HeuristicRule(ABC):
    """Base class for heuristic-based tool suggestion rules."""

    def __init__(self, config: RuleConfig):
        """Initialize the rule with its configuration.

        Args:
            config: Rule configuration from JSON

        """
        self.config = config
        # Compile regex patterns for efficient matching
        self.compiled_patterns = [
            (re.compile(pattern.pattern, re.IGNORECASE), pattern.weight) for pattern in config.patterns
        ]

    @abstractmethod
    def evaluate(
        self,
        prompt: str,
        game_state: GameState,
        agent_type: str,
    ) -> list[ToolSuggestion]:
        """Evaluate this rule and return tool suggestions.

        Args:
            prompt: User's prompt text
            game_state: Current game state
            agent_type: Type of agent being invoked

        Returns:
            List of tool suggestions (empty if rule doesn't match)

        """

    def _check_patterns(self, text: str) -> tuple[bool, float]:
        """Check if any patterns match the text.

        Args:
            text: Text to match against

        Returns:
            Tuple of (matched, best_weight) where best_weight is 0.0 if no match

        """
        best_weight = 0.0
        matched = False

        for pattern, weight in self.compiled_patterns:
            if pattern.search(text):
                matched = True
                best_weight = max(best_weight, weight)

        return matched, best_weight

    def _build_suggestions(self, confidence: float) -> list[ToolSuggestion]:
        """Build suggestions from config with calculated confidence.

        Args:
            confidence: Final confidence score for this rule

        Returns:
            List of tool suggestions with appropriate confidence

        """
        suggestions = []
        for suggestion_config in self.config.suggestions:
            # Apply confidence multiplier from config
            final_confidence = min(1.0, confidence * suggestion_config.confidence_multiplier)

            suggestions.append(
                ToolSuggestion(
                    tool_name=suggestion_config.tool_name,
                    reason=suggestion_config.reason,
                    confidence=final_confidence,
                    arguments=suggestion_config.suggested_args,
                ),
            )

        return suggestions


class QuestProgressionRule(HeuristicRule):
    """Suggests quest-related tools when quest actions are detected."""

    def evaluate(
        self,
        prompt: str,
        game_state: GameState,
        agent_type: str,
    ) -> list[ToolSuggestion]:
        # Check if this rule applies to the current agent type
        if agent_type not in self.config.applicable_agents:
            return []

        # Check if patterns match
        matched, weight = self._check_patterns(prompt)
        if not matched:
            return []

        # Calculate final confidence
        confidence = self.config.base_confidence * weight

        return self._build_suggestions(confidence)


class InventoryChangeRule(HeuristicRule):
    """Suggests inventory tools when items are acquired or transferred."""

    def evaluate(
        self,
        prompt: str,
        game_state: GameState,
        agent_type: str,
    ) -> list[ToolSuggestion]:
        if agent_type not in self.config.applicable_agents:
            return []

        matched, weight = self._check_patterns(prompt)
        if not matched:
            return []

        confidence = self.config.base_confidence * weight
        return self._build_suggestions(confidence)


class CurrencyTransactionRule(HeuristicRule):
    """Suggests currency modification when money is mentioned."""

    def evaluate(
        self,
        prompt: str,
        game_state: GameState,
        agent_type: str,
    ) -> list[ToolSuggestion]:
        if agent_type not in self.config.applicable_agents:
            return []

        matched, weight = self._check_patterns(prompt)
        if not matched:
            return []

        confidence = self.config.base_confidence * weight
        return self._build_suggestions(confidence)


class PartyManagementRule(HeuristicRule):
    """Suggests party tools when NPCs join or leave the party."""

    def evaluate(
        self,
        prompt: str,
        game_state: GameState,
        agent_type: str,
    ) -> list[ToolSuggestion]:
        if agent_type not in self.config.applicable_agents:
            return []

        # Check required context
        if self.config.required_context and "npcs" in self.config.required_context and not game_state.npcs:
            return []

        matched, weight = self._check_patterns(prompt)
        if not matched:
            return []

        confidence = self.config.base_confidence * weight
        return self._build_suggestions(confidence)


class TimePassageRule(HeuristicRule):
    """Suggests rest and time advancement tools."""

    def evaluate(
        self,
        prompt: str,
        game_state: GameState,
        agent_type: str,
    ) -> list[ToolSuggestion]:
        if agent_type not in self.config.applicable_agents:
            return []

        matched, weight = self._check_patterns(prompt)
        if not matched:
            return []

        confidence = self.config.base_confidence * weight
        return self._build_suggestions(confidence)


class LocationTransitionRule(HeuristicRule):
    """Suggests location tools when player moves to new locations."""

    def evaluate(
        self,
        prompt: str,
        game_state: GameState,
        agent_type: str,
    ) -> list[ToolSuggestion]:
        if agent_type not in self.config.applicable_agents:
            return []

        matched, weight = self._check_patterns(prompt)
        if not matched:
            return []

        confidence = self.config.base_confidence * weight
        return self._build_suggestions(confidence)


# Rule registry mapping rule_class names to implementation classes
RULE_CLASSES: dict[str, type[HeuristicRule]] = {
    "QuestProgressionRule": QuestProgressionRule,
    "InventoryChangeRule": InventoryChangeRule,
    "CurrencyTransactionRule": CurrencyTransactionRule,
    "PartyManagementRule": PartyManagementRule,
    "TimePassageRule": TimePassageRule,
    "LocationTransitionRule": LocationTransitionRule,
}
