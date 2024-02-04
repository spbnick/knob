"""
KNOB - Knowledge builder - knowledge (hyper)graph.

NOTE: All binary graph operators are left-associative
"""

from typing import Tuple, Union, Optional
from abc import ABC, abstractmethod

# We're being abstract here,
# pylint: disable=too-few-public-methods,too-many-ancestors,invalid-name

# No, I like it this way, pylint: disable=no-else-return
# We like our "id", pylint: disable=redefined-builtin


class Graph:
    """A knowledge graph"""

    def __init__(self):
        """Initialize the knowledge graph"""
        # The ID next created entity pattern will use
        self.next_entity_id = 0
        # The ID next created relation pattern will use
        self.next_relation_id = 0

    @property
    def entity(self):
        """A graph pattern matching a unique entity"""
        ep = EntityPattern(self.next_entity_id << 1, {})
        self.next_entity_id += 1
        return GraphPattern(self, {ep: False}, ep, ep)

    @property
    def e(self):
        """An alias for 'entity'"""
        return self.entity

    @property
    def relation(self):
        """A graph pattern matching a unique relation"""
        rp = RelationPattern(self.next_relation_id << 1 | 1, {}, {})
        self.next_relation_id += 1
        return GraphPattern(self, {rp: False}, rp, rp)

    @property
    def r(self):
        """An alias for 'relation'"""
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
    """An abstract atom pattern"""

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

    def __init__(self, id: int, attrs: dict[str, Union[str, int]]):
        """
        Initialize the element pattern.

        Args:
            id:     The element ID.
            attrs:  The attribute dictionary.
        """
        # The element ID
        self.id = id

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
        return self.id

    def __eq__(self, other):
        if isinstance(other, ElementPattern):
            return self.id == other.id
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
    def __or__(self, other) -> 'ElementPattern':
        """Merge two instances of the element pattern together"""

    @abstractmethod
    def with_updated_attrs(self, attrs: dict[str, Union[str, int]]) -> \
            Tuple['ElementPattern', 'ElementPattern']:
        """Duplicate the pattern with attributes updated"""


class EntityPattern(ElementPattern):
    """An entity pattern"""

    # The tuple of the names of implicit attributes in order of nesting
    IMPLICIT_ATTRS = ElementPattern.IMPLICIT_ATTRS + ("_name",)

    def __abbr__(self):
        return f"e{self.id >> 1}"

    def with_updated_attrs(self, attrs: dict[str, Union[str, int]]) -> \
            Tuple['EntityPattern', 'EntityPattern']:
        """Duplicate the pattern with attributes updated"""
        return self, EntityPattern(self.id, self.attrs | attrs)

    def __or__(self, other) -> 'EntityPattern':
        """Merge two instances of the entity pattern together"""
        if other is self:
            return self
        if not isinstance(other, EntityPattern):
            return NotImplemented
        if other.id != self.id:
            raise ValueError
        return EntityPattern(self.id, self.attrs | other.attrs)


class RelationPattern(ElementPattern):
    """A relation pattern"""

    def __init__(self,
                 id: int,
                 attrs: dict[str, Union[str, int]],
                 roles: dict[str, ElementPattern]):
        """
        Initialize the relation pattern.

        Args:
            id:     The relation element ID.
            attrs:  The attribute dictionary.
            roles:  The role dictionary.
        """
        super().__init__(id, attrs)
        self.roles = roles

    def __abbr__(self):
        return f"r{self.id >> 1}"

    def __repr__(self):
        return super().__repr__() + \
            (f":{abbr(self.roles)}" if self.roles else "")

    def with_updated_attrs(self, attrs: dict[str, Union[str, int]]) -> \
            Tuple['RelationPattern', 'RelationPattern']:
        """Duplicate the pattern with attributes updated"""
        return self, \
            RelationPattern(self.id, self.attrs | attrs, self.roles)

    def with_updated_roles(self, roles: dict[str, ElementPattern]) -> \
            Tuple['RelationPattern', 'RelationPattern']:
        """Duplicate the pattern with roles updated"""
        return self, \
            RelationPattern(self.id, self.attrs, self.roles | roles)

    def __or__(self, other) -> 'RelationPattern':
        """Merge two instances of the relation pattern together"""
        if other is self:
            return self
        if not isinstance(other, RelationPattern):
            return NotImplemented
        if other.id != self.id:
            raise ValueError
        return RelationPattern(self.id, self.attrs | other.attrs,
                               self.roles | other.roles)


