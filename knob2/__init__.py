"""
KNOB - Knowledge builder - a module for creating knowledge (hyper)graphs.

NOTE: All binary graph operators are left-associative
"""

import math
from typing import ForwardRef
from abc import ABC, abstractmethod

# We're being abstract here,
# pylint: disable=too-few-public-methods,too-many-ancestors,invalid-name


class Graph:
    """A graph"""

    def __init__(self):
        self.entity_opnd = EntityOpnd(self)
        self.relation_opnd = RelationOpnd(self)


class Opnd(ABC):
    """An operand"""

    def __init__(self, graph: Graph):
        self.graph = graph

    def __pos__(self):
        """Create a creation-enabling operator"""
        return SetCreationOp(self, True)

    def __neg__(self):
        """Create a creation-disabling operator"""
        return SetCreationOp(self, False)

    @abstractmethod
    def __repr__(self):
        pass


class ElementOpnd(Opnd):
    """An element operand"""

    def __getattr__(self, key: str) -> 'UpdateOp':
        """Create an implicit attribute update operator"""
        return UpdateOp(self, {"": key})

    def __getitem__(self, key) -> ForwardRef('UpdateOp') | NotImplemented:
        """Create an implicit attribute update operator"""
        if isinstance(key, str):
            return UpdateOp(self, {"": key})
        return NotImplemented

    def __call__(self, **attrs) -> ForwardRef('UpdateOp'):
        """Create an attribute update operator"""
        return UpdateOp(self, attrs)

    def __sub__(self, role_or_opening) -> \
            ForwardRef('CastOp') | NotImplemented:
        """Create a role-casting operator for S - R expression """
        if isinstance(role_or_opening, OpeningOpnd):
            assert role_or_opening.graph is self.graph
            return CastOp(role_or_opening, self, True)
        if isinstance(role_or_opening, str):
            return CastOp(RoleOpnd(self.graph, role_or_opening), self, True)
        return NotImplemented

    def __rsub__(self, role_or_opening) -> \
            ForwardRef('CastOp') | NotImplemented:
        """Create a role-casting operator for R - S expression """
        if isinstance(role_or_opening, OpeningOpnd):
            assert role_or_opening.graph is self.graph
            return CastOp(role_or_opening, self, False)
        if isinstance(role_or_opening, str):
            return CastOp(RoleOpnd(self.graph, role_or_opening), self, False)
        return NotImplemented


class EntityOpnd(ElementOpnd):
    """An entity operand"""

    def __rshift__(self, element) -> \
            ForwardRef('CastOp') | NotImplemented:
        """Create a role-casting operator for S >> E expression"""
        if isinstance(element, RelationOpnd):
            assert element.graph is self.graph
            return self - "source" * element
        if isinstance(element, EntityOpnd):
            assert element.graph is self.graph
            return self - "source" * RelationOpnd(self.graph) * \
                "target" - element
        return NotImplemented

    def __lshift__(self, element) -> \
            ForwardRef('CastOp') | NotImplemented:
        """Create a role-casting operator for S << E expression"""
        if isinstance(element, RelationOpnd):
            assert element.graph is self.graph
            return self - "target" * element
        if isinstance(element, EntityOpnd):
            assert element.graph is self.graph
            return self - "target" * RelationOpnd(self.graph) * \
                "source" - element
        return NotImplemented

    def __rlshift__(self, element) -> \
            ForwardRef('CastOp') | NotImplemented:
        """Create a role-casting operator for E << S expression"""
        if isinstance(element, RelationOpnd):
            assert element.graph is self.graph
            return element * "target" - self
        if isinstance(element, EntityOpnd):
            assert element.graph is self.graph
            return element - "target" * RelationOpnd(self.graph) * \
                "source" - self
        return NotImplemented

    def __rrshift__(self, element) -> \
            ForwardRef('CastOp') | NotImplemented:
        """Create a role-casting operator for E >> S expression"""
        if isinstance(element, RelationOpnd):
            assert element.graph is self.graph
            return element * "target" - self
        if isinstance(element, EntityOpnd):
            assert element.graph is self.graph
            return element - "source" * RelationOpnd(self.graph) * \
                "target" - self
        return NotImplemented

    def __repr__(self):
        return "e"


class RelationOpnd(ElementOpnd):
    """A relation operand"""

    def __mul__(self, role_or_casting) -> \
            ForwardRef('OpenOp') | NotImplemented:
        """Create a role-opening operator for S * R expression """
        if isinstance(role_or_casting, CastingOpnd):
            assert role_or_casting.graph is self.graph
            return OpenOp(self, role_or_casting, False)
        if isinstance(role_or_casting, str):
            return OpenOp(self, RoleOpnd(self.graph, role_or_casting), False)
        return NotImplemented

    def __rmul__(self, role_or_casting) -> \
            ForwardRef('OpenOp') | NotImplemented:
        """Create a role-opening operator for R * S expression """
        if isinstance(role_or_casting, CastingOpnd):
            assert role_or_casting.graph is self.graph
            return OpenOp(self, role_or_casting, True)
        if isinstance(role_or_casting, str):
            return OpenOp(self, RoleOpnd(self.graph, role_or_casting), True)
        return NotImplemented

    def __repr__(self):
        return "r"


