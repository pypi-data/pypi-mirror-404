"""Automation-First Rules for Tantra.

Provides rule-based handling that executes before the LLM,
saving costs by handling common/predictable requests instantly.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class RuleMatch:
    """Result of a successful rule match.

    Attributes:
        response: The response text to return to the user.
        rule_name: Name of the rule that matched.
        confidence: Match confidence between 0.0 and 1.0 (default 1.0).
        metadata: Optional extra data about the match (e.g. matched key, groups).
    """

    response: str
    rule_name: str
    confidence: float = 1.0
    metadata: dict[str, Any] | None = None


class Rule(ABC):
    """Base class for automation rules.

    Rules are checked before the LLM is called. If a rule matches,
    its response is returned immediately without any LLM cost.

    Examples:
        ```python
        class GreetingRule(Rule):
            def match(self, user_input: str) -> RuleMatch | None:
                if user_input.lower().strip() in ["hi", "hello", "hey"]:
                    return RuleMatch(
                        response="Hello! How can I help you today?",
                        rule_name="greeting",
                    )
                return None
        ```
    """

    @abstractmethod
    def match(self, user_input: str) -> RuleMatch | None:
        """Check if this rule matches the input.

        Args:
            user_input: The user's input string.

        Returns:
            RuleMatch if the rule handles this input, None otherwise.
        """
        pass

    @property
    def name(self) -> str:
        """Rule name for logging/metrics."""
        return self.__class__.__name__


class KeywordRule(Rule):
    """Match based on keywords in the input.

    Examples:
        ```python
        rule = KeywordRule(
            keywords=["hours", "open", "when open"],
            response="We're open Monday-Friday, 9am-5pm EST.",
            name="business_hours",
        )
        ```
    """

    def __init__(
        self,
        keywords: list[str],
        response: str,
        name: str | None = None,
        case_sensitive: bool = False,
        match_all: bool = False,
    ):
        """Initialize keyword rule.

        Args:
            keywords: List of keywords to match.
            response: Response to return when matched.
            name: Optional rule name.
            case_sensitive: Whether matching is case-sensitive.
            match_all: If True, ALL keywords must be present.
        """
        self.keywords = keywords
        self.response = response
        self._name = name or "keyword_rule"
        self.case_sensitive = case_sensitive
        self.match_all = match_all

    @property
    def name(self) -> str:
        return self._name

    def match(self, user_input: str) -> RuleMatch | None:
        """Check if any keyword (or all keywords if ``match_all``) appears in the input."""
        check_input = user_input if self.case_sensitive else user_input.lower()
        check_keywords = (
            self.keywords if self.case_sensitive else [k.lower() for k in self.keywords]
        )

        if self.match_all:
            matched = all(kw in check_input for kw in check_keywords)
        else:
            matched = any(kw in check_input for kw in check_keywords)

        if matched:
            return RuleMatch(
                response=self.response,
                rule_name=self.name,
            )
        return None


class RegexRule(Rule):
    r"""Match based on regex pattern.

    The handler can be a string or a callable that receives the match object.

    Examples:
        ```python
        # Static response
        rule = RegexRule(
            pattern=r"order\s*#?\s*(\d+)",
            response="Let me look up that order for you.",
        )

        # Dynamic response using match groups
        rule = RegexRule(
            pattern=r"order\s*#?\s*(\d+)",
            handler=lambda m: f"Order {m.group(1)} status: Shipped",
        )
        ```
    """

    def __init__(
        self,
        pattern: str | re.Pattern,
        response: str | None = None,
        handler: Callable[[re.Match], str] | None = None,
        name: str | None = None,
        flags: int = re.IGNORECASE,
    ):
        """Initialize regex rule.

        Args:
            pattern: Regex pattern to match.
            response: Static response string.
            handler: Function that takes Match and returns response.
            name: Optional rule name.
            flags: Regex flags (default: IGNORECASE).
        """
        if response is None and handler is None:
            raise ValueError("Must provide either response or handler")

        self.pattern = re.compile(pattern, flags) if isinstance(pattern, str) else pattern
        self.response = response
        self.handler = handler
        self._name = name or "regex_rule"

    @property
    def name(self) -> str:
        return self._name

    def match(self, user_input: str) -> RuleMatch | None:
        """Search for the regex pattern in the input; use handler or static response."""
        m = self.pattern.search(user_input)
        if m:
            if self.handler:
                response = self.handler(m)
            else:
                response = self.response

            return RuleMatch(
                response=response,
                rule_name=self.name,
                metadata={"groups": m.groups(), "match": m.group(0)},
            )
        return None


class LookupRule(Rule):
    """Match against a lookup table.

    Useful for FAQs and common questions.

    Examples:
        ```python
        rule = LookupRule({
            "return policy": "You can return items within 30 days.",
            "shipping": "Free shipping on orders over $50.",
            "contact": "Email support@example.com",
        })
        ```
    """

    def __init__(
        self,
        lookup: dict[str, str],
        name: str | None = None,
        case_sensitive: bool = False,
        fuzzy: bool = False,
        threshold: float = 0.8,
    ):
        """Initialize lookup rule.

        Args:
            lookup: Dict mapping keys to responses.
            name: Optional rule name.
            case_sensitive: Whether matching is case-sensitive.
            fuzzy: Whether to use fuzzy matching (substring).
            threshold: Minimum match ratio for fuzzy matching.
        """
        self.lookup = lookup
        self._name = name or "lookup_rule"
        self.case_sensitive = case_sensitive
        self.fuzzy = fuzzy
        self.threshold = threshold

    @property
    def name(self) -> str:
        return self._name

    def match(self, user_input: str) -> RuleMatch | None:
        """Look up the input in the table, with optional fuzzy substring matching."""
        check_input = user_input if self.case_sensitive else user_input.lower()

        # Exact match first
        for key, response in self.lookup.items():
            check_key = key if self.case_sensitive else key.lower()

            if check_key == check_input or check_key in check_input:
                return RuleMatch(
                    response=response,
                    rule_name=self.name,
                    metadata={"matched_key": key},
                )

        # Fuzzy match if enabled
        if self.fuzzy:
            for key, response in self.lookup.items():
                check_key = key if self.case_sensitive else key.lower()
                # Simple substring ratio
                if len(check_key) > 3 and check_key in check_input:
                    return RuleMatch(
                        response=response,
                        rule_name=self.name,
                        confidence=0.8,
                        metadata={"matched_key": key, "fuzzy": True},
                    )

        return None


class FunctionRule(Rule):
    """Custom rule using a function.

    Maximum flexibility for complex matching logic.

    Examples:
        ```python
        def check_greeting(user_input: str) -> str | None:
            greetings = ["hi", "hello", "hey", "good morning"]
            if user_input.lower().strip() in greetings:
                return "Hello! How can I help you?"
            return None

        rule = FunctionRule(check_greeting, name="greeting")
        ```
    """

    def __init__(
        self,
        func: Callable[[str], str | None],
        name: str | None = None,
    ):
        """Initialize function rule.

        Args:
            func: Function that takes input and returns response or None.
            name: Optional rule name.
        """
        self.func = func
        self._name = name or func.__name__ or "function_rule"

    @property
    def name(self) -> str:
        return self._name

    def match(self, user_input: str) -> RuleMatch | None:
        """Call the custom function; wrap its return value as a RuleMatch."""
        result = self.func(user_input)
        if result is not None:
            return RuleMatch(
                response=result,
                rule_name=self.name,
            )
        return None


class RejectRule(Rule):
    """Reject certain inputs without calling the LLM.

    Useful for blocking inappropriate content or out-of-scope requests.

    Examples:
        ```python
        rule = RejectRule(
            patterns=[r"hack", r"exploit", r"bypass"],
            response="I can't help with that request.",
        )
        ```
    """

    def __init__(
        self,
        patterns: list[str] | None = None,
        keywords: list[str] | None = None,
        response: str = "I'm not able to help with that request.",
        name: str | None = None,
    ):
        """Initialize reject rule.

        Args:
            patterns: Regex patterns to reject.
            keywords: Keywords to reject.
            response: Response when rejecting.
            name: Optional rule name.
        """
        self.patterns = [re.compile(p, re.IGNORECASE) for p in (patterns or [])]
        self.keywords = [k.lower() for k in (keywords or [])]
        self.response = response
        self._name = name or "reject_rule"

    @property
    def name(self) -> str:
        return self._name

    def match(self, user_input: str) -> RuleMatch | None:
        """Reject input if any keyword or regex pattern matches."""
        input_lower = user_input.lower()

        # Check keywords
        for kw in self.keywords:
            if kw in input_lower:
                return RuleMatch(
                    response=self.response,
                    rule_name=self.name,
                    metadata={"rejected_by": "keyword", "match": kw},
                )

        # Check patterns
        for pattern in self.patterns:
            if pattern.search(user_input):
                return RuleMatch(
                    response=self.response,
                    rule_name=self.name,
                    metadata={"rejected_by": "pattern"},
                )

        return None


class ConditionalRule(Rule):
    """Apply a rule only when a condition is met.

    Examples:
        ```python
        rule = ConditionalRule(
            condition=lambda x: len(x) < 10,
            rule=KeywordRule(["hi"], "Hello!"),
        )
        ```
    """

    def __init__(
        self,
        condition: Callable[[str], bool],
        rule: Rule,
        name: str | None = None,
    ):
        """Initialize conditional rule.

        Args:
            condition: Function that returns True if rule should be checked.
            rule: The rule to apply if condition is met.
            name: Optional rule name.
        """
        self.condition = condition
        self.rule = rule
        self._name = name or f"conditional_{rule.name}"

    @property
    def name(self) -> str:
        return self._name

    def match(self, user_input: str) -> RuleMatch | None:
        """Delegate to the wrapped rule only when the condition function returns True."""
        if self.condition(user_input):
            return self.rule.match(user_input)
        return None


class RuleSet:
    r"""Collection of rules with execution tracking.

    Examples:
        ```python
        rules = RuleSet([
            KeywordRule(["hours"], "9am-5pm"),
            LookupRule(faqs),
            RegexRule(r"order #(\d+)", handler=lookup_order),
        ])

        result = rules.match("What are your hours?")
        if result:
            print(result.response)

        # Check stats
        print(rules.stats)
        ```
    """

    def __init__(self, rules: list[Rule] | None = None):
        """Initialize rule set.

        Args:
            rules: List of rules to include.
        """
        self._rules = list(rules) if rules else []
        self._stats = {
            "checks": 0,
            "matches": 0,
            "by_rule": {},
        }

    def add(self, rule: Rule) -> None:
        """Add a rule to the set.

        Args:
            rule: The rule to append.
        """
        self._rules.append(rule)

    def match(self, user_input: str) -> RuleMatch | None:
        """Check all rules and return first match.

        Args:
            user_input: The input to check.

        Returns:
            RuleMatch if any rule matches, None otherwise.
        """
        self._stats["checks"] += 1

        for rule in self._rules:
            result = rule.match(user_input)
            if result:
                self._stats["matches"] += 1
                self._stats["by_rule"][rule.name] = self._stats["by_rule"].get(rule.name, 0) + 1
                return result

        return None

    @property
    def rules(self) -> list[Rule]:
        """Get list of rules."""
        return self._rules.copy()

    @property
    def stats(self) -> dict[str, Any]:
        """Get execution statistics."""
        total = self._stats["checks"]
        matches = self._stats["matches"]
        return {
            "total_checks": total,
            "total_matches": matches,
            "match_rate": matches / total if total > 0 else 0,
            "by_rule": self._stats["by_rule"].copy(),
        }

    def reset_stats(self) -> None:
        """Reset execution statistics."""
        self._stats = {"checks": 0, "matches": 0, "by_rule": {}}

    def __len__(self) -> int:
        """Return the number of rules in this set."""
        return len(self._rules)

    def __iter__(self) -> iter:
        """Iterate over all Rule objects in this set."""
        return iter(self._rules)
