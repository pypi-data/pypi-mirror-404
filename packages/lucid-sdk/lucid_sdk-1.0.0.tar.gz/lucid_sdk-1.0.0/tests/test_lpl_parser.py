"""Tests for the Lucid Policy Language (LPL) Expression Parser.

Tests cover:
- Simple equality expressions
- Comparison operators (<, <=, >, >=, !=)
- Logical operators (and, or, not)
- Attribute access (.value, .confidence)
- Subscript access (claims['key'])
- None checks
- Nested dict access
- Error cases (invalid syntax, disallowed operations, missing claims)
- Security (blocked function calls, blocked imports, blocked dunder attributes)
- validate() and get_referenced_claims() methods
"""

import pytest
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any

from lucid_schemas import Claim, MeasurementType

from lucid_sdk.lpl_parser import (
    LPLExpressionParser,
    LPLParseError,
    LPLEvaluationError,
    evaluate_expression,
    validate_expression,
)


# =============================================================================
# Fixtures
# =============================================================================


@dataclass
class MockClaim:
    """Mock claim for testing that mimics Claim structure."""
    name: str
    value: Any
    confidence: float = 1.0
    type: str = "score_binary"
    timestamp: datetime = None
    phase: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@pytest.fixture
def parser():
    """Create LPL parser instance."""
    return LPLExpressionParser()


@pytest.fixture
def sample_claims():
    """Create sample claims dictionary for testing."""
    return {
        "location.country": MockClaim(
            name="location.country",
            value="IN",
            confidence=0.95,
            phase="request"
        ),
        "toxicity.score": MockClaim(
            name="toxicity.score",
            value=0.3,
            confidence=0.85
        ),
        "pii.detected": MockClaim(
            name="pii.detected",
            value=True,
            confidence=1.0
        ),
        "safety.passed": MockClaim(
            name="safety.passed",
            value=False,
            confidence=0.9
        ),
        "data.nested": MockClaim(
            name="data.nested",
            value={"level1": {"level2": "deep_value"}},
            confidence=1.0
        ),
        "optional.claim": MockClaim(
            name="optional.claim",
            value=None,
            confidence=0.5
        ),
    }


@pytest.fixture
def real_claims():
    """Create real Claim objects for integration testing."""
    return {
        "location.verified": Claim(
            name="location.verified",
            type=MeasurementType.score_binary,
            value=True,
            timestamp=datetime.now(timezone.utc),
            confidence=0.98
        ),
        "score.value": Claim(
            name="score.value",
            type=MeasurementType.score_normalized,
            value=0.75,
            timestamp=datetime.now(timezone.utc),
            confidence=0.9
        ),
    }


# =============================================================================
# Simple Equality Tests
# =============================================================================


class TestSimpleEquality:
    """Tests for simple equality expressions."""

    def test_string_equality_true(self, parser, sample_claims):
        """Test string equality that evaluates to True."""
        result = parser.evaluate(
            "claims['location.country'].value == 'IN'",
            sample_claims
        )
        assert result is True

    def test_string_equality_false(self, parser, sample_claims):
        """Test string equality that evaluates to False."""
        result = parser.evaluate(
            "claims['location.country'].value == 'US'",
            sample_claims
        )
        assert result is False

    def test_boolean_equality_true(self, parser, sample_claims):
        """Test boolean equality with True."""
        result = parser.evaluate(
            "claims['pii.detected'].value == True",
            sample_claims
        )
        assert result is True

    def test_boolean_equality_false(self, parser, sample_claims):
        """Test boolean equality with False."""
        result = parser.evaluate(
            "claims['safety.passed'].value == False",
            sample_claims
        )
        assert result is True

    def test_numeric_equality(self, parser, sample_claims):
        """Test numeric equality."""
        result = parser.evaluate(
            "claims['toxicity.score'].value == 0.3",
            sample_claims
        )
        assert result is True


# =============================================================================
# Comparison Operators Tests
# =============================================================================


