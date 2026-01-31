"""
Lucid Policy Language (LPL) Expression Parser

A secure expression parser for evaluating policy conditions against claim data.
Uses Python's ast module for safe parsing without eval/exec.

This module provides a way to define and evaluate policy conditions in a
human-readable format while maintaining security by only allowing whitelisted
operations.

Supported Expression Features:
    - Comparisons: ==, !=, <, <=, >, >=
    - Logical operators: and, or, not
    - Attribute access: .value, .confidence, .name, .type, .timestamp, .phase
    - Subscript access: claims['key']
    - None checks: is None, is not None
    - Parentheses for grouping: (a and b) or c

Security Features:
    - No eval() or exec() - uses AST-based evaluation
    - Whitelisted operations only
    - No function calls to arbitrary functions
    - No imports or module access
    - Expression complexity limits (depth and node count)
    - Type-safe comparisons

Example Usage:
    >>> from lucid_sdk.lpl_parser import LPLExpressionParser
    >>> from lucid_schemas import Claim, MeasurementType
    >>> from datetime import datetime, timezone
    >>>
    >>> parser = LPLExpressionParser()
    >>> claims = {
    ...     "location.country": Claim(
    ...         name="location.country",
    ...         type=MeasurementType.conformity,
    ...         value="IN",
    ...         timestamp=datetime.now(timezone.utc),
    ...         confidence=0.95
    ...     )
    ... }
    >>>
    >>> # Evaluate a simple condition
    >>> result = parser.evaluate("claims['location.country'].value == 'IN'", claims)
    >>> assert result == True
    >>>
    >>> # Evaluate confidence threshold
    >>> result = parser.evaluate("claims['location.country'].confidence >= 0.9", claims)
    >>> assert result == True
    >>>
    >>> # Compound conditions
    >>> result = parser.evaluate(
    ...     "claims['location.country'].value == 'IN' and "
    ...     "claims['location.country'].confidence >= 0.8",
    ...     claims
    ... )
    >>> assert result == True

Author: Lucid Team
"""

from __future__ import annotations

import ast
import operator
from datetime import datetime
from typing import Any, Dict, Optional, Set, Union

from .exceptions import LucidError


# =============================================================================
# Exception Classes
# =============================================================================


