"""Tests for heuristic tool suggestion rules."""

import pytest

from app.models.tool_suggestion_config import PatternConfig, RuleConfig, SuggestionConfig
from app.services.ai.tool_suggestion.heuristic_rules import (
    CurrencyTransactionRule,
    InventoryChangeRule,
    QuestProgressionRule,
)
from tests.factories import make_game_state


@pytest.fixture
def quest_rule_config() -> RuleConfig:
    """Create a sample quest progression rule config."""
    return RuleConfig(
        rule_id="test_quest",
        rule_class="QuestProgressionRule",
        enabled=True,
        description="Test quest rule",
        patterns=[
            PatternConfig(
                pattern=r"\baccept.*quest\b",
                weight=0.9,
                description="Quest acceptance",
            ),
            PatternConfig(
                pattern=r"\bcomplete.*quest\b",
                weight=0.85,
                description="Quest completion",
            ),
        ],
        suggestions=[
            SuggestionConfig(
                tool_name="start_quest",
                reason="Player accepted a quest",
                confidence_multiplier=1.0,
            ),
        ],
        applicable_agents=["narrative"],
        base_confidence=0.8,
    )


def test_quest_rule_matches_pattern(quest_rule_config: RuleConfig) -> None:
    """Test quest rule matches when pattern is present."""
    rule = QuestProgressionRule(quest_rule_config)
    game_state = make_game_state()

    prompt = "I accept the quest to rescue the princess"
    suggestions = rule.evaluate(prompt, game_state, "narrative")

    assert len(suggestions) == 1
    assert suggestions[0].tool_name == "start_quest"
    assert suggestions[0].confidence > 0.0


def test_quest_rule_no_match_when_pattern_absent(quest_rule_config: RuleConfig) -> None:
    """Test quest rule returns empty when pattern doesn't match."""
    rule = QuestProgressionRule(quest_rule_config)
    game_state = make_game_state()

    prompt = "I walk down the street"
    suggestions = rule.evaluate(prompt, game_state, "narrative")

    assert len(suggestions) == 0


def test_quest_rule_no_match_wrong_agent(quest_rule_config: RuleConfig) -> None:
    """Test quest rule returns empty for non-applicable agent."""
    rule = QuestProgressionRule(quest_rule_config)
    game_state = make_game_state()

    prompt = "I accept the quest"
    # Rule is configured for "narrative", not "combat"
    suggestions = rule.evaluate(prompt, game_state, "combat")

    assert len(suggestions) == 0


def test_quest_rule_confidence_calculation(quest_rule_config: RuleConfig) -> None:
    """Test that confidence is calculated correctly."""
    rule = QuestProgressionRule(quest_rule_config)
    game_state = make_game_state()

    prompt = "I accept the quest"
    suggestions = rule.evaluate(prompt, game_state, "narrative")

    # Confidence should be base_confidence * pattern_weight * confidence_multiplier
    # 0.8 * 0.9 * 1.0 = 0.72
    assert len(suggestions) == 1
    assert suggestions[0].confidence == pytest.approx(0.72, abs=0.01)


def test_inventory_rule_matches_item_acquisition() -> None:
    """Test inventory rule matches item acquisition."""
    config = RuleConfig(
        rule_id="test_inventory",
        rule_class="InventoryChangeRule",
        enabled=True,
        description="Test inventory rule",
        patterns=[
            PatternConfig(pattern=r"\b(find|loot|take).*sword\b", weight=0.85),
        ],
        suggestions=[
            SuggestionConfig(tool_name="modify_inventory", reason="Item acquired"),
        ],
        applicable_agents=["narrative"],
        base_confidence=0.75,
    )

    rule = InventoryChangeRule(config)
    game_state = make_game_state()

    prompt = "I find a magic sword in the chest"
    suggestions = rule.evaluate(prompt, game_state, "narrative")

    assert len(suggestions) == 1
    assert suggestions[0].tool_name == "modify_inventory"