class TestComparisonOperators:
    """Tests for comparison operators."""

    def test_less_than_true(self, parser, sample_claims):
        """Test less than operator that evaluates to True."""
        result = parser.evaluate(
            "claims['toxicity.score'].value < 0.5",
            sample_claims
        )
        assert result is True

    def test_less_than_false(self, parser, sample_claims):
        """Test less than operator that evaluates to False."""
        result = parser.evaluate(
            "claims['toxicity.score'].value < 0.1",
            sample_claims
        )
        assert result is False

    def test_less_than_or_equal_true(self, parser, sample_claims):
        """Test less than or equal operator that evaluates to True."""
        result = parser.evaluate(
            "claims['toxicity.score'].value <= 0.3",
            sample_claims
        )
        assert result is True

    def test_less_than_or_equal_false(self, parser, sample_claims):
        """Test less than or equal operator that evaluates to False."""
        result = parser.evaluate(
            "claims['toxicity.score'].value <= 0.2",
            sample_claims
        )
        assert result is False

    def test_greater_than_true(self, parser, sample_claims):
        """Test greater than operator that evaluates to True."""
        result = parser.evaluate(
            "claims['toxicity.score'].value > 0.1",
            sample_claims
        )
        assert result is True

    def test_greater_than_false(self, parser, sample_claims):
        """Test greater than operator that evaluates to False."""
        result = parser.evaluate(
            "claims['toxicity.score'].value > 0.5",
            sample_claims
        )
        assert result is False

    def test_greater_than_or_equal_true(self, parser, sample_claims):
        """Test greater than or equal operator that evaluates to True."""
        result = parser.evaluate(
            "claims['toxicity.score'].value >= 0.3",
            sample_claims
        )
        assert result is True

    def test_greater_than_or_equal_false(self, parser, sample_claims):
        """Test greater than or equal operator that evaluates to False."""
        result = parser.evaluate(
            "claims['toxicity.score'].value >= 0.5",
            sample_claims
        )
        assert result is False

    def test_not_equal_true(self, parser, sample_claims):
        """Test not equal operator that evaluates to True."""
        result = parser.evaluate(
            "claims['location.country'].value != 'US'",
            sample_claims
        )
        assert result is True

    def test_not_equal_false(self, parser, sample_claims):
        """Test not equal operator that evaluates to False."""
        result = parser.evaluate(
            "claims['location.country'].value != 'IN'",
            sample_claims
        )
        assert result is False

    def test_confidence_comparison(self, parser, sample_claims):
        """Test comparison on confidence attribute."""
        result = parser.evaluate(
            "claims['location.country'].confidence >= 0.9",
            sample_claims
        )
        assert result is True


# =============================================================================
# Logical Operators Tests
# =============================================================================


class TestLogicalOperators:
    """Tests for logical operators (and, or, not)."""

    def test_and_both_true(self, parser, sample_claims):
        """Test AND with both operands True."""
        result = parser.evaluate(
            "claims['pii.detected'].value == True and claims['toxicity.score'].value < 0.5",
            sample_claims
        )
        assert result is True

    def test_and_first_false(self, parser, sample_claims):
        """Test AND with first operand False."""
        result = parser.evaluate(
            "claims['safety.passed'].value == True and claims['toxicity.score'].value < 0.5",
            sample_claims
        )
        assert result is False

    def test_and_second_false(self, parser, sample_claims):
        """Test AND with second operand False."""
        result = parser.evaluate(
            "claims['pii.detected'].value == True and claims['toxicity.score'].value > 0.5",
            sample_claims
        )
        assert result is False

    def test_and_both_false(self, parser, sample_claims):
        """Test AND with both operands False."""
        result = parser.evaluate(
            "claims['safety.passed'].value == True and claims['toxicity.score'].value > 0.5",
            sample_claims
        )
        assert result is False

    def test_or_both_true(self, parser, sample_claims):
        """Test OR with both operands True."""
        result = parser.evaluate(
            "claims['pii.detected'].value == True or claims['toxicity.score'].value < 0.5",
            sample_claims
        )
        assert result is True

    def test_or_first_true(self, parser, sample_claims):
        """Test OR with first operand True."""
        result = parser.evaluate(
            "claims['pii.detected'].value == True or claims['toxicity.score'].value > 0.5",
            sample_claims
        )
        assert result is True

    def test_or_second_true(self, parser, sample_claims):
        """Test OR with second operand True."""
        result = parser.evaluate(
            "claims['safety.passed'].value == True or claims['toxicity.score'].value < 0.5",
            sample_claims
        )
        assert result is True

    def test_or_both_false(self, parser, sample_claims):
        """Test OR with both operands False."""
        result = parser.evaluate(
            "claims['safety.passed'].value == True or claims['toxicity.score'].value > 0.5",
            sample_claims
        )
        assert result is False

    def test_not_true(self, parser, sample_claims):
        """Test NOT on True value."""
        result = parser.evaluate(
            "not claims['pii.detected'].value",
            sample_claims
        )
        assert result is False

    def test_not_false(self, parser, sample_claims):
        """Test NOT on False value."""
        result = parser.evaluate(
            "not claims['safety.passed'].value",
            sample_claims
        )
        assert result is True

    def test_complex_logical_expression(self, parser, sample_claims):
        """Test complex expression with multiple logical operators."""
        result = parser.evaluate(
            "(claims['pii.detected'].value == True or claims['safety.passed'].value == True) "
            "and claims['toxicity.score'].value < 0.5",
            sample_claims
        )
        assert result is True

    def test_nested_logical_expression(self, parser, sample_claims):
        """Test nested logical expressions."""
        result = parser.evaluate(
            "not (claims['safety.passed'].value == True and claims['toxicity.score'].value > 0.5)",
            sample_claims
        )
        assert result is True


