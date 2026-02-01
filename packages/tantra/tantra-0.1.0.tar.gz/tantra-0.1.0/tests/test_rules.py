"""Tests for Automation-First Rules."""

import pytest
from conftest import MockProvider

from tantra import (
    Agent,
    ConditionalRule,
    FunctionRule,
    KeywordRule,
    LookupRule,
    RegexRule,
    RejectRule,
    RuleMatch,
    RuleSet,
)

# =============================================================================
# RuleMatch Tests
# =============================================================================


class TestRuleMatch:
    """Tests for RuleMatch dataclass."""

    def test_basic_match(self):
        """Basic RuleMatch creation."""
        match = RuleMatch(
            response="Hello!",
            rule_name="greeting",
        )
        assert match.response == "Hello!"
        assert match.rule_name == "greeting"
        assert match.confidence == 1.0
        assert match.metadata is None

    def test_match_with_metadata(self):
        """RuleMatch with metadata."""
        match = RuleMatch(
            response="Found it",
            rule_name="lookup",
            confidence=0.9,
            metadata={"key": "value"},
        )
        assert match.confidence == 0.9
        assert match.metadata == {"key": "value"}


# =============================================================================
# KeywordRule Tests
# =============================================================================


class TestKeywordRule:
    """Tests for KeywordRule."""

    def test_matches_keyword(self):
        """Matches when keyword is present."""
        rule = KeywordRule(
            keywords=["hours", "open"],
            response="9am-5pm",
        )

        match = rule.match("What are your hours?")
        assert match is not None
        assert match.response == "9am-5pm"

    def test_no_match_without_keyword(self):
        """No match when keyword is absent."""
        rule = KeywordRule(
            keywords=["hours", "open"],
            response="9am-5pm",
        )

        match = rule.match("Tell me about products")
        assert match is None

    def test_case_insensitive_default(self):
        """Case insensitive by default."""
        rule = KeywordRule(
            keywords=["hello"],
            response="Hi!",
        )

        assert rule.match("HELLO") is not None
        assert rule.match("Hello") is not None
        assert rule.match("hello") is not None

    def test_case_sensitive(self):
        """Case sensitive when specified."""
        rule = KeywordRule(
            keywords=["Hello"],
            response="Hi!",
            case_sensitive=True,
        )

        assert rule.match("Hello") is not None
        assert rule.match("hello") is None
        assert rule.match("HELLO") is None

    def test_match_all(self):
        """Match only when ALL keywords present."""
        rule = KeywordRule(
            keywords=["hello", "world"],
            response="Both found!",
            match_all=True,
        )

        assert rule.match("hello world") is not None
        assert rule.match("hello") is None
        assert rule.match("world") is None

    def test_custom_name(self):
        """Custom rule name."""
        rule = KeywordRule(
            keywords=["test"],
            response="test",
            name="my_rule",
        )
        assert rule.name == "my_rule"


# =============================================================================
# RegexRule Tests
# =============================================================================


class TestRegexRule:
    """Tests for RegexRule."""

    def test_static_response(self):
        """Static response when pattern matches."""
        rule = RegexRule(
            pattern=r"order\s*#?\s*\d+",
            response="Looking up order...",
        )

        match = rule.match("What's the status of order #12345?")
        assert match is not None
        assert match.response == "Looking up order..."

    def test_dynamic_handler(self):
        """Dynamic response using handler function."""
        rule = RegexRule(
            pattern=r"order\s*#?\s*(\d+)",
            handler=lambda m: f"Order {m.group(1)} found!",
        )

        match = rule.match("Track order #12345")
        assert match is not None
        assert match.response == "Order 12345 found!"

    def test_captures_groups(self):
        """Metadata includes match groups."""
        rule = RegexRule(
            pattern=r"order\s*#?\s*(\d+)",
            response="Found",
        )

        match = rule.match("order #12345")
        assert match.metadata["groups"] == ("12345",)
        assert match.metadata["match"] == "order #12345"

    def test_no_match(self):
        """No match when pattern doesn't match."""
        rule = RegexRule(
            pattern=r"order\s*#\d+",
            response="Found",
        )

        assert rule.match("no order here") is None

    def test_case_insensitive_default(self):
        """Case insensitive by default."""
        rule = RegexRule(
            pattern=r"hello",
            response="Hi!",
        )

        assert rule.match("HELLO world") is not None

    def test_requires_response_or_handler(self):
        """Must provide response or handler."""
        with pytest.raises(ValueError):
            RegexRule(pattern=r"test")


