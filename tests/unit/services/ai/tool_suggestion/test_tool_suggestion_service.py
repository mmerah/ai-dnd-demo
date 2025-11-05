"""Tests for ToolSuggestionService."""

from unittest.mock import Mock

import pytest

from app.models.tool_suggestion_config import (
    PatternConfig,
    RuleConfig,
    SuggestionConfig,
    ToolSuggestionRulesConfig,
)
from app.services.ai.config_loader import AgentConfigLoader
from app.services.ai.tool_suggestion.tool_suggestion_service import ToolSuggestionService
from tests.factories import make_game_state


def make_mock_config_loader(
    rules_configs: list[RuleConfig],
    min_confidence: float = 0.5,
    max_suggestions: int = 3,
) -> Mock:
    """Create a mock AgentConfigLoader with specified rules."""
    mock_loader = Mock(spec=AgentConfigLoader)
    rules_config = ToolSuggestionRulesConfig(
        rules=rules_configs,
        global_settings={
            "min_confidence_threshold": min_confidence,
            "max_suggestions_per_turn": max_suggestions,
        },
    )
    mock_loader.load_tool_suggestion_rules.return_value = rules_config
    return mock_loader


@pytest.mark.asyncio
async def test_service_evaluates_all_rules() -> None:
    """Test that service evaluates all provided rules."""
    rule_config = RuleConfig(
        rule_id="test_inventory",
        rule_class="InventoryChangeRule",
        enabled=True,
        description="Test inventory rule",
        patterns=[
            PatternConfig(pattern=r"\bfind.*sword\b", weight=0.9),
        ],
        suggestions=[
            SuggestionConfig(tool_name="modify_inventory", reason="Item found"),
        ],
        applicable_agents=["narrative"],
        base_confidence=0.8,
    )

    config_loader = make_mock_config_loader([rule_config])
    service = ToolSuggestionService(config_loader)

    game_state = make_game_state()
    prompt = "I find a magic sword"

    result = await service.suggest_tools(game_state, prompt, "narrative")

    assert len(result.suggestions) == 1
    assert result.suggestions[0].tool_name == "modify_inventory"


@pytest.mark.asyncio
async def test_service_filters_by_confidence() -> None:
    """Test that service filters out low-confidence suggestions."""
    # Create rule with low confidence
    config = RuleConfig(
        rule_id="low_conf",
        rule_class="InventoryChangeRule",
        enabled=True,
        description="Low confidence rule",
        patterns=[
            PatternConfig(pattern=r"\bitem\b", weight=0.5),
        ],
        suggestions=[
            SuggestionConfig(tool_name="modify_inventory", reason="Item change"),
        ],
        applicable_agents=["narrative"],
        base_confidence=0.3,  # 0.3 * 0.5 = 0.15
    )

    config_loader = make_mock_config_loader([config], min_confidence=0.5)
    service = ToolSuggestionService(config_loader)

    game_state = make_game_state()
    prompt = "I find an item"

    result = await service.suggest_tools(game_state, prompt, "narrative")

    # Suggestion should be filtered out due to low confidence (0.15 < 0.5)
    assert len(result.suggestions) == 0


@pytest.mark.asyncio
async def test_service_deduplicates_by_tool_name() -> None:
    """Test that service deduplicates suggestions, keeping highest confidence."""
    # Create two rules suggesting the same tool with different confidence
    high_conf_config = RuleConfig(
        rule_id="high",
        rule_class="InventoryChangeRule",
        enabled=True,
        description="High confidence",
        patterns=[PatternConfig(pattern=r"\bitem\b", weight=1.0)],
        suggestions=[SuggestionConfig(tool_name="modify_inventory", reason="High confidence")],
        applicable_agents=["narrative"],
        base_confidence=0.9,  # 0.9 * 1.0 = 0.9
    )

    low_conf_config = RuleConfig(
        rule_id="low",
        rule_class="InventoryChangeRule",
        enabled=True,
        description="Low confidence",
        patterns=[PatternConfig(pattern=r"\bitem\b", weight=1.0)],
        suggestions=[SuggestionConfig(tool_name="modify_inventory", reason="Low confidence")],
        applicable_agents=["narrative"],
        base_confidence=0.6,  # 0.6 * 1.0 = 0.6
    )

    config_loader = make_mock_config_loader([high_conf_config, low_conf_config])
    service = ToolSuggestionService(config_loader)

    game_state = make_game_state()
    prompt = "item"

    result = await service.suggest_tools(game_state, prompt, "narrative")

    # Should only have one suggestion with highest confidence
    assert len(result.suggestions) == 1
    assert result.suggestions[0].tool_name == "modify_inventory"
    assert result.suggestions[0].confidence == pytest.approx(0.9, abs=0.01)
    assert result.suggestions[0].reason == "High confidence"


