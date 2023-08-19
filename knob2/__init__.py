"""
KNOB - Knowledge builder - a module for creating knowledge (hyper)graphs.

NOTE: All binary graph operators are left-associative
"""

import math
from typing import ForwardRef
from abc import ABC, abstractmethod

# We're being abstract here,
# pylint: disable=too-few-public-methods,too-many-ancestors,invalid-name

# We're all friends here, pylint: disable=protected-access

# No, I like it this way, pylint: disable=no-else-return


class Graph:
    """A graph"""

    def __init__(self):
        self.entity = EntityAtom(self)
        self.relation = RelationAtom(self)


class Expr(ABC):
    """An expression (tree)"""

    def __init__(self, graph: Graph):
        self._graph = graph

    @property
    @abstractmethod
    def _left_atom(self):
        """The leftmost atom of the expression tree."""

    @property
    @abstractmethod
    def _right_atom(self):
        """The rightmost atom of the expression tree."""

    @abstractmethod
    def __repr__(self):
        pass

    def __pos__(self):
        """Create a creation-enabling operator"""
        return SetCreationOp(self, True)

    def __neg__(self):
        """Create a creation-disabling operator"""
        return SetCreationOp(self, False)

    def __getattr__(self, key: str) -> 'UpdateOp':
        """Create an implicit attribute update operator"""
        if isinstance(self._right_atom, ElementAtom):
            return UpdateOp(self, {"": key})
        return NotImplemented

    def __getitem__(self, key) -> ForwardRef('UpdateOp') | NotImplemented:
        """Create an implicit attribute update operator"""
        if isinstance(self._right_atom, ElementAtom) and isinstance(key, str):
            return UpdateOp(self, {"": key})
        return NotImplemented

    def __call__(self, **attrs) -> ForwardRef('UpdateOp'):
        """Create an attribute update operator"""
        if isinstance(self._right_atom, ElementAtom):
            return UpdateOp(self, attrs)
        return NotImplemented

    def __sub__(self, other) -> ForwardRef('CastOp') | NotImplemented:
        """Create a role-casting operator for S - O expression """
        if isinstance(other, str):
            other = RoleAtom(self._graph, other)
        if CastOp.args_are_valid(self, other):
            return CastOp(self, other)
        return NotImplemented

    def __rsub__(self, other) -> ForwardRef('CastOp') | NotImplemented:
        """Create a role-casting operator for O - S expression """
        if isinstance(other, str):
            other = RoleAtom(self._graph, other)
        if CastOp.args_are_valid(other, self):
            return CastOp(other, self)
        return NotImplemented

    def __mul__(self, other) -> ForwardRef('OpenOp') | NotImplemented:
        """Create a role-opening operator for S * O expression """
        if isinstance(other, str):
            other = RoleAtom(self._graph, other)
        if OpenOp.args_are_valid(self, other):
            return OpenOp(self, other)
        return NotImplemented

    def __rmul__(self, other) -> ForwardRef('OpenOp') | NotImplemented:
        """Create a role-opening operator for O * S expression """
        if isinstance(other, str):
            other = RoleAtom(self._graph, other)
        if OpenOp.args_are_valid(other, self):
            return OpenOp(other, self)
        return NotImplemented

    @staticmethod
    def __shift(left, op, right) -> ForwardRef('CastOp') | NotImplemented:
        """Create an expression for a shift operator"""
        # No it's not, pylint: disable=too-many-return-statements
        assert op in {"<<", ">>"}

        if not isinstance(left, Expr) or not isinstance(right, Expr):
            return NotImplemented

        assert left._graph is right._graph

        ltr = op == ">>"
        left_atom = left._right_atom
        right_atom = right._left_atom

        if isinstance(left_atom, EntityAtom) and \
           isinstance(right_atom, EntityAtom):
            relation = RelationAtom(left._graph)
            if ltr:
                return left - "source" * relation * "target" - right
            else:
                return left - "target" * relation * "source" - right
        elif isinstance(left_atom, RelationAtom) and \
                isinstance(right_atom, EntityAtom):
            if ltr:
                return left * "target" - right
            else:
                return left * "source" - right
        elif isinstance(left_atom, EntityAtom) and \
                isinstance(right_atom, RelationAtom):
            if ltr:
                return left - "source" * right
            else:
                return left - "target" * right

        return NotImplemented

    def __rshift__(self, other) -> ForwardRef('CastOp') | NotImplemented:
        """Create edge/role expression for S >> O expression"""
        return Expr.__shift(self, ">>", other)

    def __rrshift__(self, other) -> ForwardRef('CastOp') | NotImplemented:
        """Create edge/role expression for O >> S expression"""
        return Expr.__shift(other, ">>", self)

    def __lshift__(self, other) -> ForwardRef('CastOp') | NotImplemented:
        """Create edge/role expression for S << O expression"""
        return Expr.__shift(self, "<<", other)

    def __rlshift__(self, other) -> ForwardRef('CastOp') | NotImplemented:
        """Create edge/role expression for O << S expression"""
        return Expr.__shift(other, "<<", self)


class Atom(Expr):
    """An atomic (indivisible) expression (not an operator)"""

    @property
    def _left_atom(self):
        return self

    @property
    def _right_atom(self):
        return self