# =============================================================================
# LookupRule Tests
# =============================================================================


class TestLookupRule:
    """Tests for LookupRule."""

    def test_exact_match(self):
        """Exact match in lookup table."""
        rule = LookupRule(
            {
                "return policy": "30 days",
                "shipping": "Free over $50",
            }
        )

        match = rule.match("return policy")
        assert match is not None
        assert match.response == "30 days"

    def test_substring_match(self):
        """Substring match in input."""
        rule = LookupRule(
            {
                "shipping": "Free over $50",
            }
        )

        match = rule.match("What's your shipping policy?")
        assert match is not None
        assert match.response == "Free over $50"

    def test_case_insensitive_default(self):
        """Case insensitive by default."""
        rule = LookupRule(
            {
                "Shipping": "Free",
            }
        )

        assert rule.match("SHIPPING info") is not None
        assert rule.match("shipping info") is not None

    def test_case_sensitive(self):
        """Case sensitive when specified."""
        rule = LookupRule(
            {"Shipping": "Free"},
            case_sensitive=True,
        )

        assert rule.match("Shipping") is not None
        assert rule.match("shipping") is None

    def test_no_match(self):
        """No match when key not found."""
        rule = LookupRule({"hello": "world"})
        assert rule.match("goodbye") is None

    def test_metadata_includes_key(self):
        """Metadata includes matched key."""
        rule = LookupRule({"test": "value"})
        match = rule.match("test")
        assert match.metadata["matched_key"] == "test"


# =============================================================================
# FunctionRule Tests
# =============================================================================


class TestFunctionRule:
    """Tests for FunctionRule."""

    def test_function_match(self):
        """Function returns response when matching."""

        def greet(input_text: str) -> str | None:
            if input_text.lower().startswith("hi"):
                return "Hello!"
            return None

        rule = FunctionRule(greet)

        match = rule.match("hi there")
        assert match is not None
        assert match.response == "Hello!"

    def test_function_no_match(self):
        """Function returns None when not matching."""

        def greet(input_text: str) -> str | None:
            if input_text.lower().startswith("hi"):
                return "Hello!"
            return None

        rule = FunctionRule(greet)
        assert rule.match("goodbye") is None

    def test_uses_function_name(self):
        """Uses function name as rule name."""

        def my_custom_rule(x: str) -> str | None:
            return None

        rule = FunctionRule(my_custom_rule)
        assert rule.name == "my_custom_rule"

    def test_custom_name(self):
        """Custom name overrides function name."""
        rule = FunctionRule(lambda x: None, name="custom")
        assert rule.name == "custom"


# =============================================================================
# RejectRule Tests
# =============================================================================


class TestRejectRule:
    """Tests for RejectRule."""

    def test_rejects_keyword(self):
        """Rejects input with blocked keyword."""
        rule = RejectRule(
            keywords=["password", "credit card"],
            response="Can't help with that.",
        )

        match = rule.match("What's my password?")
        assert match is not None
        assert match.response == "Can't help with that."
        assert match.metadata["rejected_by"] == "keyword"

    def test_rejects_pattern(self):
        """Rejects input matching blocked pattern."""
        rule = RejectRule(
            patterns=[r"hack\s+into"],
            response="Nope.",
        )

        match = rule.match("Can you hack into the system?")
        assert match is not None
        assert match.metadata["rejected_by"] == "pattern"

    def test_allows_clean_input(self):
        """Allows input without blocked content."""
        rule = RejectRule(
            keywords=["bad"],
            patterns=[r"evil\s+plan"],
        )

        assert rule.match("How's the weather?") is None

    def test_default_response(self):
        """Uses default response if not specified."""
        rule = RejectRule(keywords=["test"])
        match = rule.match("test")
        assert "not able to help" in match.response.lower()