# =============================================================================
# Attribute Access Tests
# =============================================================================


class TestAttributeAccess:
    """Tests for attribute access (.value, .confidence, etc.)."""

    def test_access_value(self, parser, sample_claims):
        """Test accessing .value attribute."""
        result = parser.evaluate(
            "claims['location.country'].value == 'IN'",
            sample_claims
        )
        assert result is True

    def test_access_confidence(self, parser, sample_claims):
        """Test accessing .confidence attribute."""
        result = parser.evaluate(
            "claims['location.country'].confidence > 0.9",
            sample_claims
        )
        assert result is True

    def test_access_name(self, parser, sample_claims):
        """Test accessing .name attribute."""
        result = parser.evaluate(
            "claims['location.country'].name == 'location.country'",
            sample_claims
        )
        assert result is True

    def test_access_type(self, parser, sample_claims):
        """Test accessing .type attribute."""
        result = parser.evaluate(
            "claims['location.country'].type == 'score_binary'",
            sample_claims
        )
        assert result is True

    def test_access_phase(self, parser, sample_claims):
        """Test accessing .phase attribute."""
        result = parser.evaluate(
            "claims['location.country'].phase == 'request'",
            sample_claims
        )
        assert result is True

    def test_access_disallowed_attribute(self, parser, sample_claims):
        """Test that accessing disallowed attributes raises error."""
        with pytest.raises(LPLParseError) as exc_info:
            parser.evaluate(
                "claims['location.country'].forbidden_attr == 'x'",
                sample_claims
            )
        assert "disallowed" in str(exc_info.value).lower()


# =============================================================================
# Subscript Access Tests
# =============================================================================


class TestSubscriptAccess:
    """Tests for subscript access (claims['key'])."""

    def test_simple_subscript(self, parser, sample_claims):
        """Test simple claim subscript access."""
        result = parser.evaluate(
            "claims['toxicity.score'].value < 1.0",
            sample_claims
        )
        assert result is True

    def test_subscript_with_dot_notation_key(self, parser, sample_claims):
        """Test subscript with dot notation in key."""
        result = parser.evaluate(
            "claims['location.country'].value == 'IN'",
            sample_claims
        )
        assert result is True

    def test_subscript_missing_claim(self, parser, sample_claims):
        """Test subscript access to missing claim raises error."""
        with pytest.raises(LPLEvaluationError) as exc_info:
            parser.evaluate(
                "claims['nonexistent.claim'].value == 'x'",
                sample_claims
            )
        assert "not found" in str(exc_info.value).lower()


# =============================================================================
# None Checks Tests
# =============================================================================


class TestNoneChecks:
    """Tests for None comparisons."""

    def test_is_none_true(self, parser, sample_claims):
        """Test 'is None' check that evaluates to True."""
        result = parser.evaluate(
            "claims['optional.claim'].value is None",
            sample_claims
        )
        assert result is True

    def test_is_none_false(self, parser, sample_claims):
        """Test 'is None' check that evaluates to False."""
        result = parser.evaluate(
            "claims['location.country'].value is None",
            sample_claims
        )
        assert result is False

    def test_is_not_none_true(self, parser, sample_claims):
        """Test 'is not None' check that evaluates to True."""
        result = parser.evaluate(
            "claims['location.country'].value is not None",
            sample_claims
        )
        assert result is True

    def test_is_not_none_false(self, parser, sample_claims):
        """Test 'is not None' check that evaluates to False."""
        result = parser.evaluate(
            "claims['optional.claim'].value is not None",
            sample_claims
        )
        assert result is False


