"""
KNOB - Knowledge builder - a module for creating knowledge (hyper)graphs.

NOTE: All binary graph operators are left-associative
"""

import math
from typing import Tuple
from abc import ABC, abstractmethod

# We're being abstract here,
# pylint: disable=too-few-public-methods,too-many-ancestors,invalid-name

# We're all friends here, pylint: disable=protected-access

# No, I like it this way, pylint: disable=no-else-return


class Graph:
    """A graph"""

    def __init__(self):
        """Initialize the graph"""
        # The ID next created entity atom will use
        self.next_entity_id = 0
        # The ID next created relation atom will use
        self.next_relation_id = 0

    @property
    def entity(self):
        """A unique entity"""
        entity = EntityAtom(self, self.next_entity_id << 1)
        self.next_entity_id += 1
        return entity

    @property
    def e(self):
        """An alias for unique entity"""
        return self.entity

    @property
    def relation(self):
        """A unique relation"""
        relation = RelationAtom(self, self.next_relation_id << 1 | 1)
        self.next_relation_id += 1
        return relation

    @property
    def r(self):
        """An alias for unique relation"""
        return self.relation


def abbr(x) -> str:
    """
    Produce an abbreviated representation of a value

    Args:
        x:  The value to produce an abbreviated representation for.
            If the value has a callable attribute "__abbr__", then that will
            be called to produce the abbreviated representation.
            If the value is a dictionary, and all its keys are valid
            identifiers, it will be formatted as kwargs, with values formatted
            with abbr(), otherwise it will be formatted as a dictionary
            constructor with both its keys and values formatted with abbr().
            If the value is a set, list, or a tuple, its elements will be
            formatted with abbr().
            Otherwise repr() will be used.

    Returns:
        The abbreviated representation of the value.
    """
    # Oh, shut up, pylint: disable=too-many-return-statements
    if callable(getattr(x, "__abbr__", None)):
        return x.__abbr__()
    if isinstance(x, dict):
        if all(isinstance(k, str) and k.isidentifier() for k in x):
            return "(" + ", ".join(
                str(k) + "=" + abbr(v)
                for k, v in x.items()
            ) + ")"
        else:
            return "{" + ", ".join(
                abbr(k) + ": " + abbr(v)
                for k, v in x.items()
            ) + "}"
    if isinstance(x, set):
        return "{" + ", ".join(abbr(e) for e in x) + "}"
    if isinstance(x, list):
        return "[" + ", ".join(abbr(e) for e in x) + "]"
    if isinstance(x, tuple):
        if len(x) == 1:
            return "(" + abbr(x[0]) + ")"
        return "(" + ", ".join(abbr(e) for e in x) + ")"
    return repr(x)


class AtomPattern(ABC):
    """An abstract atom pattern evaluated from an expresion"""

    @abstractmethod
    def __abbr__(self):
        pass

    @abstractmethod
    def __repr__(self):
        pass


class ElementPattern(AtomPattern):
    """An abstract element (relation or entity) pattern"""

    # The tuple of the names of implicit attributes in order of nesting
    IMPLICIT_ATTRS: Tuple[str, ...] = ("_type",)

    def __init__(self, atom: 'ElementAtom', attrs: dict[str, object]):
        """
        Initialize the element pattern.

        Args:
            atom:   The element atom expression this pattern was created from.
            attrs:  The attribute dictionary.
        """
        # The element atom expression this pattern was created from
        self.atom = atom

        # Substitute implicit attrs
        if "" in attrs:
            for implicit_attr in self.IMPLICIT_ATTRS:
                if implicit_attr not in attrs:
                    attrs[implicit_attr] = attrs.pop("")
                    break
            else:
                raise NotImplementedError("Implicit attributes exhausted")

        self.attrs = attrs

    def __hash__(self):
        return hash(self.atom)

    def __eq__(self, other):
        if isinstance(other, ElementPattern):
            return self.atom == other.atom
        return NotImplemented

    def __repr__(self):
        result = abbr(self)
        explicit_attrs = self.attrs.copy()
        for implicit_attr in self.IMPLICIT_ATTRS:
            if implicit_attr not in explicit_attrs:
                break
            value = explicit_attrs.pop(implicit_attr)
            if value.isidentifier():
                result += f".{value}"
            else:
                result += f"[{value!r}]"
        if explicit_attrs:
            result += abbr(explicit_attrs)
        return result

    @abstractmethod
    def with_updated_attrs(self, attrs: dict[str, object]) -> \
            Tuple['ElementPattern', 'ElementPattern']:
        """Duplicate the pattern with attributes updated"""