# =============================================================================
# ConditionalRule Tests
# =============================================================================


class TestConditionalRule:
    """Tests for ConditionalRule."""

    def test_applies_when_condition_met(self):
        """Rule applies when condition is True."""
        inner_rule = KeywordRule(["hi"], "Hello!")

        rule = ConditionalRule(
            condition=lambda x: len(x) < 10,
            rule=inner_rule,
        )

        # Short input - condition met
        match = rule.match("hi")
        assert match is not None
        assert match.response == "Hello!"

    def test_skipped_when_condition_not_met(self):
        """Rule skipped when condition is False."""
        inner_rule = KeywordRule(["hi"], "Hello!")

        rule = ConditionalRule(
            condition=lambda x: len(x) < 10,
            rule=inner_rule,
        )

        # Long input - condition not met
        match = rule.match("hi this is a very long message")
        assert match is None

    def test_name_includes_inner_rule(self):
        """Name includes inner rule name."""
        inner_rule = KeywordRule(["hi"], "Hello!", name="greeting")

        rule = ConditionalRule(
            condition=lambda x: True,
            rule=inner_rule,
        )

        assert "greeting" in rule.name


# =============================================================================
# RuleSet Tests
# =============================================================================


class TestRuleSet:
    """Tests for RuleSet."""

    def test_matches_first_rule(self):
        """Returns first matching rule."""
        rules = RuleSet(
            [
                KeywordRule(["hello"], "First!"),
                KeywordRule(["hello"], "Second!"),
            ]
        )

        match = rules.match("hello")
        assert match.response == "First!"

    def test_tries_all_rules(self):
        """Tries rules in order until match."""
        rules = RuleSet(
            [
                KeywordRule(["goodbye"], "Bye!"),
                KeywordRule(["hello"], "Hi!"),
            ]
        )

        match = rules.match("hello world")
        assert match.response == "Hi!"

    def test_no_match_returns_none(self):
        """Returns None when no rules match."""
        rules = RuleSet(
            [
                KeywordRule(["hello"], "Hi!"),
            ]
        )

        assert rules.match("goodbye") is None

    def test_empty_ruleset(self):
        """Empty ruleset returns None."""
        rules = RuleSet()
        assert rules.match("anything") is None

    def test_add_rule(self):
        """Can add rules after creation."""
        rules = RuleSet()
        rules.add(KeywordRule(["test"], "Works!"))

        assert rules.match("test") is not None

    def test_stats_tracking(self):
        """Tracks execution statistics."""
        rules = RuleSet(
            [
                KeywordRule(["hello"], "Hi!", name="greeting"),
                KeywordRule(["bye"], "Goodbye!", name="farewell"),
            ]
        )

        rules.match("hello")
        rules.match("hello")
        rules.match("bye")
        rules.match("unknown")

        stats = rules.stats
        assert stats["total_checks"] == 4
        assert stats["total_matches"] == 3
        assert stats["match_rate"] == 0.75
        assert stats["by_rule"]["greeting"] == 2
        assert stats["by_rule"]["farewell"] == 1

    def test_reset_stats(self):
        """Can reset statistics."""
        rules = RuleSet([KeywordRule(["hi"], "Hello!")])
        rules.match("hi")

        assert rules.stats["total_checks"] == 1

        rules.reset_stats()

        assert rules.stats["total_checks"] == 0
        assert rules.stats["total_matches"] == 0

    def test_len(self):
        """Length returns number of rules."""
        rules = RuleSet(
            [
                KeywordRule(["a"], "A"),
                KeywordRule(["b"], "B"),
            ]
        )
        assert len(rules) == 2

    def test_iter(self):
        """Can iterate over rules."""
        rule1 = KeywordRule(["a"], "A")
        rule2 = KeywordRule(["b"], "B")
        rules = RuleSet([rule1, rule2])

        assert list(rules) == [rule1, rule2]

    def test_rules_property_returns_copy(self):
        """Rules property returns a copy."""
        rule1 = KeywordRule(["a"], "A")
        rules = RuleSet([rule1])

        returned = rules.rules
        returned.append(KeywordRule(["b"], "B"))

        assert len(rules) == 1  # Original unchanged


