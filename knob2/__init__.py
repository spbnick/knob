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


class AtomPattern(ABC):
    """An abstract atom pattern evaluated from an expresion"""

    @abstractmethod
    def __repr__(self):
        pass


class ElementPattern(AtomPattern):
    """An abstract element (relation or entity) pattern"""

    def __init__(self, attrs: dict[str, object]):
        """
        Initialize the element pattern.

        Args:
            attrs:  The attribute dictionary.
        """
        self.attrs = attrs

    @abstractmethod
    def with_updated_attrs(self, attrs: dict[str, object]) -> \
            'ElementPattern':
        """Duplicate the pattern with attributes updated"""


class EntityPattern(ElementPattern):
    """An entity pattern"""

    def __repr__(self):
        return 'e' + str(id(self)) + (repr(self.attrs) if self.attrs else "")

    def with_updated_attrs(self, attrs: dict[str, object]) -> \
            'EntityPattern':
        """Duplicate the pattern with attributes updated"""
        return self, EntityPattern(self.attrs | attrs)


class RelationPattern(ElementPattern):
    """A relation pattern"""

    def __init__(self,
                 attrs: dict[str, object],
                 roles: dict[str, ElementPattern]):
        """
        Initialize the relation pattern.

        Args:
            attrs:  The attribute dictionary.
            roles:  The role dictionary.
        """
        super().__init__(attrs)
        self.roles = roles

    def __repr__(self):
        return 'r' + str(id(self)) + \
            (repr(self.attrs) if self.attrs or self.roles else "") + \
            (repr(self.roles) if self.roles else "")

    def with_updated_attrs(self, attrs: dict[str, object]) -> \
            'RelationPattern':
        """Duplicate the pattern with attributes updated"""
        return self, RelationPattern(self.attrs | attrs, self.roles)

    def with_updated_roles(self, roles: dict[str, EntityPattern]) -> \
            'RelationPattern':
        """Duplicate the pattern with roles updated"""
        return self, RelationPattern(self.attrs, self.roles | roles)


class RolePattern(AtomPattern):
    """A role (unattached/opening/casting) pattern"""

    def __init__(self, name: str, element: ElementPattern | None):
        """
        Initialize the role's attachment pattern.

        Args:
            name:       The name of the role.
            element:    The element attached to the role, or None.
        """
        self.element = element
        self.name = name

    def __repr__(self):
        return (
            f"({self.name!r}" +
            ("" if self.element is None else f": {self.element!r}") +
            ")"
        )

    def with_element(self, element: ElementPattern) -> \
            ForwardRef('RolePattern'):
        """Create a duplicate with the element set"""
        assert self.element is None
        assert element is not None
        return self, RolePattern(self.name, element)


class GraphPattern:
    """A (sub)graph pattern"""

    def __init__(self,
                 graph: Graph,
                 elements: dict[ElementPattern, bool],
                 left: AtomPattern,
                 right: AtomPattern):
        """
        Initialize the graph pattern.

        Args:
            graph:      The supergraph of the graph this pattern is matching.
            elements:   A dictionary of patterns matching elements
                        (entities or relations) belonging to the subgraph, and
                        one of the two values:
                        * False, if the element pattern should be matched.
                        * True, if all elements matching the (enumerable)
                          pattern should be created unconditionally.
                        Roles in any relation patterns contained in this
                        dictionary can only reference entity patterns from the
                        same dictionary.
            left:       The left-side atom pattern to use when using the
                        graph pattern on the right side of an operator.
                        Must be, or refer to, an element in "elements".
            right:      The right-side atom pattern to use when using the
                        graph pattern on the left side of an operator.
                        Must be, or refer to, an element in "elements".
        """
        entities = {
            e: c
            for e, c in elements.items() if isinstance(e, EntityPattern)
        }
        relations = {
            e: c
            for e, c in elements.items() if isinstance(e, RelationPattern)
        }
        assert set(entities) >= {
            entity
            for relation in relations
            for entity in relation.roles.values()
        }
        assert isinstance(left, (RolePattern, ElementPattern))
        assert isinstance(right, (RolePattern, ElementPattern))
        left_element = \
            left.element if isinstance(left, RolePattern) else left
        right_element = \
            right.element if isinstance(right, RolePattern) else right
        assert left_element is None or left_element in elements
        assert right_element is None or right_element in elements
        self.graph = graph
        self.elements = elements
        self.entities = entities
        self.relations = relations
        self.left = left
        self.right = right

    def __repr__(self):
        return f"{self.left!r} {self.elements!r} {self.right!r}"

    def with_replaced_atom(self, old: AtomPattern, new: AtomPattern) -> \
            ForwardRef('GraphPattern'):
        """Create a duplicate graph pattern with an atom pattern replaced"""
        assert old in {self.left, self.right}, \
            "Replacing a non-interface atom pattern"
        assert not isinstance(old, ElementPattern) or old in self.elements, \
            "Replacing unknown element pattern"
        assert isinstance(old, ElementPattern) <= \
            isinstance(new, ElementPattern), \
            "Cannot downgrade element pattern to a role pattern"

        elements = self.elements.copy()
        left = self.left
        right = self.right

        if isinstance(old, ElementPattern):
            elements[new] = elements.pop(old)
        if old is left:
            left = new
        if new is right:
            right = new

        return GraphPattern(self.graph, elements, left, right)

    def __or__(self, other) -> ForwardRef('GraphPattern') | NotImplemented:
        """Merge two graph patterns"""
        if isinstance(other, GraphPattern) and other.graph is self.graph:
            return GraphPattern(
                self.graph,
                {
                    element: max(self.elements.get(element, False),
                                 other.elements.get(element, False))
                    for element in set(self.elements) | set(other.elements)
                },
                self.left,
                other.right
            )
        return NotImplemented


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

    @abstractmethod
    def _eval(self) -> GraphPattern:
        """Evaluate the expression to a graph pattern"""

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

    def _eval(self) -> GraphPattern:
        """Evaluate the expression to a graph pattern"""
        pattern = RolePattern(self._name, None)
        return GraphPattern(self.graph, {}, pattern, pattern)


