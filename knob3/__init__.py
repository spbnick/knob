"""
KNOB - Knowledge builder - a module for creating knowledge (hyper)graphs.

An element is either an entity or a relation.
An element can contain attributes.
Relations can contain roles.
Roles can be played by elements (either entities or roles).

Actually, could we make all elements equal and simply allow attributes to
reference other elements and call such attributes "roles"? And then call
elements with roles "relations"?

This can make things much simpler to understand, think about, and implement.
"""

from typing import Dict, Set, Tuple
from functools import reduce
from itertools import product


class Element:
    """A graph element"""

    def __init__(self, attrs:Dict[str, str]):
        """
        Initialize an element.

        Args:
            attrs:  A dictionary of the elment's attribute names and values.
        """
        self.attrs = attrs.copy()


class Role:
    """A graph role"""

    def __init__(self, name: str, relation: Element, actor: Element):
        """
        Initialize a graph role.

        Args:
            name:       The name of the role.
            relation:   The role's relation element.
            actor:      The role's actor element.
        """
        self.name = name
        self.relation = relation
        self.actor = actor

    def __hash__(self):
        return hash((self.name, self.relation, self.actor))

    def __eq__(self, other):
        if not isinstance(other, RolePattern):
            return NotImplemented
        return self.name == other.name and \
            self.relation == other.relation and \
            self.actor == other.actor


class ElementPattern:
    """A graph element pattern"""
    def __init__(self, attrs:Dict[str, str], create: bool):
        """
        Initialize a graph element pattern.

        Args:
            attrs:  A dictionary of the element's attribute names and values
                    to be matched/created.
            create: False, if the element should be matched. True, if created.
        """
        self.attrs = attrs.copy()
        self.create = create

    def matches(self, element: Element):
        """
        Check if the pattern matches an element.

        Args:
            element:    The element to match the pattern against.

        Returns:
            True, if the pattern matches the element. False, if not.
        """
        return set(self.attrs.items()) <= set(element.attrs.items())


class RolePattern:
    """A graph's role pattern"""

    def __init__(self, name: str,
                 relation: ElementPattern, actor: ElementPattern):
        """
        Initialize a graph's role pattern.

        Args:
            name:       The name of the role.
            relation:   The role's relation element pattern.
            actor:      The role's actor element pattern.
        """
        self.name = name
        self.relation = relation
        self.actor = actor

    def __hash__(self):
        return hash((self.name, self.relation, self.actor))

    def __eq__(self, other):
        if not isinstance(other, RolePattern):
            return NotImplemented
        return self.name == other.name and \
            self.relation == other.relation and \
            self.actor == other.actor


class GraphPattern:
    """A pattern matching/creating a subgraph"""

    def __init__(self,
                 element_patterns: Set[ElementPattern],
                 role_patterns: Set[RolePattern]):
        """
        Initialize a graph pattern.

        Args:
            element_patterns:   A set of patterns for elements to match/create.
            role_patterns:      A set of patterns for roles to match/create.
                                Must reference element patterns from
                                "element_patterns" only.
        """
        assert element_patterns >= {
            element_pattern
            for role_pattern in role_patterns
            for element_pattern in (role_pattern.relation, role_pattern.actor)
        }
        self.element_patterns = element_patterns.copy()
        self.role_patterns = role_patterns.copy()


class Graph:
    """A graph"""

    def __init__(self, elements: Set[Element], roles: Set[Roles]):
        """
        Initialize a graph.

        Args:
            elements:   A set of elements belonging to the graph.
            roles:      A set of roles connecting the elements.
        """
        assert elements >= {
            element
            for role in roles
            for element in (role.relation, role.actor)
        }
        self.elements = elements.copy()
        self.roles = roles.copy()


    def match(self, pattern: GraphPattern) -> Graph:
        """
        Return the subgraph matching the matching part of a graph pattern.

        Args:
            pattern:    The graph pattern to apply.

        Returns:
            A graph containing the matched elements and roles.
        """
        # A dictionary of matching element patterns and
        # sets of elements they match
        element_patterns_elements = {
            element_pattern: set(
                filter(element_pattern.matches, self.elements)
            )
            for element_pattern in pattern.element_patterns
            if not element_pattern.create
        }
        # If any element patterns matched nothing
        if not all(element_patterns_elements.values()):
            return None

        # A dictionary of matching role patterns and
        # sets of roles they match
        role_patterns_roles = {
            role_pattern: {
                role
                for role in (
                    Role(role_pattern.name, relation, actor)
                    for (relation, actor) in product(
                        element_patterns_elements[role_pattern.relation],
                        element_patterns_elements[role_pattern.actor]
                    )
                ) if role in self.roles
            }
            for role_pattern in pattern.role_patterns
            if role_pattern.relation in element_patterns_elements and
            role_pattern.actor in element_patterns_elements and
        }
        # If any role patterns matched nothing
        if not all(role_patterns_roles.values()):
            return None

        # Intersect elements in element patterns with elements in role
        # patterns they are involved in.
        # TODO: HMMM, SHOULD WE DO TWO LOOPS?
        for element_pattern, elements in element_patterns_elements.items():
            for role_pattern, roles in role_patterns_roles.items():
                if element_pattern is role_pattern.relation:
                    elements &= {role.relation for role in roles}
                    roles &= {
                        role for role in roles if role.relation in elements
                    }
                if element_pattern is role_pattern.actor:
                    elements &= {role.actor for role in roles}
                    roles &= {
                        role for role in roles if role.actor in elements
                    }

        # If any element patterns have no elements remaining
        if not all(element_patterns_elements.values()):
            return None
        # If any role patterns have no roles remaining
        if not all(role_patterns_roles.values()):
            return None

        # Return the matched subgraph
        return Graph(
            reduce(lambda x, y: x | y,
                   element_patterns_elements.values(),
                   set()),
            reduce(lambda x, y: x | y,
                   role_patterns_roles.values(),
                   set())
        )

    def apply(self, pattern: GraphPattern) -> Graph:
        """
        Apply a graph pattern to the graph, creating the elements and the
        roles requested by the pattern, if any.

        Args:
            pattern:    The graph pattern to apply.

        Returns:
            A graph containing elements and roles added to the graph (can be
            empty), if the pattern applied, or None, if it didn't.
        """