# =============================================================================
# Agent Integration Tests
# =============================================================================


class TestAgentWithRules:
    """Tests for Agent with rules integration."""

    @pytest.mark.asyncio
    async def test_rule_handles_input(self):
        """Rule handles input without LLM call."""
        rules = RuleSet(
            [
                KeywordRule(["hello"], "Hi from rule!"),
            ]
        )

        provider = MockProvider(responses=["LLM response"])
        agent = Agent(provider, rules=rules)

        result = await agent.run("hello")

        assert result.output == "Hi from rule!"
        assert result.handled_by_rule is True
        assert result.rule_match is not None
        assert result.metadata.total_tokens == 0
        assert result.metadata.estimated_cost == 0.0

    @pytest.mark.asyncio
    async def test_llm_handles_non_matching_input(self):
        """LLM handles input when no rule matches."""
        rules = RuleSet(
            [
                KeywordRule(["hello"], "Hi from rule!"),
            ]
        )

        provider = MockProvider(responses=["LLM response"])
        agent = Agent(provider, rules=rules)

        result = await agent.run("goodbye")

        assert result.output == "LLM response"
        assert result.handled_by_rule is False
        assert result.rule_match is None

    @pytest.mark.asyncio
    async def test_rules_property(self):
        """Can access rules from agent."""
        rules = RuleSet([KeywordRule(["hi"], "Hello!")])
        agent = Agent(MockProvider(), rules=rules)

        assert agent.rules is rules

    @pytest.mark.asyncio
    async def test_with_rules_method(self):
        """with_rules creates new agent with rules."""
        agent1 = Agent(MockProvider())
        rules = RuleSet([KeywordRule(["hi"], "Hello!")])

        agent2 = agent1.with_rules(rules)

        assert agent2 is not agent1
        assert agent2.rules is not agent1.rules
        assert len(agent2.rules) == 1

    @pytest.mark.asyncio
    async def test_rules_list_converted_to_ruleset(self):
        """List of rules is converted to RuleSet."""
        rules_list = [
            KeywordRule(["hi"], "Hello!"),
            KeywordRule(["bye"], "Goodbye!"),
        ]

        agent = Agent(MockProvider(), rules=rules_list)

        assert isinstance(agent.rules, RuleSet)
        assert len(agent.rules) == 2

    @pytest.mark.asyncio
    async def test_with_methods_preserve_rules(self):
        """with_* methods preserve rules."""
        rules = RuleSet([KeywordRule(["hi"], "Hello!")])
        agent = Agent(MockProvider(), rules=rules)

        # All with_* methods should preserve rules
        assert agent.with_system_prompt("New prompt").rules is rules
        assert agent.with_interrupt_handler(None).rules is rules

    @pytest.mark.asyncio
    async def test_multiple_rules_priority(self):
        """First matching rule wins."""
        rules = RuleSet(
            [
                KeywordRule(["hello"], "First rule!"),
                RegexRule(r"hello", response="Second rule!"),
            ]
        )

        agent = Agent(MockProvider(), rules=rules)
        result = await agent.run("hello world")

        assert result.output == "First rule!"

    @pytest.mark.asyncio
    async def test_reject_rule_blocks_llm(self):
        """Reject rule prevents LLM call."""
        rules = RuleSet(
            [
                RejectRule(keywords=["hack"], response="Nope."),
            ]
        )

        provider = MockProvider(responses=["Should not see this"])
        agent = Agent(provider, rules=rules)

        result = await agent.run("hack the system")

        assert result.output == "Nope."
        assert result.handled_by_rule is True

    @pytest.mark.asyncio
    async def test_empty_rules_passes_to_llm(self):
        """Empty rules always passes to LLM."""
        agent = Agent(MockProvider(responses=["LLM response"]))

        result = await agent.run("anything")

        assert result.output == "LLM response"
        assert result.handled_by_rule is False