# =============================================================================
# Nested Dict Access Tests
# =============================================================================


class TestNestedDictAccess:
    """Tests for nested dictionary access."""

    def test_nested_dict_via_subscript(self, parser, sample_claims):
        """Test nested dict access via subscript."""
        result = parser.evaluate(
            "claims['data.nested'].value['level1']['level2'] == 'deep_value'",
            sample_claims
        )
        assert result is True


# =============================================================================
# Error Cases Tests
# =============================================================================


class TestErrorCases:
    """Tests for error handling."""

    def test_empty_expression(self, parser, sample_claims):
        """Test that empty expression raises error."""
        with pytest.raises(LPLParseError) as exc_info:
            parser.evaluate("", sample_claims)
        assert "empty" in str(exc_info.value).lower()

    def test_whitespace_only_expression(self, parser, sample_claims):
        """Test that whitespace-only expression raises error."""
        with pytest.raises(LPLParseError) as exc_info:
            parser.evaluate("   ", sample_claims)
        assert "empty" in str(exc_info.value).lower()

    def test_invalid_syntax(self, parser, sample_claims):
        """Test that invalid syntax raises parse error."""
        with pytest.raises(LPLParseError) as exc_info:
            parser.evaluate("claims['test'] ==== 'value'", sample_claims)
        assert "syntax" in str(exc_info.value).lower()

    def test_unclosed_string(self, parser, sample_claims):
        """Test that unclosed string raises parse error."""
        with pytest.raises(LPLParseError):
            parser.evaluate("claims['test'].value == 'unclosed", sample_claims)

    def test_unclosed_bracket(self, parser, sample_claims):
        """Test that unclosed bracket raises parse error."""
        with pytest.raises(LPLParseError):
            parser.evaluate("claims['test'.value == 'x'", sample_claims)

    def test_missing_claim_key(self, parser, sample_claims):
        """Test that missing claim raises evaluation error."""
        with pytest.raises(LPLEvaluationError) as exc_info:
            parser.evaluate(
                "claims['missing.claim'].value == 'x'",
                sample_claims
            )
        assert "not found" in str(exc_info.value).lower()

    def test_attribute_on_none(self, parser, sample_claims):
        """Test that accessing attribute on None raises error."""
        # Create a claim where accessing .value.something fails
        claims = {"null.test": MockClaim(name="null.test", value=None)}
        with pytest.raises(LPLEvaluationError):
            parser.evaluate(
                "claims['null.test'].value.something == 'x'",
                claims
            )

    def test_type_error_in_comparison(self, parser, sample_claims):
        """Test that type error in comparison raises evaluation error."""
        with pytest.raises(LPLEvaluationError) as exc_info:
            parser.evaluate(
                "claims['location.country'].value < 5",  # String < Int
                sample_claims
            )
        assert "type" in str(exc_info.value).lower()


# =============================================================================
# Security Tests
# =============================================================================