class RolePattern(AtomPattern):
    """A role pattern"""

    def __init__(self, name: str, element: Optional[ElementPattern]):
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
        # Satisfy mypy
        self.element: None = None

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
        # Satisfy mypy
        self.element: ElementPattern = element

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
        # Satisfy mypy
        self.element: RelationPattern = relation

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
                        dictionary can only reference element patterns from
                        the same dictionary.
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

        gp = GraphPattern(
            self.graph,
            update_elements(self.elements, old, new),
            update_boundary(self.left, old, new),
            update_boundary(self.right, old, new),
        )
        # print(f"{self} . with_replaced_atom({old}, {new}) -> {gp}")
        return gp

    def __or__(self, other) -> 'GraphPattern':
        """Merge two graph patterns"""
        if not isinstance(other, GraphPattern):
            return NotImplemented
        if other.graph is not self.graph:
            raise ValueError

        elements = self.elements.copy()
        id_elements = {e.id: e for e in elements}
        for element, create in other.elements.items():
            if element.id in id_elements:
                element = id_elements[element.id] | element
            id_elements[element.id] = element
            elements.pop(element, None)
            elements[element] = create

        def update_boundary(boundary):
            if isinstance(boundary, AttachedRolePattern):
                return boundary.with_replaced_element(
                    id_elements[boundary.element.id]
                )
            elif isinstance(boundary, ElementPattern):
                return id_elements[boundary.id]
            return boundary

        return GraphPattern(
            self.graph,
            elements,
            update_boundary(self.left),
            update_boundary(other.right)
        )

    def __pos__(self):
        """Enable creation of all elements in the graph pattern"""
        return GraphPattern(
            self.graph,
            {element: True for element in self.elements},
            self.left,
            self.right
        )

    def __neg__(self):
        """Disable creation of all elements in the graph pattern"""
        return GraphPattern(
            self.graph,
            {element: False for element in self.elements},
            self.left,
            self.right
        )

    def __getattr__(self, key: str) -> 'GraphPattern':
        """Update the implicit attribute of the right element"""
        return self[key]

    def __getitem__(self, key) -> 'GraphPattern':
        """Update the implicit attribute of the right element"""
        atom = self.right
        if isinstance(atom, ElementPattern):
            return self.with_replaced_atom(
                *atom.with_updated_attrs({"": key})
            )
        raise ValueError

    def __call__(self, **attrs) -> 'GraphPattern':
        """Update attributes of the right element"""
        atom = self.right
        if isinstance(atom, ElementPattern):
            return self.with_replaced_atom(
                *atom.with_updated_attrs(attrs)
            )
        raise ValueError

    @staticmethod
    def _cast(left, right) -> 'GraphPattern':
        """Cast an element in an opened or detached role"""
        # This will do, pylint: disable=too-many-branches
        assert isinstance(left, GraphPattern) or \
            isinstance(right, GraphPattern)

        if isinstance(left, str):
            left = DetachedRolePattern(left)
            left = GraphPattern(right.graph, {}, left, left)
        elif not isinstance(left, GraphPattern):
            return NotImplemented

        if isinstance(right, str):
            right = DetachedRolePattern(right)
            right = GraphPattern(left.graph, {}, right, right)
        elif not isinstance(right, GraphPattern):
            return NotImplemented

        if left.graph is not right.graph:
            raise ValueError

        left_atom = left.right
        right_atom = right.left

        # If the element is on the left
        if isinstance(left_atom, ElementPattern):
            element = left_atom
            if isinstance(right_atom, (DetachedRolePattern, OpeningPattern)):
                role_or_opening = right_atom
            else:
                raise ValueError
        # Else, if the element is on the right
        elif isinstance(right_atom, ElementPattern):
            element = right_atom
            if isinstance(left_atom, (DetachedRolePattern, OpeningPattern)):
                role_or_opening = left_atom
            else:
                raise ValueError
        else:
            raise ValueError

        # If we're completing a role
        if isinstance(role_or_opening, OpeningPattern):
            return (left | right).with_replaced_atom(
                *role_or_opening.element.with_updated_roles(
                    {role_or_opening.name: element}
                )
            )
        # Else, we're casting an element for the role
        else:
            return (left | right).with_replaced_atom(
                *role_or_opening.cast(element)
            )

    def __sub__(self, other) -> 'GraphPattern':
        """Cast a role (for S - O expression)"""
        return self._cast(self, other)

    def __rsub__(self, other) -> 'GraphPattern':
        """Cast a role (for O - S expression)"""
        return self._cast(other, self)

    @staticmethod
    def _open(left, right) -> 'GraphPattern':
        """Open a detached or cast role in a relation"""
        # This will do, pylint: disable=too-many-branches
        assert isinstance(left, GraphPattern) or \
            isinstance(right, GraphPattern)

        if isinstance(left, str):
            left = DetachedRolePattern(left)
            left = GraphPattern(right.graph, {}, left, left)
        elif not isinstance(left, GraphPattern):
            return NotImplemented

        if isinstance(right, str):
            right = DetachedRolePattern(right)
            right = GraphPattern(left.graph, {}, right, right)
        elif not isinstance(right, GraphPattern):
            return NotImplemented

        if left.graph is not right.graph:
            raise ValueError

        left_atom = left.right
        right_atom = right.left

        # If the relation is on the left
        if isinstance(left_atom, RelationPattern):
            relation = left_atom
            if isinstance(right_atom, (DetachedRolePattern, CastingPattern)):
                role_or_casting = right_atom
            else:
                raise ValueError
        # Else, if the role is on the right
        elif isinstance(right_atom, RelationPattern):
            relation = right_atom
            if isinstance(left_atom, (DetachedRolePattern, CastingPattern)):
                role_or_casting = left_atom
            else:
                raise ValueError
        else:
            raise ValueError

        # If we're completing a role
        if isinstance(role_or_casting, CastingPattern):
            return (left | right).with_replaced_atom(
                *relation.with_updated_roles(
                    {role_or_casting.name: role_or_casting.element}
                )
            )
        # Else, we're opening a role with the relation
        else:
            return (left | right).with_replaced_atom(
                *role_or_casting.open(relation)
            )

    def __mul__(self, other) -> 'GraphPattern':
        """Open a role (for S * O expression)"""
        return self._open(self, other)

    def __rmul__(self, other) -> 'GraphPattern':
        """Open a role (for O * S expression)"""
        return self._open(other, self)

    @staticmethod
    def _shift(left, op: str, right) -> 'GraphPattern':
        """Create an expression for a shift operator"""
        # No it's not, pylint: disable=too-many-return-statements
        assert op in {"<<", ">>"}

        if not isinstance(left, GraphPattern) or \
           not isinstance(right, GraphPattern):
            return NotImplemented

        if left.graph is not right.graph:
            raise ValueError

        ltr = op == ">>"
        left_atom = left.right
        right_atom = right.left

        if isinstance(left_atom, EntityPattern) and \
           isinstance(right_atom, EntityPattern):
            relation = left.graph.relation
            if ltr:
                return left - "source" * relation * "target" - right
            else:
                return left - "target" * relation * "source" - right
        elif isinstance(left_atom, RelationPattern) and \
                isinstance(right_atom, EntityPattern):
            if ltr:
                return left * "target" - right
            else:
                return left * "source" - right
        elif isinstance(left_atom, EntityPattern) and \
                isinstance(right_atom, RelationPattern):
            if ltr:
                return left - "source" * right
            else:
                return left - "target" * right

        raise ValueError

    def __rshift__(self, other) -> 'GraphPattern':
        """Create edge/role with other graph pattern, for S >> O expression"""
        return self._shift(self, ">>", other)

    def __rrshift__(self, other) -> 'GraphPattern':
        """Create edge/role with other graph pattern, for O >> S expression"""
        return self._shift(other, ">>", self)

    def __lshift__(self, other) -> 'GraphPattern':
        """Create edge/role with other graph pattern, for S << O expression"""
        return self._shift(self, "<<", other)

    def __rlshift__(self, other) -> 'GraphPattern':
        """Create edge/role with other graph pattern, for O << S expression"""
        return self._shift(other, "<<", self)
