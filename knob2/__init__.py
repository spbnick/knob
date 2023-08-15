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


class RoleOpnd(Opnd):
    """An unassigned role operand"""
    def __init__(self, graph: Graph, name: str):
        super().__init__(graph)
        self.name = name

    def __repr__(self):
        return repr(self.name)


class ActorOpnd(Opnd):
    """An actor operand (something which can be cast for a role)"""

    def __sub__(self, role_or_director) -> \
            ForwardRef('CastOp') | NotImplemented:
        """Create a role-casting operator for S - O expression """
        if isinstance(role_or_director, DirectorOpnd):
            assert role_or_director.graph is self.graph
            return CastOp(self, role_or_director)
        if isinstance(role_or_director, str):
            return CastOp(self, RoleOpnd(self.graph, role_or_director))
        return NotImplemented

    def __rsub__(self, role_or_director) -> \
            ForwardRef('CastOp') | NotImplemented:
        """Create a role-casting operator for O - S expression """
        if isinstance(role_or_director, DirectorOpnd):
            assert role_or_director.graph is self.graph
            return CastOp(role_or_director, self)
        if isinstance(role_or_director, str):
            return CastOp(RoleOpnd(self.graph, role_or_director), self)
        return NotImplemented


class DirectorOpnd(Opnd):
    """A casting director operand (something which can open a role)"""

    def __mul__(self, role_or_actor) -> \
            ForwardRef('OpenOp') | NotImplemented:
        """Create a role-opening operator for S * O expression """
        if isinstance(role_or_actor, ActorOpnd):
            assert role_or_actor.graph is self.graph
            return OpenOp(self, role_or_actor)
        if isinstance(role_or_actor, str):
            return OpenOp(self, RoleOpnd(self.graph, role_or_actor))
        return NotImplemented

    def __rmul__(self, role_or_actor) -> \
            ForwardRef('OpenOp') | NotImplemented:
        """Create a role-opening operator for O * S expression """
        if isinstance(role_or_actor, ActorOpnd):
            assert role_or_actor.graph is self.graph
            return OpenOp(role_or_actor, self)
        if isinstance(role_or_actor, str):
            return OpenOp(RoleOpnd(self.graph, role_or_actor), self)
        return NotImplemented


class ElementOpnd(ActorOpnd):
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


class EntityOpnd(ElementOpnd):
    """An entity operand"""

    def __rshift__(self, opnd) -> \
            ForwardRef('CastOp') | NotImplemented:
        """Create edge/role expression for S >> O expression"""
        if isinstance(opnd, RelationOpnd):
            assert opnd.graph is self.graph
            return self - "source" * opnd
        if isinstance(opnd, EntityOpnd):
            assert opnd.graph is self.graph
            return self - "source" * RelationOpnd(self.graph) * \
                "target" - opnd
        return NotImplemented

    def __lshift__(self, opnd) -> \
            ForwardRef('CastOp') | NotImplemented:
        """Create edge/role expression for S << O expression"""
        if isinstance(opnd, RelationOpnd):
            assert opnd.graph is self.graph
            return self - "target" * opnd
        if isinstance(opnd, EntityOpnd):
            assert opnd.graph is self.graph
            return self - "target" * RelationOpnd(self.graph) * \
                "source" - opnd
        return NotImplemented

    def __rlshift__(self, opnd) -> \
            ForwardRef('CastOp') | NotImplemented:
        """Create edge/role expression for O << S expression"""
        if isinstance(opnd, RelationOpnd):
            assert opnd.graph is self.graph
            return opnd * "target" - self
        if isinstance(opnd, EntityOpnd):
            assert opnd.graph is self.graph
            return opnd - "target" * RelationOpnd(self.graph) * \
                "source" - self
        return NotImplemented

    def __rrshift__(self, opnd) -> \
            ForwardRef('CastOp') | NotImplemented:
        """Create edge/role expression for O >> S expression"""
        if isinstance(opnd, RelationOpnd):
            assert opnd.graph is self.graph
            return opnd * "target" - self
        if isinstance(opnd, EntityOpnd):
            assert opnd.graph is self.graph
            return opnd - "source" * RelationOpnd(self.graph) * \
                "target" - self
        return NotImplemented

    def __repr__(self):
        return "e"


class RelationOpnd(ElementOpnd, DirectorOpnd):
    """A relation operand"""

    def __repr__(self):
        return "r"


class CastingOpnd(Opnd):
    """A role's casting operand"""


class OpeningOpnd(Opnd):
    """A role's opening operand"""


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


class SetCreationOp(Op, EntityOpnd, RelationOpnd):
    """An operation changing the operand's creation state"""
    def __init__(self, opnd: Opnd, create: bool):
        super().__init__(opnd.graph)
        self.opnd = opnd
        self.create = create

    def __repr__(self):
        return ("+" if self.create else "-") + \
            opnd_repr_right(self, self.opnd)


class OpenOp(Op, EntityOpnd, RelationOpnd, CastingOpnd, OpeningOpnd):
    """An operation binding a role name or casting to a relation"""
    def __init__(self, left, right):
        def opnds_are_valid(x, y):
            return isinstance(x, DirectorOpnd) and \
                isinstance(y, (ActorOpnd, RoleOpnd))
        assert opnds_are_valid(left, right) or opnds_are_valid(right, left)
        assert left.graph is right.graph
        super().__init__(left.graph)
        self.left = left
        self.right = right

    def __repr__(self):
        return opnd_repr_left(self.left, self) + " * " + \
            opnd_repr_right(self, self.right)


class CastOp(Op, EntityOpnd, RelationOpnd, CastingOpnd, OpeningOpnd):
    """An operation (re)binding a role name or opening to an actor element"""
    def __init__(self, left, right):
        def opnds_are_valid(x, y):
            return isinstance(x, ActorOpnd) and \
                isinstance(y, (DirectorOpnd, RoleOpnd))
        assert opnds_are_valid(left, right) or opnds_are_valid(right, left)
        assert left.graph is right.graph
        super().__init__(left.graph)
        self.left = left
        self.right = right

    def __repr__(self):
        return opnd_repr_left(self.left, self) + " - " + \
            opnd_repr_right(self, self.right)


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