class EntityPattern(ElementPattern):
    """An entity pattern"""

    # The tuple of the names of implicit attributes in order of nesting
    IMPLICIT_ATTRS = ElementPattern.IMPLICIT_ATTRS + ("_name",)

    def __init__(self, atom: 'EntityAtom', attrs: dict[str, object]):
        """
        Initialize the entity pattern.

        Args:
            atom:   The entity atom expression this pattern was created from.
            attrs:  The attribute dictionary.
        """
        assert isinstance(atom, EntityAtom)
        super().__init__(atom, attrs)
        # Make mypy happy
        self.atom: EntityAtom = atom

    def __abbr__(self):
        return repr(self.atom)

    def with_updated_attrs(self, attrs: dict[str, object]) -> \
            Tuple['EntityPattern', 'EntityPattern']:
        """Duplicate the pattern with attributes updated"""
        return self, EntityPattern(self.atom, self.attrs | attrs)


class RelationPattern(ElementPattern):
    """A relation pattern"""

    def __init__(self,
                 atom: 'RelationAtom',
                 attrs: dict[str, object],
                 roles: dict[str, ElementPattern]):
        """
        Initialize the relation pattern.

        Args:
            atom:   The relation atom expression this pattern was created
                    from.
            attrs:  The attribute dictionary.
            roles:  The role dictionary.
        """
        assert isinstance(atom, RelationAtom)
        super().__init__(atom, attrs)
        # Make mypy happy
        self.atom: RelationAtom = atom
        self.roles = roles

    def __abbr__(self):
        return repr(self.atom)

    def __repr__(self):
        return super().__repr__() + \
            (f":{abbr(self.roles)}" if self.roles else "")

    def with_updated_attrs(self, attrs: dict[str, object]) -> \
            Tuple['RelationPattern', 'RelationPattern']:
        """Duplicate the pattern with attributes updated"""
        return self, \
            RelationPattern(self.atom, self.attrs | attrs, self.roles)

    def with_updated_roles(self, roles: dict[str, EntityPattern]) -> \
            Tuple['RelationPattern', 'RelationPattern']:
        """Duplicate the pattern with roles updated"""
        return self, \
            RelationPattern(self.atom, self.attrs, self.roles | roles)


class RolePattern(AtomPattern):
    """A role pattern"""

    def __init__(self, name: str, element: None | ElementPattern):
        """
        Initialize the role pattern.

        Args:
            name:       The name of the role.
            element:    The element attached to the role, or None.
        """
        self.name = name
        self.element = element


class DetachedRolePattern(RolePattern):
    """An unattached role pattern"""

    def __init__(self, name: str):
        """
        Initialize the role pattern.

        Args:
            name:       The name of the role.
        """
        super().__init__(name, None)

    def __abbr__(self):
        return repr(self.name)

    def __repr__(self):
        return repr(self.name)

    def open(self, relation: RelationPattern) -> \
            Tuple['DetachedRolePattern', 'OpeningPattern']:
        """Open the role with a relationship"""
        return self, OpeningPattern(relation, self.name)

    def cast(self, element: ElementPattern) -> \
            Tuple['DetachedRolePattern', 'CastingPattern']:
        """Cast an element with the role"""
        return self, CastingPattern(self.name, element)


class AttachedRolePattern(RolePattern):
    """An attached (opened/cast) role pattern"""

    def __init__(self, name: str, element: ElementPattern):
        """
        Initialize the attached role pattern.

        Args:
            name:       The name of the role.
            element:    The element attached to the role.
        """
        assert isinstance(element, ElementPattern)
        super().__init__(name, element)

    @abstractmethod
    def with_replaced_element(self, element: ElementPattern) -> \
            'AttachedRolePattern':
        """Create a new attached pattern with the element replaced"""


class CastingPattern(AttachedRolePattern):
    """A role casting (an element acting a role) pattern"""

    def __abbr__(self):
        return f"{self.name!r}-{abbr(self.element)}"

    def __repr__(self):
        return f"{self.name!r}-{self.element!r}"

    def with_replaced_element(self, element: ElementPattern) -> \
            'CastingPattern':
        return CastingPattern(self.name, element)


