"""Tests for keyword-based priority classifier."""

from hemdov.domain.services.keyword_classifier import KeywordBasedClassifier
from shared.priority_entities import PriorityRule


def test_classifier_should_return_high_priority_for_instructions():
    """Verify that 'instructions' keyword triggers priority 5."""
    classifier = KeywordBasedClassifier()
    priority, category = classifier.classify("instructions.md")
    assert priority == 5
    assert category == "instruction"


def test_classifier_should_return_high_priority_for_rules():
    """Verify that 'rule' keyword triggers priority 5."""
    classifier = KeywordBasedClassifier()
    priority, category = classifier.classify("rule.md")
    assert priority == 5
    assert category == "instruction"


def test_classifier_should_return_medium_priority_for_agent():
    """Verify that 'agent' keyword triggers priority 4."""
    classifier = KeywordBasedClassifier()
    priority, category = classifier.classify("agent.md")
    assert priority == 4
    assert category == "agent"


def test_classifier_should_return_default_for_unknown():
    """Verify that unknown filenames get default priority."""
    classifier = KeywordBasedClassifier()
    priority, category = classifier.classify("random.txt")
    assert priority == 1
    assert category == "general"


def test_classifier_should_accept_custom_rules():
    """Verify that classifier can use custom rules."""
    custom_rules = (PriorityRule(("critical",), priority=5, category="critical"),)
    classifier = KeywordBasedClassifier(rules=custom_rules)
    priority, category = classifier.classify("critical.md")
    assert priority == 5
    assert category == "critical"


def test_classifier_should_be_case_insensitive():
    """Verify that classification is case-insensitive."""
    classifier = KeywordBasedClassifier()
    priority1, cat1 = classifier.classify("INSTRUCTIONS.MD")
    priority2, cat2 = classifier.classify("instructions.md")
    assert priority1 == priority2 == 5
    assert cat1 == cat2 == "instruction"