class RoleOpnd(Opnd):
    """An unassigned role operand"""
    def __init__(self, graph: Graph, name: str):
        super().__init__(graph)
        self.name = name

    def __repr__(self):
        return repr(self.name)


class OpeningOpnd(Opnd):
    """A role's opening operand (a role name assigned to a relation)"""


class CastingOpnd(Opnd):
    """A role's casting operand (a role name assigned to an element)"""


class Op(Opnd):
    """An operation"""


class UpdateOp(Op, EntityOpnd, RelationOpnd):
    """An element attribute update operation"""
    def __init__(self, element: ElementOpnd, attrs: dict[str, object]):
        super().__init__(element.graph)
        self.element = element
        self.attrs = attrs

    def __repr__(self):
        if set(self.attrs) == {""}:
            if self.attrs[""].isidentifier():
                expr = "." + self.attrs[""]
            else:
                expr = "[" + repr(self.attrs[""]) + "]"
        else:
            if all(k.isidentifier() for k in self.attrs):
                expr = ", ".join(
                    k + "=" + repr(v) for k, v in self.attrs.items()
                )
            else:
                expr = "**" + repr(self.attrs)
            expr = "(" + expr + ")"
        return opnd_repr_left(self.element, self) + expr


class SetCreationOp(Op, EntityOpnd, RelationOpnd, OpeningOpnd, CastingOpnd):
    """An operation changing the operand's creation state"""
    def __init__(self, opnd: Opnd, create: bool):
        super().__init__(opnd.graph)
        self.opnd = opnd
        self.create = create

    def __repr__(self):
        return ("+" if self.create else "-") + \
            opnd_repr_right(self, self.opnd)


class OpenOp(Op, OpeningOpnd, EntityOpnd, RelationOpnd):
    """An operation binding a role name or casting to a relation"""
    def __init__(self,
                 relation: RelationOpnd,
                 role_or_casting: RoleOpnd | CastingOpnd,
                 reverse: bool):
        super().__init__(relation.graph)
        self.relation = relation
        self.role_or_casting = role_or_casting
        self.reverse = reverse

    def __repr__(self):
        # Piss off, pylint: disable=no-else-return
        if self.reverse:
            return opnd_repr_left(self.role_or_casting, self) + " * " + \
                opnd_repr_right(self, self.relation)
        else:
            return opnd_repr_left(self.relation, self) + " * " + \
                opnd_repr_right(self, self.role_or_casting)


class CastOp(Op, CastingOpnd, EntityOpnd, RelationOpnd):
    """An operation binding a role name or opening to an actor element"""
    def __init__(self,
                 role_or_opening: RoleOpnd | OpeningOpnd,
                 element: ElementOpnd,
                 reverse: bool):
        super().__init__(element.graph)
        self.role_or_opening = role_or_opening
        self.element = element
        self.reverse = reverse

    def __repr__(self):
        # Piss off, pylint: disable=no-else-return
        if self.reverse:
            return opnd_repr_left(self.element, self) + " - " + \
                opnd_repr_right(self, self.role_or_opening)
        else:
            return opnd_repr_left(self.role_or_opening, self) + " - " + \
                opnd_repr_right(self, self.element)


# Precedence of operands - lower precedence first
OPND_TYPE_PRECEDENCE = [
    CastOp,
    OpenOp,
    SetCreationOp,
    UpdateOp,
    Opnd,
]

def opnd_type_get_precedence(opnd_type: type) -> int:
    """Get operand type precedence (lower precedence - lower number)"""
    assert isinstance(opnd_type, type)
    assert issubclass(opnd_type, Opnd)
    # Return the precedence index of the type closest to the operand type
    mro = opnd_type.__mro__
    return min(
        enumerate(OPND_TYPE_PRECEDENCE),
        default=(-1, object),
        # Use inheritance distance from type as the key
        key=lambda x: mro.index(x[1]) if x[1] in mro else math.inf
    )[0]


def opnd_get_precedence(opnd: Opnd) -> int:
    """Get operand instance precedence (lower precedence - lower number)"""
    assert isinstance(opnd, Opnd)
    return opnd_type_get_precedence(type(opnd))


def opnd_repr_right(op: Op, opnd: Opnd):
    """
    Enclose a string representation of an operand into parentheses, if it's
    to the right of a higher- or same-precedence operator.
    """
    expr = repr(opnd)
    if opnd_get_precedence(op) >= opnd_get_precedence(opnd):
        expr = "(" + expr + ")"
    return expr


def opnd_repr_left(opnd: Opnd, op: Op):
    """
    Enclose a string representation of an operand into parentheses, if it's
    to the left of a higher-precedence operator.
    """
    expr = repr(opnd)
    if opnd_get_precedence(op) > opnd_get_precedence(opnd):
        expr = "(" + expr + ")"
    return expr