def test_currency_rule_matches_gold_transaction() -> None:
    """Test currency rule matches gold transactions."""
    config = RuleConfig(
        rule_id="test_currency",
        rule_class="CurrencyTransactionRule",
        enabled=True,
        description="Test currency rule",
        patterns=[
            PatternConfig(pattern=r"\d+\s+gold\b", weight=0.9),
        ],
        suggestions=[
            SuggestionConfig(tool_name="modify_currency", reason="Currency transaction"),
        ],
        applicable_agents=["narrative"],
        base_confidence=0.8,
    )

    rule = CurrencyTransactionRule(config)
    game_state = make_game_state()

    prompt = "The merchant gives me 50 gold pieces"
    suggestions = rule.evaluate(prompt, game_state, "narrative")

    assert len(suggestions) == 1
    assert suggestions[0].tool_name == "modify_currency"


def test_pattern_case_insensitive() -> None:
    """Test that pattern matching is case-insensitive."""
    config = RuleConfig(
        rule_id="test_case",
        rule_class="QuestProgressionRule",
        enabled=True,
        description="Test case sensitivity",
        patterns=[
            PatternConfig(pattern=r"\bQUEST\b", weight=0.9),
        ],
        suggestions=[
            SuggestionConfig(tool_name="test", reason="test"),
        ],
        applicable_agents=["narrative"],
        base_confidence=0.8,
    )

    rule = QuestProgressionRule(config)
    game_state = make_game_state()

    # Pattern is "QUEST" but should match "quest"
    prompt = "I accept the quest"
    suggestions = rule.evaluate(prompt, game_state, "narrative")

    assert len(suggestions) == 1


def test_multiple_patterns_use_highest_weight() -> None:
    """Test that when multiple patterns match, highest weight is used."""
    config = RuleConfig(
        rule_id="test_multi",
        rule_class="QuestProgressionRule",
        enabled=True,
        description="Test multiple patterns",
        patterns=[
            PatternConfig(pattern=r"\bquest\b", weight=0.5),
            PatternConfig(pattern=r"\bepic.*quest\b", weight=0.95),
        ],
        suggestions=[
            SuggestionConfig(tool_name="test", reason="test", confidence_multiplier=1.0),
        ],
        applicable_agents=["narrative"],
        base_confidence=0.8,
    )

    rule = QuestProgressionRule(config)
    game_state = make_game_state()

    prompt = "I accept the epic quest"
    suggestions = rule.evaluate(prompt, game_state, "narrative")

    # Should use higher weight: 0.8 * 0.95 * 1.0 = 0.76
    assert len(suggestions) == 1
    assert suggestions[0].confidence == pytest.approx(0.76, abs=0.01)


def test_confidence_multiplier_applied() -> None:
    """Test that confidence multiplier is applied correctly."""
    config = RuleConfig(
        rule_id="test_multiplier",
        rule_class="QuestProgressionRule",
        enabled=True,
        description="Test multiplier",
        patterns=[
            PatternConfig(pattern=r"\bquest\b", weight=1.0),
        ],
        suggestions=[
            SuggestionConfig(tool_name="test", reason="test", confidence_multiplier=1.5),
        ],
        applicable_agents=["narrative"],
        base_confidence=0.5,
    )

    rule = QuestProgressionRule(config)
    game_state = make_game_state()

    prompt = "I accept the quest"
    suggestions = rule.evaluate(prompt, game_state, "narrative")

    # Confidence: 0.5 * 1.0 * 1.5 = 0.75
    assert len(suggestions) == 1
    assert suggestions[0].confidence == pytest.approx(0.75, abs=0.01)


def test_confidence_capped_at_1_0() -> None:
    """Test that confidence is capped at 1.0 even with high multipliers."""
    config = RuleConfig(
        rule_id="test_cap",
        rule_class="QuestProgressionRule",
        enabled=True,
        description="Test cap",
        patterns=[
            PatternConfig(pattern=r"\bquest\b", weight=1.0),
        ],
        suggestions=[
            SuggestionConfig(tool_name="test", reason="test", confidence_multiplier=2.0),
        ],
        applicable_agents=["narrative"],
        base_confidence=1.0,
    )

    rule = QuestProgressionRule(config)
    game_state = make_game_state()

    prompt = "quest"
    suggestions = rule.evaluate(prompt, game_state, "narrative")

    # Would be 1.0 * 1.0 * 2.0 = 2.0, but should be capped at 1.0
    assert len(suggestions) == 1
    assert suggestions[0].confidence == 1.0