class RoleAtom(Atom):
    """An unassigned role"""

    def __init__(self, graph: Graph, name: str):
        super().__init__(graph)
        self._name = name

    def __repr__(self):
        return repr(self._name)


class ElementAtom(Atom):
    """An element atom"""


class EntityAtom(ElementAtom):
    """An entity operand"""

    def __repr__(self):
        return "e"


class RelationAtom(ElementAtom):
    """A relation operand"""

    def __repr__(self):
        return "r"


class Op(Expr):
    """An operator over one or more expressions"""


class UnaryOp(Op):
    """An unary operator"""

    def __init__(self, arg: Expr):
        super().__init__(arg._graph)
        self._arg = arg

    @property
    def _left_atom(self):
        return self._arg._left_atom

    @property
    def _right_atom(self):
        return self._arg._right_atom


class BinaryOp(Op):
    """A binary operator"""

    def __init__(self, left: Expr, right: Expr):
        assert left._graph is right._graph
        super().__init__(left._graph)
        self._left = left
        self._right = right

    @property
    def _left_atom(self):
        return self._left._left_atom

    @property
    def _right_atom(self):
        return self._right._right_atom


class UpdateOp(UnaryOp):
    """An element attribute update operation"""
    def __init__(self, arg: Expr, attrs: dict[str, object]):
        super().__init__(arg)
        self._attrs = attrs

    def __repr__(self):
        if set(self._attrs) == {""}:
            if self._attrs[""].isidentifier():
                expr = "." + self._attrs[""]
            else:
                expr = "[" + repr(self._attrs[""]) + "]"
        else:
            if all(k.isidentifier() for k in self._attrs):
                expr = ", ".join(
                    k + "=" + repr(v) for k, v in self._attrs.items()
                )
            else:
                expr = "**" + repr(self._attrs)
            expr = "(" + expr + ")"
        return opnd_repr_left(self._arg, self) + expr


class SetCreationOp(UnaryOp):
    """An operation changing the operand's creation state"""
    def __init__(self, arg: Expr, create: bool):
        super().__init__(arg)
        self._create = create

    def __repr__(self):
        return ("+" if self._create else "-") + \
            opnd_repr_right(self, self._arg)


class OpenOp(BinaryOp):
    """An operation "opening" a role name with a relation"""

    @staticmethod
    def args_are_valid(left, right):
        """Check the operation arguments are valid"""
        return (
            isinstance(left, Expr) and isinstance(right, Expr) and
            left._graph is right._graph and
            (
                isinstance(left._right_atom, RelationAtom) and
                isinstance(right._left_atom, RoleAtom) or
                isinstance(left._right_atom, RoleAtom) and
                isinstance(right._left_atom, RelationAtom)
            )
        )

    def __init__(self, left, right):
        assert OpenOp.args_are_valid(left, right)
        super().__init__(left, right)

    def __repr__(self):
        return opnd_repr_left(self._left, self) + " * " + \
            opnd_repr_right(self, self._right)


class CastOp(BinaryOp):
    """An operation "casting" an element for a role"""

    @staticmethod
    def args_are_valid(left, right):
        """Check the operation arguments are valid"""
        return (
            isinstance(left, Expr) and isinstance(right, Expr) and
            left._graph is right._graph and
            (
                isinstance(left._right_atom, ElementAtom) and
                isinstance(right._left_atom, RoleAtom) or
                isinstance(left._right_atom, RoleAtom) and
                isinstance(right._left_atom, ElementAtom)
            )
        )

    def __init__(self, left, right):
        assert CastOp.args_are_valid(left, right)
        super().__init__(left, right)

    def __repr__(self):
        return opnd_repr_left(self._left, self) + " - " + \
            opnd_repr_right(self, self._right)


# Precedence of expressions - lower precedence first
EXPR_TYPE_PRECEDENCE = [
    CastOp,
    OpenOp,
    SetCreationOp,
    UpdateOp,
    Atom,
]


def expr_type_get_precedence(expr_type: type) -> int:
    """Get expression type precedence (lower precedence - lower number)"""
    assert isinstance(expr_type, type)
    assert issubclass(expr_type, Expr)
    # Return the precedence index of the type closest to the expression type
    mro = expr_type.__mro__
    return min(
        enumerate(EXPR_TYPE_PRECEDENCE),
        default=(-1, object),
        # Use inheritance distance from type as the key
        key=lambda x: mro.index(x[1]) if x[1] in mro else math.inf
    )[0]


def expr_get_precedence(expr: Expr) -> int:
    """Get expression precedence (lower precedence - lower number)"""
    assert isinstance(expr, Expr)
    return expr_type_get_precedence(type(expr))


def opnd_repr_right(op: Op, opnd: Expr):
    """
    Enclose a string representation of an operand expression into parentheses,
    if it's to the right of a higher- or same-precedence operator.
    """
    opnd_repr = repr(opnd)
    if expr_get_precedence(op) >= expr_get_precedence(opnd):
        opnd_repr = "(" + opnd_repr + ")"
    return opnd_repr


def opnd_repr_left(opnd: Expr, op: Op):
    """
    Enclose a string representation of an operand expression into parentheses,
    if it's to the left of a higher-precedence operator.
    """
    opnd_repr = repr(opnd)
    if expr_get_precedence(op) > expr_get_precedence(opnd):
        opnd_repr = "(" + opnd_repr + ")"
    return opnd_repr