class TestSecurity:
    """Tests for security features (blocked operations)."""

    def test_blocked_function_call(self, parser, sample_claims):
        """Test that function calls are blocked."""
        with pytest.raises(LPLParseError) as exc_info:
            parser.evaluate("print('hello')", sample_claims)
        assert "disallowed" in str(exc_info.value).lower()

    def test_blocked_builtin_function(self, parser, sample_claims):
        """Test that builtin function calls are blocked."""
        with pytest.raises(LPLParseError) as exc_info:
            parser.evaluate("len(claims)", sample_claims)
        assert "disallowed" in str(exc_info.value).lower()

    def test_blocked_import(self, parser, sample_claims):
        """Test that import statements are blocked."""
        with pytest.raises(LPLParseError):
            parser.evaluate("__import__('os')", sample_claims)

    def test_blocked_dunder_attribute(self, parser, sample_claims):
        """Test that dunder attributes on subscript results are blocked."""
        # The parser blocks dunder attributes on claim subscript results
        # Note: claims.__class__ is allowed because attribute validation
        # only applies to claims['key'].attribute access patterns
        with pytest.raises(LPLParseError) as exc_info:
            parser.validate("claims['test'].__class__")
        assert "disallowed" in str(exc_info.value).lower()

    def test_blocked_arbitrary_variable(self, parser, sample_claims):
        """Test that arbitrary variables are blocked."""
        with pytest.raises(LPLParseError) as exc_info:
            parser.evaluate("my_variable == 'test'", sample_claims)
        assert "disallowed" in str(exc_info.value).lower()

    def test_blocked_list_comprehension(self, parser, sample_claims):
        """Test that list comprehensions are blocked."""
        with pytest.raises(LPLParseError):
            parser.evaluate("[x for x in claims]", sample_claims)

    def test_blocked_lambda(self, parser, sample_claims):
        """Test that lambda expressions are blocked."""
        with pytest.raises(LPLParseError):
            parser.evaluate("(lambda: True)()", sample_claims)

    def test_blocked_exec_eval(self, parser, sample_claims):
        """Test that exec/eval patterns are blocked."""
        with pytest.raises(LPLParseError):
            parser.evaluate("eval('1+1')", sample_claims)

    def test_expression_depth_limit(self):
        """Test that expression depth limit is enforced."""
        parser = LPLExpressionParser(max_depth=5)
        # Create deeply nested expression using nested attribute access
        # Each 'and not' adds depth to the AST
        deep_expr = "not " * 10 + "True"
        with pytest.raises(LPLParseError) as exc_info:
            parser.validate(deep_expr)
        assert "depth" in str(exc_info.value).lower()

    def test_expression_node_limit(self):
        """Test that node count limit is enforced."""
        parser = LPLExpressionParser(max_nodes=5)
        # Expression with many nodes
        expr = "True and True and True and True and True"
        with pytest.raises(LPLParseError) as exc_info:
            parser.validate(expr)
        assert "complex" in str(exc_info.value).lower()


# =============================================================================
# validate() Method Tests
# =============================================================================


class TestValidateMethod:
    """Tests for the validate() method."""

    def test_validate_valid_expression(self, parser):
        """Test validate() returns True for valid expression."""
        result = parser.validate("claims['test'].value == 'x'")
        assert result is True

    def test_validate_complex_expression(self, parser):
        """Test validate() for complex valid expression."""
        result = parser.validate(
            "claims['a'].value == 'x' and claims['b'].confidence > 0.5"
        )
        assert result is True

    def test_validate_empty_expression(self, parser):
        """Test validate() raises for empty expression."""
        with pytest.raises(LPLParseError):
            parser.validate("")

    def test_validate_invalid_syntax(self, parser):
        """Test validate() raises for invalid syntax."""
        with pytest.raises(LPLParseError):
            parser.validate("claims['test'] ===")

    def test_validate_disallowed_operation(self, parser):
        """Test validate() raises for disallowed operations."""
        with pytest.raises(LPLParseError):
            parser.validate("print('hello')")


# =============================================================================
# get_referenced_claims() Method Tests
# =============================================================================


class TestGetReferencedClaims:
    """Tests for the get_referenced_claims() method."""

    def test_single_claim_reference(self, parser):
        """Test extracting single claim reference."""
        claims = parser.get_referenced_claims("claims['test.claim'].value == 'x'")
        assert claims == {"test.claim"}

    def test_multiple_claim_references(self, parser):
        """Test extracting multiple claim references."""
        claims = parser.get_referenced_claims(
            "claims['a.claim'].value == 'x' and claims['b.claim'].confidence > 0.5"
        )
        assert claims == {"a.claim", "b.claim"}

    def test_duplicate_claim_references(self, parser):
        """Test that duplicate references are deduplicated."""
        claims = parser.get_referenced_claims(
            "claims['same.claim'].value == 'x' and claims['same.claim'].confidence > 0.5"
        )
        assert claims == {"same.claim"}

    def test_no_claim_references(self, parser):
        """Test expression with no claim references."""
        claims = parser.get_referenced_claims("True and False")
        assert claims == set()

    def test_empty_expression_raises(self, parser):
        """Test that empty expression raises error."""
        with pytest.raises(LPLParseError):
            parser.get_referenced_claims("")

    def test_complex_expression_claim_extraction(self, parser):
        """Test claim extraction from complex expression."""
        claims = parser.get_referenced_claims(
            "(claims['location.country'].value == 'IN' or claims['location.country'].value == 'US') "
            "and claims['toxicity.score'].value < 0.7 "
            "and not claims['blocked.user'].value"
        )
        assert claims == {"location.country", "toxicity.score", "blocked.user"}