@pytest.mark.asyncio
async def test_service_sorts_by_confidence() -> None:
    """Test that service sorts suggestions by confidence descending."""
    high_config = RuleConfig(
        rule_id="high",
        rule_class="CurrencyTransactionRule",
        enabled=True,
        description="High",
        patterns=[PatternConfig(pattern=r"\b100 gold\b", weight=1.0)],
        suggestions=[SuggestionConfig(tool_name="modify_currency", reason="High value")],
        applicable_agents=["narrative"],
        base_confidence=0.9,
    )

    low_config = RuleConfig(
        rule_id="low",
        rule_class="InventoryChangeRule",
        enabled=True,
        description="Low",
        patterns=[PatternConfig(pattern=r"\bitem\b", weight=1.0)],
        suggestions=[SuggestionConfig(tool_name="modify_inventory", reason="Item change")],
        applicable_agents=["narrative"],
        base_confidence=0.6,
    )

    config_loader = make_mock_config_loader([low_config, high_config])
    service = ToolSuggestionService(config_loader)

    game_state = make_game_state()
    prompt = "I receive 100 gold and an item"

    result = await service.suggest_tools(game_state, prompt, "narrative")

    assert len(result.suggestions) == 2
    # Should be sorted by confidence descending
    assert result.suggestions[0].tool_name == "modify_currency"
    assert result.suggestions[1].tool_name == "modify_inventory"


@pytest.mark.asyncio
async def test_service_limits_max_suggestions() -> None:
    """Test that service limits number of suggestions returned."""
    configs = []
    for i in range(5):
        config = RuleConfig(
            rule_id=f"rule_{i}",
            rule_class="InventoryChangeRule",
            enabled=True,
            description=f"Rule {i}",
            patterns=[PatternConfig(pattern=r"\bitem\b", weight=1.0)],
            suggestions=[SuggestionConfig(tool_name=f"tool_{i}", reason=f"Rule {i}")],
            applicable_agents=["narrative"],
            base_confidence=0.8,
        )
        configs.append(config)

    config_loader = make_mock_config_loader(configs, max_suggestions=3)
    service = ToolSuggestionService(config_loader)

    game_state = make_game_state()
    prompt = "I find an item"

    result = await service.suggest_tools(game_state, prompt, "narrative")

    # Should only return 3 suggestions even though 5 matched
    assert len(result.suggestions) == 3


@pytest.mark.asyncio
async def test_service_handles_rule_exceptions() -> None:
    """Test that service continues when a rule raises an exception."""
    # Create a good rule config
    good_config = RuleConfig(
        rule_id="good",
        rule_class="InventoryChangeRule",
        enabled=True,
        description="Good rule",
        patterns=[PatternConfig(pattern=r"\bitem\b", weight=1.0)],
        suggestions=[SuggestionConfig(tool_name="modify_inventory", reason="Good")],
        applicable_agents=["narrative"],
        base_confidence=0.8,
    )

    # Create a bad rule config with unknown class (will be skipped)
    bad_config = RuleConfig(
        rule_id="bad",
        rule_class="UnknownRuleClass",
        enabled=True,
        description="Bad rule",
        patterns=[PatternConfig(pattern=r"\bitem\b", weight=1.0)],
        suggestions=[SuggestionConfig(tool_name="bad_tool", reason="Bad")],
        applicable_agents=["narrative"],
        base_confidence=0.8,
    )

    config_loader = make_mock_config_loader([bad_config, good_config])
    service = ToolSuggestionService(config_loader)

    game_state = make_game_state()
    prompt = "I find an item"

    # Should skip unknown rule class and return suggestion from good rule
    result = await service.suggest_tools(game_state, prompt, "narrative")

    assert len(result.suggestions) == 1
    assert result.suggestions[0].tool_name == "modify_inventory"


@pytest.mark.asyncio
async def test_service_returns_empty_when_no_matches() -> None:
    """Test that service returns empty suggestions when nothing matches."""
    config = RuleConfig(
        rule_id="inventory",
        rule_class="InventoryChangeRule",
        enabled=True,
        description="Inventory rule",
        patterns=[PatternConfig(pattern=r"\bitem\b", weight=1.0)],
        suggestions=[SuggestionConfig(tool_name="modify_inventory", reason="Item change")],
        applicable_agents=["narrative"],
        base_confidence=0.8,
    )

    config_loader = make_mock_config_loader([config])
    service = ToolSuggestionService(config_loader)

    game_state = make_game_state()
    prompt = "I walk down the street"

    result = await service.suggest_tools(game_state, prompt, "narrative")

    assert len(result.suggestions) == 0


@pytest.mark.asyncio
async def test_service_empty_with_no_rules() -> None:
    """Test that service works with empty rule list."""
    config_loader = make_mock_config_loader([])
    service = ToolSuggestionService(config_loader)

    game_state = make_game_state()
    prompt = "anything"

    result = await service.suggest_tools(game_state, prompt, "narrative")

    assert len(result.suggestions) == 0