class ElementAtom(Atom):
    """An element atom"""


class EntityAtom(ElementAtom):
    """An entity operand"""

    def __repr__(self):
        return "e"

    def _eval(self):
        pattern = EntityPattern({})
        return GraphPattern(self._graph, {pattern: False}, pattern, pattern)


class RelationAtom(ElementAtom):
    """A relation operand"""

    def __repr__(self):
        return "r"

    def _eval(self):
        pattern = RelationPattern({}, {})
        return GraphPattern(self._graph, {pattern: False}, pattern, pattern)


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

    def _eval(self):
        graph = self._arg._eval()
        atom = graph.right
        if not isinstance(atom, ElementPattern):
            raise TypeError
        return graph.with_replaced_atom(
            *atom.with_updated_attrs(self._attrs)
        )


class SetCreationOp(UnaryOp):
    """An operation changing the operand's creation state"""
    def __init__(self, arg: Expr, create: bool):
        super().__init__(arg)
        self._create = create

    def __repr__(self):
        return ("+" if self._create else "-") + \
            opnd_repr_right(self, self._arg)

    def _eval(self):
        graph = self._arg._eval()
        return GraphPattern(
            graph.graph,
            {
                element: self._create
                for element in graph.elements
            },
            graph.left,
            graph.right
        )


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

    def _eval(self):
        left_graph = self._left._eval()
        right_graph = self._right._eval()
        left_atom = left_graph.right
        right_atom = right_graph.left

        assert (
            isinstance(left_atom, RelationPattern) and
            isinstance(right_atom, RolePattern) or
            isinstance(left_atom, RolePattern) and
            isinstance(right_atom, RelationPattern)
        )

        # If the role is on the left
        if isinstance(left_atom, RolePattern):
            role = left_atom
            relation = right_atom
        # Else, the role is on the right
        else:
            relation = left_atom
            role = right_atom

        # If we're trying to open one role name with two relations
        if isinstance(role.element, RelationPattern):
            raise TypeError

        # If we're opening a role with the relation
        if role.element is None:
            return (left_graph | right_graph).with_replaced_atom(
                *role.with_element(relation)
            )
        # Else, we're completing a role
        else:
            return (left_graph | right_graph).with_replaced_atom(
                *relation.with_updated_roles({role.name: role.element})
            )


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

    def _eval(self):
        left_graph = self._left._eval()
        right_graph = self._right._eval()
        left_atom = left_graph.right
        right_atom = right_graph.left

        assert (
            isinstance(left_atom, ElementPattern) and
            isinstance(right_atom, RolePattern) or
            isinstance(left_atom, RolePattern) and
            isinstance(right_atom, ElementPattern)
        )

        # If the role is on the left
        if isinstance(left_atom, RolePattern):
            role = left_atom
            element = right_atom
        # Else, the role is on the right
        else:
            element = left_atom
            role = right_atom

        # If we're trying to cast two entities in one role
        if isinstance(role.element, EntityPattern):
            raise TypeError

        # If we're casting an element for the role
        if role.element is None:
            return (left_graph | right_graph).with_replaced_atom(
                *role.with_element(element)
            )
        # Else, we're completing a role
        else:
            return (left_graph | right_graph).with_replaced_atom(
                *role.element.with_updated_roles({role.name: element})
            )


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