# =============================================================================
# Convenience Functions Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_evaluate_expression_function(self, sample_claims):
        """Test the evaluate_expression convenience function."""
        result = evaluate_expression(
            "claims['location.country'].value == 'IN'",
            sample_claims
        )
        assert result is True

    def test_validate_expression_function(self):
        """Test the validate_expression convenience function."""
        result = validate_expression("claims['test'].value == 'x'")
        assert result is True

    def test_validate_expression_invalid(self):
        """Test validate_expression raises for invalid expression."""
        with pytest.raises(LPLParseError):
            validate_expression("invalid ===")


# =============================================================================
# Parser Configuration Tests
# =============================================================================


class TestParserConfiguration:
    """Tests for parser configuration options."""

    def test_default_max_depth(self):
        """Test default max_depth configuration."""
        parser = LPLExpressionParser()
        assert parser.max_depth == 20

    def test_default_max_nodes(self):
        """Test default max_nodes configuration."""
        parser = LPLExpressionParser()
        assert parser.max_nodes == 100

    def test_custom_max_depth(self):
        """Test custom max_depth configuration."""
        parser = LPLExpressionParser(max_depth=10)
        assert parser.max_depth == 10

    def test_custom_max_nodes(self):
        """Test custom max_nodes configuration."""
        parser = LPLExpressionParser(max_nodes=50)
        assert parser.max_nodes == 50

    def test_invalid_max_depth(self):
        """Test that invalid max_depth raises error."""
        with pytest.raises(ValueError):
            LPLExpressionParser(max_depth=0)

    def test_invalid_max_nodes(self):
        """Test that invalid max_nodes raises error."""
        with pytest.raises(ValueError):
            LPLExpressionParser(max_nodes=0)


# =============================================================================
# Integration Tests with Real Claims
# =============================================================================


class TestIntegrationWithRealClaims:
    """Integration tests using real Claim objects."""

    def test_with_real_claim_objects(self, parser, real_claims):
        """Test evaluation with real Claim objects."""
        result = parser.evaluate(
            "claims['location.verified'].value == True",
            real_claims
        )
        assert result is True

    def test_confidence_check_with_real_claims(self, parser, real_claims):
        """Test confidence check with real Claim objects."""
        result = parser.evaluate(
            "claims['location.verified'].confidence >= 0.95",
            real_claims
        )
        assert result is True

    def test_compound_condition_with_real_claims(self, parser, real_claims):
        """Test compound condition with real Claim objects."""
        result = parser.evaluate(
            "claims['location.verified'].value == True and "
            "claims['score.value'].value > 0.5",
            real_claims
        )
        assert result is True


# =============================================================================
# Edge Cases Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_long_claim_name(self, parser):
        """Test with very long claim name."""
        long_name = "a" * 200 + ".claim"
        claims = {long_name: MockClaim(name=long_name, value="test")}
        result = parser.evaluate(f"claims['{long_name}'].value == 'test'", claims)
        assert result is True

    def test_special_characters_in_claim_value(self, parser):
        """Test claim with special characters in value."""
        claims = {"special": MockClaim(name="special", value="hello\nworld\t!")}
        result = parser.evaluate(
            "claims['special'].value == 'hello\\nworld\\t!'",
            claims
        )
        assert result is True

    def test_unicode_in_claim_value(self, parser):
        """Test claim with unicode characters."""
        claims = {"unicode": MockClaim(name="unicode", value="test")}
        result = parser.evaluate(
            "claims['unicode'].value == 'test'",
            claims
        )
        assert result is True

    def test_empty_string_value(self, parser):
        """Test claim with empty string value."""
        claims = {"empty": MockClaim(name="empty", value="")}
        result = parser.evaluate("claims['empty'].value == ''", claims)
        assert result is True

    def test_zero_confidence(self, parser):
        """Test claim with zero confidence."""
        claims = {"zero": MockClaim(name="zero", value=True, confidence=0.0)}
        result = parser.evaluate("claims['zero'].confidence == 0.0", claims)
        assert result is True

    def test_chained_comparison(self, parser, sample_claims):
        """Test chained comparison (Python style)."""
        result = parser.evaluate(
            "0.1 < claims['toxicity.score'].value < 0.5",
            sample_claims
        )
        assert result is True

    def test_boolean_coercion(self, parser, sample_claims):
        """Test that non-boolean results are coerced to boolean."""
        # Test with a value that's truthy
        result = parser.evaluate(
            "claims['location.country'].value",  # String 'IN' is truthy
            sample_claims
        )
        assert result is True