class LPLParseError(LucidError):
    """Exception raised when LPL expression parsing fails.

    This error indicates a syntax or structural problem with the expression
    that prevents it from being parsed.

    Attributes:
        expression: The expression that failed to parse.
        position: Character position where the error occurred (if available).
    """

    def __init__(
        self,
        message: str,
        expression: Optional[str] = None,
        position: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if expression:
            details["expression"] = expression
        if position is not None:
            details["position"] = position

        super().__init__(message, "LPL_PARSE_ERROR", details)
        self.expression = expression
        self.position = position


class LPLEvaluationError(LucidError):
    """Exception raised when LPL expression evaluation fails.

    This error indicates a runtime problem during expression evaluation,
    such as missing claims, type mismatches, or invalid operations.

    Attributes:
        expression: The expression that failed to evaluate.
        claim_name: Name of the claim that caused the error (if applicable).
    """

    def __init__(
        self,
        message: str,
        expression: Optional[str] = None,
        claim_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if expression:
            details["expression"] = expression
        if claim_name:
            details["claim_name"] = claim_name

        super().__init__(message, "LPL_EVALUATION_ERROR", details)
        self.expression = expression
        self.claim_name = claim_name


# =============================================================================
# LPL Expression Parser
# =============================================================================


class LPLExpressionParser:
    """Secure expression parser for Lucid Policy Language (LPL) conditions.

    This parser safely evaluates policy condition expressions by using Python's
    ast module to parse and walk the expression tree. It only allows a
    whitelisted set of operations, preventing code injection attacks.

    Security Model:
        - Expressions are parsed into an AST, not executed directly
        - Only specific AST node types are allowed (whitelisted)
        - Function calls are blocked (no arbitrary code execution)
        - Imports and module access are blocked
        - Expression complexity is limited to prevent DoS

    Supported Operations:
        - Binary comparisons: ==, !=, <, <=, >, >=
        - Logical operators: and, or, not
        - Attribute access on claims: .value, .confidence, .name, etc.
        - Dictionary subscript: claims['key']
        - None comparisons: is None, is not None
        - Parenthetical grouping

    Attributes:
        max_depth: Maximum AST depth allowed (default: 20).
        max_nodes: Maximum number of AST nodes allowed (default: 100).

    Example:
        >>> parser = LPLExpressionParser()
        >>> claims = {"country": Claim(name="country", value="US", ...)}
        >>> parser.evaluate("claims['country'].value == 'US'", claims)
        True

    Note:
        The 'claims' variable is automatically injected into the evaluation
        context. Expressions must reference claims using claims['name'] syntax.
    """

    # Whitelisted AST node types for safe evaluation
    ALLOWED_NODE_TYPES: Set[type] = {
        ast.Expression,  # Top-level expression wrapper
        ast.BoolOp,      # and, or
        ast.BinOp,       # Not used but safe (arithmetic if needed later)
        ast.UnaryOp,     # not, -, +
        ast.Compare,     # ==, !=, <, <=, >, >=, is, is not
        ast.Attribute,   # .value, .confidence, etc.
        ast.Subscript,   # claims['key']
        ast.Name,        # Variable names (claims, None, True, False)
        ast.Load,        # Load context
        ast.Constant,    # String, number, None, True, False literals
        ast.And,         # and operator
        ast.Or,          # or operator
        ast.Not,         # not operator
        ast.Eq,          # ==
        ast.NotEq,       # !=
        ast.Lt,          # <
        ast.LtE,         # <=
        ast.Gt,          # >
        ast.GtE,         # >=
        ast.Is,          # is
        ast.IsNot,       # is not
    }

    # Whitelisted attribute names for Claim objects
    ALLOWED_CLAIM_ATTRIBUTES: Set[str] = {
        "value",
        "confidence",
        "name",
        "type",
        "timestamp",
        "phase",
        "nonce",
        "compliance_framework",
        "control_id",
        "schema_version",
    }

    # Whitelisted variable names
    ALLOWED_NAMES: Set[str] = {
        "claims",
        "None",
        "True",
        "False",
    }

    # Comparison operators mapping
    COMPARISON_OPS: Dict[type, Any] = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
    }

    def __init__(
        self,
        max_depth: int = 20,
        max_nodes: int = 100
    ) -> None:
        """Initialize the LPL expression parser.

        Args:
            max_depth: Maximum allowed AST tree depth. Prevents deeply nested
                expressions that could cause stack overflow.
            max_nodes: Maximum allowed number of AST nodes. Prevents overly
                complex expressions that could cause DoS.

        Raises:
            ValueError: If max_depth or max_nodes is less than 1.
        """
        if max_depth < 1:
            raise ValueError("max_depth must be at least 1")
        if max_nodes < 1:
            raise ValueError("max_nodes must be at least 1")

        self.max_depth = max_depth
        self.max_nodes = max_nodes

    def evaluate(
        self,
        expression: str,
        claims: Dict[str, Any]
    ) -> bool:
        """Evaluate an LPL expression against a set of claims.

        Parses the expression into an AST, validates it for security, and
        then evaluates it against the provided claims dictionary.

        Args:
            expression: The LPL expression string to evaluate.
                Must be a valid Python-like expression using only allowed
                operations and referencing claims via claims['name'] syntax.
            claims: Dictionary mapping claim names to Claim objects.
                The claims are accessible in the expression as claims['name'].

        Returns:
            The boolean result of evaluating the expression.

        Raises:
            LPLParseError: If the expression cannot be parsed or contains
                disallowed operations.
            LPLEvaluationError: If the expression fails during evaluation
                (e.g., missing claim, type error).

        Example:
            >>> parser = LPLExpressionParser()
            >>> claims = {"verified": Claim(name="verified", value=True, ...)}
            >>> parser.evaluate("claims['verified'].value == True", claims)
            True
        """
        if not expression or not expression.strip():
            raise LPLParseError(
                "Expression cannot be empty",
                expression=expression
            )

        # Parse the expression into an AST
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            raise LPLParseError(
                f"Invalid expression syntax: {e.msg}",
                expression=expression,
                position=e.offset
            )

        # Validate the AST for security
        self._validate_ast(tree, expression)

        # Evaluate the AST
        try:
            result = self._evaluate_node(tree.body, claims)
        except LPLEvaluationError:
            raise
        except Exception as e:
            raise LPLEvaluationError(
                f"Expression evaluation failed: {str(e)}",
                expression=expression
            )

        # Ensure boolean result
        if not isinstance(result, bool):
            # Coerce to boolean for truthiness evaluation
            return bool(result)

        return result

    def validate(self, expression: str) -> bool:
        """Validate an LPL expression without evaluating it.

        This method checks if an expression is syntactically valid and
        contains only allowed operations. Useful for validating policy
        expressions at configuration time.

        Args:
            expression: The LPL expression string to validate.

        Returns:
            True if the expression is valid.

        Raises:
            LPLParseError: If the expression is invalid.

        Example:
            >>> parser = LPLExpressionParser()
            >>> parser.validate("claims['test'].value == 'foo'")
            True
        """
        if not expression or not expression.strip():
            raise LPLParseError(
                "Expression cannot be empty",
                expression=expression
            )

        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            raise LPLParseError(
                f"Invalid expression syntax: {e.msg}",
                expression=expression,
                position=e.offset
            )

        self._validate_ast(tree, expression)
        return True

    def _validate_ast(self, tree: ast.AST, expression: str) -> None:
        """Validate that the AST only contains allowed operations.

        Walks the AST and checks:
        1. All node types are in the whitelist
        2. All referenced names are allowed
        3. All attribute accesses are to allowed claim attributes
        4. Tree depth and node count are within limits

        Args:
            tree: The parsed AST to validate.
            expression: The original expression string (for error messages).

        Raises:
            LPLParseError: If the AST contains disallowed operations.
        """
        node_count = 0
        max_depth_seen = 0

        def check_node(node: ast.AST, depth: int = 0) -> None:
            nonlocal node_count, max_depth_seen

            node_count += 1
            max_depth_seen = max(max_depth_seen, depth)

            # Check node count limit
            if node_count > self.max_nodes:
                raise LPLParseError(
                    f"Expression too complex: exceeds maximum of {self.max_nodes} nodes",
                    expression=expression
                )

            # Check depth limit
            if depth > self.max_depth:
                raise LPLParseError(
                    f"Expression too deeply nested: exceeds maximum depth of {self.max_depth}",
                    expression=expression
                )

            # Check node type is allowed
            if type(node) not in self.ALLOWED_NODE_TYPES:
                raise LPLParseError(
                    f"Disallowed operation: {type(node).__name__}. "
                    f"Only comparison, logical, and attribute operations are allowed.",
                    expression=expression
                )

            # Check Name nodes reference allowed variables
            if isinstance(node, ast.Name):
                if node.id not in self.ALLOWED_NAMES:
                    raise LPLParseError(
                        f"Disallowed variable: '{node.id}'. "
                        f"Only 'claims', 'None', 'True', 'False' are allowed.",
                        expression=expression
                    )

            # Check Attribute nodes access allowed attributes
            # We validate attribute names, allowing nested access like value.quote
            if isinstance(node, ast.Attribute):
                # Get the full attribute chain
                attr_name = node.attr

                # Allow any attribute access on the value - this enables
                # expressions like claims['tee.attestation'].value.quote
                # The actual runtime check will validate if the attribute exists

                # Check if this is a direct access on claims (after subscript)
                # In that case, validate it's an allowed claim attribute
                if isinstance(node.value, ast.Subscript):
                    if attr_name not in self.ALLOWED_CLAIM_ATTRIBUTES:
                        raise LPLParseError(
                            f"Disallowed claim attribute: '{attr_name}'. "
                            f"Allowed attributes: {', '.join(sorted(self.ALLOWED_CLAIM_ATTRIBUTES))}",
                            expression=expression
                        )

            # Recursively check child nodes
            for child in ast.iter_child_nodes(node):
                check_node(child, depth + 1)

        check_node(tree)

    def _evaluate_node(
        self,
        node: ast.AST,
        claims: Dict[str, Any]
    ) -> Any:
        """Recursively evaluate an AST node.

        This is the core evaluation logic that walks the AST and computes
        the result. Each node type has its own handling logic.

        Args:
            node: The AST node to evaluate.
            claims: The claims dictionary for resolving claim references.

        Returns:
            The result of evaluating the node.

        Raises:
            LPLEvaluationError: If evaluation fails.
        """
        # Handle constants (strings, numbers, None, True, False)
        if isinstance(node, ast.Constant):
            return node.value

        # Handle variable names
        if isinstance(node, ast.Name):
            if node.id == "claims":
                return claims
            elif node.id == "None":
                return None
            elif node.id == "True":
                return True
            elif node.id == "False":
                return False
            else:
                raise LPLEvaluationError(
                    f"Unknown variable: '{node.id}'"
                )

        # Handle subscript access: claims['key']
        if isinstance(node, ast.Subscript):
            value = self._evaluate_node(node.value, claims)
            key = self._evaluate_node(node.slice, claims)

            if not isinstance(key, str):
                raise LPLEvaluationError(
                    f"Claim key must be a string, got {type(key).__name__}"
                )

            if value is claims:
                # Accessing a claim from the claims dict
                if key not in claims:
                    raise LPLEvaluationError(
                        f"Claim not found: '{key}'",
                        claim_name=key
                    )
                return claims[key]
            elif isinstance(value, dict):
                # Accessing a key from a dict value
                if key not in value:
                    raise LPLEvaluationError(
                        f"Key not found in value: '{key}'"
                    )
                return value[key]
            else:
                raise LPLEvaluationError(
                    f"Cannot subscript type: {type(value).__name__}"
                )

        # Handle attribute access: .value, .confidence, etc.
        if isinstance(node, ast.Attribute):
            value = self._evaluate_node(node.value, claims)
            attr_name = node.attr

            # Handle None.attribute (should raise)
            if value is None:
                raise LPLEvaluationError(
                    f"Cannot access attribute '{attr_name}' on None"
                )

            # Try to get the attribute
            if hasattr(value, attr_name):
                return getattr(value, attr_name)
            elif isinstance(value, dict) and attr_name in value:
                # Allow dict-style access for nested values
                return value[attr_name]
            else:
                raise LPLEvaluationError(
                    f"Attribute '{attr_name}' not found on {type(value).__name__}"
                )

        # Handle comparison operations: ==, !=, <, <=, >, >=, is, is not
        if isinstance(node, ast.Compare):
            left = self._evaluate_node(node.left, claims)

            # Handle chained comparisons: a < b < c
            for op, comparator in zip(node.ops, node.comparators):
                right = self._evaluate_node(comparator, claims)

                op_func = self.COMPARISON_OPS.get(type(op))
                if op_func is None:
                    raise LPLEvaluationError(
                        f"Unsupported comparison operator: {type(op).__name__}"
                    )

                try:
                    if not op_func(left, right):
                        return False
                except TypeError as e:
                    raise LPLEvaluationError(
                        f"Type error in comparison: {str(e)}"
                    )

                # For chained comparisons, the right becomes the new left
                left = right

            return True

        # Handle boolean operations: and, or
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                for value in node.values:
                    if not self._evaluate_node(value, claims):
                        return False
                return True
            elif isinstance(node.op, ast.Or):
                for value in node.values:
                    if self._evaluate_node(value, claims):
                        return True
                return False

        # Handle unary operations: not, -, +
        if isinstance(node, ast.UnaryOp):
            operand = self._evaluate_node(node.operand, claims)

            if isinstance(node.op, ast.Not):
                return not operand
            elif isinstance(node.op, ast.USub):
                return -operand
            elif isinstance(node.op, ast.UAdd):
                return +operand

        raise LPLEvaluationError(
            f"Unsupported node type during evaluation: {type(node).__name__}"
        )

    def get_referenced_claims(self, expression: str) -> Set[str]:
        """Extract the set of claim names referenced in an expression.

        This method parses the expression and identifies all claim keys
        that are accessed via claims['key'] syntax. Useful for dependency
        analysis and pre-validation.

        Args:
            expression: The LPL expression to analyze.

        Returns:
            Set of claim names referenced in the expression.

        Raises:
            LPLParseError: If the expression cannot be parsed.

        Example:
            >>> parser = LPLExpressionParser()
            >>> parser.get_referenced_claims(
            ...     "claims['a'].value == 'x' and claims['b'].confidence > 0.5"
            ... )
            {'a', 'b'}
        """
        if not expression or not expression.strip():
            raise LPLParseError(
                "Expression cannot be empty",
                expression=expression
            )

        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            raise LPLParseError(
                f"Invalid expression syntax: {e.msg}",
                expression=expression,
                position=e.offset
            )

        # Validate first to ensure the expression is safe
        self._validate_ast(tree, expression)

        # Extract claim names
        claim_names: Set[str] = set()

        def find_claims(node: ast.AST) -> None:
            if isinstance(node, ast.Subscript):
                # Check if this is claims['key']
                if isinstance(node.value, ast.Name) and node.value.id == "claims":
                    if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                        claim_names.add(node.slice.value)

            for child in ast.iter_child_nodes(node):
                find_claims(child)

        find_claims(tree)
        return claim_names


# =============================================================================
# Convenience Functions
# =============================================================================


def evaluate_expression(
    expression: str,
    claims: Dict[str, Any]
) -> bool:
    """Convenience function to evaluate an LPL expression.

    Creates a default parser instance and evaluates the expression.
    For repeated evaluations, prefer creating a parser instance directly.

    Args:
        expression: The LPL expression string to evaluate.
        claims: Dictionary mapping claim names to Claim objects.

    Returns:
        The boolean result of evaluating the expression.

    Raises:
        LPLParseError: If the expression cannot be parsed.
        LPLEvaluationError: If the expression fails during evaluation.

    Example:
        >>> from lucid_sdk.lpl_parser import evaluate_expression
        >>> result = evaluate_expression(
        ...     "claims['test'].value == 'foo'",
        ...     {"test": Claim(name="test", value="foo", ...)}
        ... )
        >>> assert result == True
    """
    parser = LPLExpressionParser()
    return parser.evaluate(expression, claims)


def validate_expression(expression: str) -> bool:
    """Convenience function to validate an LPL expression.

    Creates a default parser instance and validates the expression.
    For repeated validations, prefer creating a parser instance directly.

    Args:
        expression: The LPL expression string to validate.

    Returns:
        True if the expression is valid.

    Raises:
        LPLParseError: If the expression is invalid.

    Example:
        >>> from lucid_sdk.lpl_parser import validate_expression
        >>> validate_expression("claims['test'].value == 'foo'")
        True
    """
    parser = LPLExpressionParser()
    return parser.validate(expression)