class OpeningPattern(AttachedRolePattern):
    """A role opening (a relationship's open role) pattern"""

    def __init__(self, relation: RelationPattern, name: str):
        """
        Initialize the opening pattern.

        Args:
            relation:   The relation with the role open.
            name:       The name of the role.
        """
        super().__init__(name, relation)

    def __abbr__(self):
        return f"{abbr(self.element)}*{self.name!r}"

    def __repr__(self):
        return f"{self.element!r}*{self.name!r}"

    def with_replaced_element(self, element: ElementPattern) -> \
            'OpeningPattern':
        assert isinstance(element, RelationPattern)
        return OpeningPattern(element, self.name)


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
        assert set(elements) >= {
            element
            for relation in relations
            for element in relation.roles.values()
        }, "A relation's role is played by an unknown element"

        def get_atom_element(atom: AtomPattern):
            return atom.element if isinstance(atom, RolePattern) else atom

        left_element = get_atom_element(left)
        right_element = get_atom_element(right)
        assert left_element is None or left_element in elements, \
            "Unknown left element (reference)"
        assert right_element is None or right_element in elements, \
            "Unknown right element (reference)"

        self.graph = graph
        self.elements = elements
        self.entities = entities
        self.relations = relations
        self.left = left
        self.right = right

    def __abbr__(self):
        return f"{self.left!r} {...} {self.right!r}"

    def __repr__(self):
        if isinstance(self.left, OpeningPattern):
            left = f"{self.left.name!r}*{abbr(self.left.element)}"
        elif isinstance(self.left, CastingPattern):
            left = f"{self.left.name!r}-{abbr(self.left.element)}"
        else:
            left = abbr(self.left)

        if isinstance(self.right, OpeningPattern):
            right = f"{abbr(self.right.element)}*{self.right.name!r}"
        elif isinstance(self.right, CastingPattern):
            right = f"{abbr(self.right.element)}-{self.right.name!r}"
        else:
            right = abbr(self.right)

        return f"{left} < " + ", ".join(
            ("", "+")[c] + repr(e) for e, c in self.elements.items()
        ) + f" > {right}"

    def with_replaced_atom(self, old: AtomPattern, new: AtomPattern) -> \
            'GraphPattern':
        """Create a duplicate graph pattern with an atom pattern replaced"""
        assert not isinstance(old, ElementPattern) or old in self.elements, \
            "Replacing unknown element pattern"
        assert isinstance(old, ElementPattern) <= \
            isinstance(new, ElementPattern), \
            "Cannot downgrade element pattern to a role pattern"

        def update_elements(elements, old, new):
            if isinstance(old, ElementPattern) and \
                    isinstance(new, ElementPattern):
                elements = elements.copy()
                elements[new] = elements.pop(old)
            return elements

        def update_boundary(boundary, old, new):
            if old is boundary:
                return new
            elif isinstance(boundary, AttachedRolePattern) and \
                    boundary.element is old:
                assert isinstance(new, ElementPattern)
                return boundary.with_replaced_element(new)
            return boundary

        return GraphPattern(
            self.graph,
            update_elements(self.elements, old, new),
            update_boundary(self.left, old, new),
            update_boundary(self.right, old, new),
        )

    def __or__(self, other) -> 'GraphPattern':
        """Merge two graph patterns"""
        if isinstance(other, GraphPattern) and other.graph is self.graph:
            elements = self.elements.copy()
            for element, create in other.elements.items():
                if element in elements:
                    create = max(elements[element], create)
                elements[element] = create
            return GraphPattern(self.graph, elements, self.left, other.right)
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
        raise ValueError

    def __getitem__(self, key) -> 'UpdateOp':
        """Create an implicit attribute update operator"""
        if isinstance(self._right_atom, ElementAtom) and isinstance(key, str):
            return UpdateOp(self, {"": key})
        raise ValueError

    def __call__(self, **attrs) -> 'UpdateOp':
        """Create an attribute update operator"""
        if isinstance(self._right_atom, ElementAtom):
            return UpdateOp(self, attrs)
        raise ValueError

    def __sub__(self, other) -> 'CastOp':
        """Create a role-casting operator for S - O expression """
        if isinstance(other, str):
            other = RoleAtom(self._graph, other)
        if CastOp.args_are_valid(self, other):
            return CastOp(self, other)
        return NotImplemented

    def __rsub__(self, other) -> 'CastOp':
        """Create a role-casting operator for O - S expression """
        if isinstance(other, str):
            other = RoleAtom(self._graph, other)
        if CastOp.args_are_valid(other, self):
            return CastOp(other, self)
        return NotImplemented

    def __mul__(self, other) -> 'OpenOp':
        """Create a role-opening operator for S * O expression """
        if isinstance(other, str):
            other = RoleAtom(self._graph, other)
        if OpenOp.args_are_valid(self, other):
            return OpenOp(self, other)
        return NotImplemented

    def __rmul__(self, other) -> 'OpenOp':
        """Create a role-opening operator for O * S expression """
        if isinstance(other, str):
            other = RoleAtom(self._graph, other)
        if OpenOp.args_are_valid(other, self):
            return OpenOp(other, self)
        return NotImplemented

    @staticmethod
    def __shift(left, op, right) -> 'CastOp':
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
            relation = left._graph.relation
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

    def __rshift__(self, other) -> 'CastOp':
        """Create edge/role expression for S >> O expression"""
        return Expr.__shift(self, ">>", other)

    def __rrshift__(self, other) -> 'CastOp':
        """Create edge/role expression for O >> S expression"""
        return Expr.__shift(other, ">>", self)

    def __lshift__(self, other) -> 'CastOp':
        """Create edge/role expression for S << O expression"""
        return Expr.__shift(self, "<<", other)

    def __rlshift__(self, other) -> 'CastOp':
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
        pattern = DetachedRolePattern(self._name)
        return GraphPattern(self._graph, {}, pattern, pattern)


