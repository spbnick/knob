"""
KNOB - Knowledge builder - knowledge (hyper)graph.

NOTE: All binary graph operators are left-associative
"""

from typing import Tuple, Union
from abc import ABC, abstractmethod

# We're being abstract here,
# pylint: disable=too-few-public-methods,too-many-ancestors,invalid-name

# No, I like it this way, pylint: disable=no-else-return
# We like our "id", pylint: disable=redefined-builtin


class Graph:
    """A knowledge graph"""

    def __init__(self):
        """Initialize the knowledge graph"""

    @property
    def entity(self):
        """A graph pattern matching a unique entity"""
        return EntityGraphPattern()

    @property
    def e(self):
        """An alias for 'entity'"""
        return self.entity

    @property
    def relation(self):
        """A graph pattern matching a unique relation"""
        return RelationGraphPattern()

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

    # The ID next created element pattern can use
    __NEXT_ID = 1

    # The tuple of the names of implicit attributes in order of nesting
    IMPLICIT_ATTRS: Tuple[str, ...] = ("_type",)

    def __init__(self, id: int, attrs: dict[str, Union[str, int]]):
        """
        Initialize the element pattern.

        Args:
            id:     The element ID. Zero to assign next available.
            attrs:  The attribute dictionary.
        """
        # The element ID
        if id == 0:
            id = ElementPattern.__NEXT_ID
            ElementPattern.__NEXT_ID += 1
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

    def attrs_repr(self):
        """Generate a string representation of element attributes"""
        result = ""
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

    def __repr__(self):
        return abbr(self) + self.attrs_repr()

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
        return f"e#{self.id}"

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
                 roles: dict[str, int]):
        """
        Initialize the relation pattern.

        Args:
            id:     The relation element ID. Zero to assign next available.
            attrs:  The attribute dictionary.
            roles:  A dictionary of role names and the IDs of actor elements.
        """
        super().__init__(id, attrs)
        self.roles = roles

    def __abbr__(self):
        return f"r#{self.id}"

    def __repr__(self):
        return super().__repr__() + (
            ":(" + ", ".join(
                (n if n.isidentifier() else repr(n)) + "=#" + str(a_id)
                for n, a_id in self.roles.items()
            ) + ")" if self.roles else ""
        )

    def with_updated_attrs(self, attrs: dict[str, Union[str, int]]) -> \
            Tuple['RelationPattern', 'RelationPattern']:
        """Duplicate the pattern with attributes updated"""
        return self, \
            RelationPattern(self.id, self.attrs | attrs, self.roles)

    def with_updated_roles(self, roles: dict[str, int]) -> \
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

    def __init__(self, name: str, element_id: int):
        """
        Initialize the role pattern.

        Args:
            name:       The name of the role.
            element_id: The ID of the element attached to the role,
                        or zero, if none.
        """
        assert isinstance(name, str)
        assert isinstance(element_id, int)
        self.name = name
        self.element_id = element_id


class DetachedRolePattern(RolePattern):
    """An unattached role pattern"""

    def __init__(self, name: str):
        """
        Initialize the role pattern.

        Args:
            name:       The name of the role.
        """
        assert isinstance(name, str)
        super().__init__(name, 0)

    def __abbr__(self):
        return repr(self.name)

    def __repr__(self):
        return repr(self.name)

    def open(self, relation_id: int) -> \
            Tuple['DetachedRolePattern', 'OpeningPattern']:
        """Open the role with a relationship"""
        return self, OpeningPattern(relation_id, self.name)

    def cast(self, element_id: int) -> \
            Tuple['DetachedRolePattern', 'CastingPattern']:
        """Cast an element with the role"""
        return self, CastingPattern(self.name, element_id)


class AttachedRolePattern(RolePattern):
    """An attached (opened/cast) role pattern"""

    def __init__(self, name: str, element_id: int):
        """
        Initialize the attached role pattern.

        Args:
            name:       The name of the role.
            element_id: The ID of the element attached to the role.
        """
        assert isinstance(name, str)
        assert isinstance(element_id, int)
        super().__init__(name, element_id)

    @abstractmethod
    def with_replaced_element_id(self, element_id: int) -> \
            'AttachedRolePattern':
        """Create a new attached pattern with the element ID replaced"""


class CastingPattern(AttachedRolePattern):
    """A role casting (an element acting a role) pattern"""

    def __abbr__(self):
        return f"{self.name!r}-#{self.element_id}"

    def __repr__(self):
        return f"{self.name!r}-#{self.element_id}"

    def with_replaced_element_id(self, element_id: int) -> \
            'CastingPattern':
        return CastingPattern(self.name, element_id)


class OpeningPattern(AttachedRolePattern):
    """A role opening (a relationship's open role) pattern"""

    def __init__(self, relation_id: int, name: str):
        """
        Initialize the opening pattern.

        Args:
            relation_id:    The ID of the relation with the role open.
            name:           The name of the role.
        """
        super().__init__(name, relation_id)

    def __abbr__(self):
        return f"#{self.element_id}*{self.name!r}"

    def __repr__(self):
        return f"#{self.element_id}*{self.name!r}"

    def with_replaced_element_id(self, element_id: int) -> \
            'OpeningPattern':
        assert isinstance(element_id, int)
        return OpeningPattern(element_id, self.name)


class GraphPattern:
    """A graph pattern"""

    def __init__(self,
                 elements: dict[int, ElementPattern],
                 marks: set[int],
                 left: AtomPattern,
                 right: AtomPattern):
        """
        Initialize the graph pattern.

        Args:
            elements:   A dictionary of element IDs and corresponding element
                        patterns. The pattern IDs must match corresponding
                        dictionary keys.
            marks:      A set of IDs of marked elements. Must be a subset of
                        "elements" keys.
            left:       The left-side atom pattern to use when using the
                        graph pattern on the right side of an operator.
                        Must be, or refer to, an element in "elements".
            right:      The right-side atom pattern to use when using the
                        graph pattern on the left side of an operator.
                        Must be, or refer to, an element in "elements".
        """
        assert isinstance(elements, dict)
        assert all(isinstance(id, int) and
                   isinstance(e, ElementPattern) and
                   id == e.id
                   for id, e in elements.items())
        assert isinstance(marks, set)
        assert marks <= set(elements)
        assert all(
            a_id in elements
            for e in elements.values() if isinstance(e, RelationPattern)
            for a_id in e.roles.values()
        ), "A relation references an unknown actor element"

        def get_atom_id(atom: AtomPattern):
            if isinstance(atom, RolePattern):
                return atom.element_id
            elif isinstance(atom, ElementPattern):
                return atom.id
            else:
                assert False, f"Unexpected atom type {type(atom)}"
                return 0

        left_id = get_atom_id(left)
        right_id = get_atom_id(right)
        assert left_id == 0 or left_id in elements, \
            "Unknown left element (reference)"
        assert right_id == 0 or right_id in elements, \
            "Unknown right element (reference)"

        self.elements = elements
        self.marks = marks
        self.left = left
        self.right = right

    def __abbr__(self):
        return f"{self.left!r} {...} {self.right!r}"

    def __repr__(self):
        # It's OK, pylint: disable=too-many-branches

        # A list of entity IDs
        entity_ids = []
        # A list of relation IDs
        relation_ids = []
        # A dictionary of element IDs and repr (signature, body) tuples
        reprs = {}

        # Generate pattern-unique element signatures
        for id, element in self.elements.items():
            if isinstance(element, EntityPattern):
                entity_ids.append(id)
                reprs[id] = (f"e{len(entity_ids)}",)
            elif isinstance(element, RelationPattern):
                relation_ids.append(id)
                reprs[id] = (f"r{len(relation_ids)}",)
        # Generate element bodies
        for id, element in self.elements.items():
            body = element.attrs_repr()
            if isinstance(element, RelationPattern):
                if any(not n.isidentifier() for n in element.roles):
                    body += ":{" + ", ".join(
                        repr(n) + ": " + reprs[a_id][0]
                        for n, a_id in element.roles.items()
                    ) + "}"
                elif element.roles:
                    body += ":(" + ", ".join(
                        n + "=" + reprs[a_id][0]
                        for n, a_id in element.roles.items()
                    ) + ")"
            reprs[id] += (body,)

        if isinstance(self.left, OpeningPattern):
            left = f"{self.left.name!r}*{reprs[self.left.element_id][0]}"
        elif isinstance(self.left, CastingPattern):
            left = f"{self.left.name!r}-{reprs[self.left.element_id][0]}"
        elif isinstance(self.left, ElementPattern):
            left = reprs[self.left.id][0]
        else:
            left = abbr(self.left)

        if isinstance(self.right, OpeningPattern):
            right = f"{reprs[self.right.element_id][0]}*{self.right.name!r}"
        elif isinstance(self.right, CastingPattern):
            right = f"{reprs[self.right.element_id][0]}-{self.right.name!r}"
        elif isinstance(self.right, ElementPattern):
            right = reprs[self.right.id][0]
        else:
            right = abbr(self.right)

        return f"{left} < " + ", ".join(
            ("", "+")[id in self.marks] + "".join(reprs[id])
            for id in (entity_ids + relation_ids)
        ) + f" > {right}"

    def with_replaced_atom(self, old: AtomPattern, new: AtomPattern) -> \
            'GraphPattern':
        """Create a duplicate graph pattern with an atom pattern replaced"""
        assert not isinstance(old, ElementPattern) or \
            old.id in self.elements, "Replacing unknown element pattern"
        assert isinstance(old, ElementPattern) <= \
            isinstance(new, ElementPattern), \
            "Cannot downgrade element pattern to a role pattern"

        def update_elements(elements, old, new):
            if isinstance(old, ElementPattern) and \
                    isinstance(new, ElementPattern):
                assert old.id == new.id, \
                    f"New element has different ID ({new.id != old.id})"
                elements = elements.copy()
                elements[new.id] = new
            return elements

        def update_boundary(boundary, old, new):
            if old is boundary:
                return new
            elif isinstance(boundary, AttachedRolePattern) and \
                    isinstance(old, ElementPattern) and \
                    boundary.element_id == old.id:
                assert isinstance(new, ElementPattern)
                return boundary.with_replaced_element_id(new.id)
            return boundary

        gp = GraphPattern(
            update_elements(self.elements, old, new),
            self.marks,
            update_boundary(self.left, old, new),
            update_boundary(self.right, old, new),
        )
        # print(f"{self} . with_replaced_atom({old}, {new}) -> {gp}")
        return gp

    def __or__(self, other) -> 'GraphPattern':
        """Merge two graph patterns"""
        if not isinstance(other, GraphPattern):
            return NotImplemented
        elements = self.elements.copy()
        for id, element in other.elements.items():
            elements[id] = elements.get(id, element) | element
        return GraphPattern(elements, other.marks, self.left, other.right)

    def __pos__(self):
        """Mark all elements in the graph pattern"""
        return GraphPattern(
            self.elements,
            set(self.elements),
            self.left,
            self.right
        )

    def __neg__(self):
        """Unmark all elements in the graph pattern"""
        return GraphPattern(
            self.elements,
            set(),
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
            left = GraphPattern({}, set(), left, left)
        elif not isinstance(left, GraphPattern):
            return NotImplemented

        if isinstance(right, str):
            right = DetachedRolePattern(right)
            right = GraphPattern({}, set(), right, right)
        elif not isinstance(right, GraphPattern):
            return NotImplemented

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
            combined = left | right
            relation = combined.elements[role_or_opening.element_id]
            return combined.with_replaced_atom(*relation.with_updated_roles(
                {role_or_opening.name: element.id}
            ))
        # Else, we're casting an element for the role
        else:
            return (left | right).with_replaced_atom(
                *role_or_opening.cast(element.id)
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
            left = GraphPattern({}, set(), left, left)
        elif not isinstance(left, GraphPattern):
            return NotImplemented

        if isinstance(right, str):
            right = DetachedRolePattern(right)
            right = GraphPattern({}, set(), right, right)
        elif not isinstance(right, GraphPattern):
            return NotImplemented

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
                    {role_or_casting.name: role_or_casting.element_id}
                )
            )
        # Else, we're opening a role with the relation
        else:
            return (left | right).with_replaced_atom(
                *role_or_casting.open(relation.id)
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

        ltr = op == ">>"
        left_atom = left.right
        right_atom = right.left

        if isinstance(left_atom, EntityPattern) and \
           isinstance(right_atom, EntityPattern):
            relation = RelationGraphPattern()
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


class EntityGraphPattern(GraphPattern):
    """A single-entity graph pattern"""

    def __init__(self, **attrs: Union[str, int]):
        """
        Initialize the single-entity graph pattern.

        Args:
            attrs:  The attribute dictionary.
        """
        ep = EntityPattern(0, attrs)
        super().__init__({ep.id: ep}, set(), ep, ep)


class RelationGraphPattern(GraphPattern):
    """A single-relation graph pattern"""

    def __init__(self, **attrs: Union[str, int]):
        """
        Initialize the single-relation graph pattern.

        Args:
            attrs:  The relation's attribute dictionary.
        """
        rp = RelationPattern(0, attrs, {})
        super().__init__({rp.id: rp}, set(), rp, rp)