class ElementAtom(Atom):
    """An element atom"""

    # Relax, pylint: disable=redefined-builtin
    def __init__(self, graph: Graph, id: int):
        """
        Initialize the element atom.

        Args:
            graph:  The graph the element belongs to.
            id:     The integer the element is identified by within its graph.
        """
        assert isinstance(graph, Graph)
        assert isinstance(id, int)
        super().__init__(graph)
        self.id = id

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        if isinstance(other, ElementAtom):
            return self.id == other.id
        return NotImplemented


class EntityAtom(ElementAtom):
    """An entity operand"""

    def __repr__(self):
        return f"e{self.id >> 1}"

    def _eval(self):
        pattern = EntityPattern(self, {})
        return GraphPattern(self._graph, {pattern: False}, pattern, pattern)


class RelationAtom(ElementAtom):
    """A relation operand"""

    def __repr__(self):
        return f"r{self.id >> 1}"

    def _eval(self):
        pattern = RelationPattern(self, {}, {})
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
            raise ValueError
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

        # If we're trying to open an opening
        if isinstance(left_atom, OpeningPattern) or \
                isinstance(right_atom, OpeningPattern):
            raise ValueError

        assert (
            isinstance(left_atom, RelationPattern) and
            isinstance(right_atom, (DetachedRolePattern, CastingPattern)) or
            isinstance(left_atom, (DetachedRolePattern, CastingPattern)) and
            isinstance(right_atom, RelationPattern)
        )

        # If the relation is on the left
        if isinstance(left_atom, RelationPattern):
            relation = left_atom
            role_or_casting = right_atom
        # Else, the role is on the right
        else:
            role_or_casting = left_atom
            relation = right_atom

        # If we're completing a role
        if isinstance(role_or_casting, CastingPattern):
            return (left_graph | right_graph).with_replaced_atom(
                *relation.with_updated_roles(
                    {role_or_casting.name: role_or_casting.element}
                )
            )
        # Else, we're opening a role with the relation
        else:
            return (left_graph | right_graph).with_replaced_atom(
                *role_or_casting.open(relation)
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

        print("left_graph:", left_graph)
        print("right_graph:", right_graph)
        print("left_atom:", left_atom)
        print("right_atom:", right_atom)

        # If we're trying to cast a casting
        if isinstance(left_atom, CastingPattern) or \
                isinstance(right_atom, CastingPattern):
            raise ValueError

        assert (
            isinstance(left_atom, ElementPattern) and
            isinstance(right_atom, (DetachedRolePattern, OpeningPattern)) or
            isinstance(left_atom, (DetachedRolePattern, OpeningPattern)) and
            isinstance(right_atom, ElementPattern)
        )

        # If the element is on the left
        if isinstance(left_atom, ElementPattern):
            element = left_atom
            role_or_opening = right_atom
        # Else, the element is on the right
        else:
            role_or_opening = left_atom
            element = right_atom

        print("merged_graph:", left_graph | right_graph)

        # If we're completing a role
        if isinstance(role_or_opening, OpeningPattern):
            print("replacement:",
                  role_or_opening.element.with_updated_roles(
                      {role_or_opening.name: element}
                  ))
            return (left_graph | right_graph).with_replaced_atom(
                *role_or_opening.element.with_updated_roles(
                    {role_or_opening.name: element}
                )
            )
        # Else, we're casting an element for the role
        else:
            return (left_graph | right_graph).with_replaced_atom(
                *role_or_opening.cast(element)
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
