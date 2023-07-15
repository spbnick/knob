"""
KNOB - Knowledge builder - a module for creating knowledge (hyper)graphs.

An overview of various types and how they're used:

    Graph:
        entities: EntityDomainAccessor
        relations: RelationDomainAccessor

    EntityDomainAccessor:
        __getattr__(type_name): EntityTypeAccessor
        __getitem__(type_name): EntityTypeAccessor

    EntityTypeAccessor:
        __getattr__(name): EntityReference
        __getitem__(name): EntityReference

    EntityReference:
        __lshift__(EntityReference): EntityReference
        __rshift__(EntityReference): EntityReference
        __lshift__(RelationTemplate): RelationTemplate
        __rshift__(RelationTemplate): RelationTemplate

    RelationDomainAccessor:
        __getattr__(type_name): RelationTemplate
        __getitem__(type_name): RelationTemplate

    RelationTemplate:
        __call__(attrs_and_roles): RelationTemplate
        __lshift__(EntityReference): EntityReference
        __rshift__(EntityReference): EntityReference

Access patterns:

    Graph
     |
     |    EntityDomainAccessor
     |     |
     |     |       EntityTypeAccessor
     |     |        |
     |     |        |     EntityReference
     |     |        |      |
     v     v        v      v
    graph.entities.<type>.<name>(**attrs)

    Graph
     |
     |    RelationDomainAccessor
     |     |
     |     |       RelationTemplate
     |     |        |
     v     v        v
    graph.relations.<type>(**attrs_and_roles) >> entity

Notes:

    All role-assignment operations ('<<' and '>>') return the right operand.
    Relations are created whenever a relation template is created/updated.
    Adding a role to a relation (template) deletes the old relation.
"""

from collections import defaultdict
import graphviz

# It's OK, pylint: disable=too-few-public-methods,protected-access
# Piss off, pylint: disable=use-dict-literal

# Accepted attribute types (must be a tuple of types)
ATTR_TYPES = (str, bool, int, float)

# The name of the source role
SOURCE_ROLE_NAME = "source"

# The name of the target role
TARGET_ROLE_NAME = "target"


class Graph:
    """A graph"""

    def __init__(self):
        """Initialize the graph"""
        self._entity_types_names_attrs = \
            defaultdict(lambda: defaultdict(dict))
        self._relation_types_roles_attrs = \
            defaultdict(lambda: defaultdict(dict))
        self.entities = EntityDomainAccessor(self)
        self.relations = RelationDomainAccessor(self)

    def _render_graphviz_entities(self, graph):
        """
        Render the graph entities into a Graphviz graph.

        Args:
            graph:  The graphviz graph to render entities into.
        """
        for entity_type, names_attrs in \
                self._entity_types_names_attrs.items():
            for name, attrs in names_attrs.items():
                graph.node(
                    repr((entity_type, name)),
                    label=f"{entity_type}:\n{name}" if entity_type else name,
                    _attributes=dict(
                        [("shape", "box"),
                         ("knob_domain", "entity"),
                         ("knob_type", entity_type)] +
                        [("knob_attr_" + n, str(v))
                         for n, v in attrs.items()]
                    )
                )

    def _render_graphviz_relations(self, graph):
        """
        Render the graph relations into a Graphviz graph.

        Args:
            graph:  The graphviz graph to render relations into.
        """
        for relation_type, roles_attrs in \
                self._relation_types_roles_attrs.items():
            for roles, attrs in roles_attrs.items():
                roles_dict = dict(roles)
                # If this is a simple relation (source->target)
                if set(roles_dict) == {SOURCE_ROLE_NAME, TARGET_ROLE_NAME}:
                    # Create the relation edge
                    graph.edge(
                        repr(roles_dict[SOURCE_ROLE_NAME]),
                        repr(roles_dict[TARGET_ROLE_NAME]),
                        label=relation_type,
                        _attributes=dict(
                            [("knob_domain", "relation"),
                             ("knob_type", relation_type)] +
                            [("knob_attr_" + n, str(v))
                             for n, v in attrs.items()]
                        )
                    )
                # Else this is a complex (non-binary) relation
                else:
                    # Relation node name
                    name = repr(tuple(sorted(roles)))
                    # Create the relation node
                    graph.node(
                        name, label=relation_type,
                        _attributes=dict(
                            [("shape", "diamond"),
                             ("knob_domain", "relation"),
                             ("knob_type", relation_type)] +
                            [("knob_attr_" + n, v) for n, v in attrs.items()]
                        )
                    )
                    # Create the role edges
                    for role, entity in roles:
                        graph.edge(
                            name, repr(entity), label=role,
                            _attributes=dict(
                                style="dashed",
                                knob_domain="role",
                                knob_type=role
                            )
                        )

    def render_graphviz(self):
        """
        Render the graph into Graphviz source code.

        Returns:
            The rendered Graphviz source code string.
        """
        graph = graphviz.Digraph()
        self._render_graphviz_entities(graph)
        self._render_graphviz_relations(graph)
        return graph.source


class EntityReference:
    """An entity reference"""

    def __init__(self, graph: Graph, type_name: str, name: str):
        """Initialize an entity reference"""
        self.graph = graph
        self.type_name = type_name
        self.name = name
        # Make sure the entity exists
        # It's OK, pylint: disable=pointless-statement
        self.graph._entity_types_names_attrs[self.type_name][self.name]

    def __hash__(self):
        return hash((id(self.graph), self.type_name, self.name))

    def __eq__(self, other):
        return isinstance(other, EntityReference) and \
            self.graph is other.graph and \
            self.type_name == other.type_name and \
            self.name == other.name

    def __rshift__(self, other_or_cont):
        """
        Set yourself as the "source" role of (a container of) (implicit
        typeless) relations.
        """
        result_list = []
        other_cont = other_or_cont \
            if isinstance(other_or_cont, (set, frozenset, list, tuple)) \
            else [other_or_cont]
        for other in other_cont:
            if isinstance(other, EntityReference):
                self.graph.relations[""](**{SOURCE_ROLE_NAME: self,
                                            TARGET_ROLE_NAME: other})
            elif isinstance(other, RelationTemplate):
                other = other(**{SOURCE_ROLE_NAME: self})
            else:
                return NotImplemented
            result_list.append(other)
        return type(other_cont)(result_list) \
            if other_cont is other_or_cont \
            else result_list[0]

    def __rlshift__(self, other_or_cont):
        """
        Set yourself as the "source" role of (a container of) (implicit
        typeless) relations.
        """
        return self.__rshift__(other_or_cont)

    def __lshift__(self, other_or_cont):
        """
        Set yourself as the "target" role of (a container of) (implicit
        typeless) relations.
        """
        result_list = []
        other_cont = other_or_cont \
            if isinstance(other_or_cont, (set, frozenset, list, tuple)) \
            else [other_or_cont]
        for other in other_cont:
            if isinstance(other, EntityReference):
                self.graph.relations[""](**{TARGET_ROLE_NAME: self,
                                            SOURCE_ROLE_NAME: other})
            elif isinstance(other, RelationTemplate):
                other = other(**{TARGET_ROLE_NAME: self})
            else:
                return NotImplemented
            result_list.append(other)
        return type(other_cont)(result_list) \
            if other_cont is other_or_cont \
            else result_list[0]

    def __rrshift__(self, other_or_cont):
        """
        Set yourself as the "target" role of (a container of) (implicit
        typeless) relations.
        """
        return self.__lshift__(other_or_cont)

    def __call__(self, **attrs) -> 'EntityReference':
        """
        Add/modify entity attributes.

        Args:
            attrs:  The attributes of the entity to add/modify.

        Returns:
            The reference to the (updated) entity.
        """
        assert all(isinstance(k, str) and isinstance(v, ATTR_TYPES)
                   for k, v in attrs.items())
        self.graph._entity_types_names_attrs[self.type_name][self.name]. \
            update(attrs)
        return self


class EntityTypeAccessor:
    """An accessor for a type of entity"""

    def __init__(self, graph: Graph, type_name: str):
        """Initialize the entity type accessor"""
        self.graph = graph
        self.type_name = type_name

    def __getattr__(self, name: str) -> EntityReference:
        """Access an entity with specified name"""
        return EntityReference(self.graph, self.type_name, name)

    def __getitem__(self, name: str) -> EntityReference:
        """Access an entity with specified name"""
        return EntityReference(self.graph, self.type_name, name)


class EntityDomainAccessor:
    """An accessor for all graph entities"""

    def __init__(self, graph: Graph):
        """Initialize the entity accessor"""
        self.graph = graph

    def __getattr__(self, type_name: str) -> EntityTypeAccessor:
        """Access an entity type"""
        return EntityTypeAccessor(self.graph, type_name)

    def __getitem__(self, type_name: str) -> EntityTypeAccessor:
        """Access an entity type"""
        return EntityTypeAccessor(self.graph, type_name)


class RelationTemplate:
    """A template for a relation"""

    def __init__(self, graph: Graph, type_name: str,
                 roles: frozenset, attrs: dict):
        """
        Initialize a relation template.

        Args:
            graph:              The graph the relation belongs to.
            type_name:          The name of the type of the relation.
            roles:              A frozenset with tuples, two items each:
                                * Role name
                                * A tuple with entity's type name and name.
            attrs:              A dictionary of attribute names and values.
        """
        assert all(
            isinstance(role, str) and
            isinstance(entity, tuple) and len(entity) == 2 and
            isinstance(entity[0], str) and isinstance(entity[1], str)
            for role, entity in roles
        )
        assert all(
            isinstance(k, str) and isinstance(v, ATTR_TYPES)
            for k, v in attrs.items()
        )
        self.graph = graph
        self.type_name = type_name
        self.roles = roles
        self.attrs = attrs
        # Create/replace relation attributes
        self.graph._relation_types_roles_attrs[self.type_name][self.roles] = \
            attrs.copy()

    def __rshift__(self, other_or_cont):
        """
        Set (a container of) entities as the "target" role for the template
        relation.
        """
        other_cont = other_or_cont \
            if isinstance(other_or_cont, (set, frozenset, list, tuple)) \
            else [other_or_cont]
        for other in other_cont:
            if isinstance(other, EntityReference):
                self(**{TARGET_ROLE_NAME: other})
            else:
                return NotImplemented
        return other_or_cont

    def __rlshift__(self, other_or_cont):
        """
        Set (a container of) entities as the "target" role for the template
        relation.
        """
        result_list = []
        other_cont = other_or_cont \
            if isinstance(other_or_cont, (set, frozenset, list, tuple)) \
            else [other_or_cont]
        for other in other_cont:
            if isinstance(other, EntityReference):
                result_list.append(self(**{TARGET_ROLE_NAME: other}))
            else:
                return NotImplemented
        return type(other_cont)(result_list) \
            if other_cont is other_or_cont \
            else result_list[0]

    def __lshift__(self, other_or_cont):
        """
        Set (a container of) entities as the "source" role for the template
        relation.
        """
        other_cont = other_or_cont \
            if isinstance(other_or_cont, (set, frozenset, list, tuple)) \
            else [other_or_cont]
        for other in other_cont:
            if isinstance(other, EntityReference):
                self(**{SOURCE_ROLE_NAME: other})
            else:
                return NotImplemented
        return other_or_cont

    def __rrshift__(self, other_or_cont):
        """
        Set (a container of) entities as the "source" role for the template
        relation.
        """
        result_list = []
        other_cont = other_or_cont \
            if isinstance(other_or_cont, (set, frozenset, list, tuple)) \
            else [other_or_cont]
        for other in other_cont:
            if isinstance(other, EntityReference):
                result_list.append(self(**{SOURCE_ROLE_NAME: other}))
            else:
                return NotImplemented
        return type(other_cont)(result_list) \
            if other_cont is other_or_cont \
            else result_list[0]

    def __call__(self, **attrs_and_roles) -> 'RelationTemplate':
        """
        Create a new relation template (and a relation) from this one with
        attributes and/or relations updated.

        Args:
            attrs_and_roles:    A dictionary of attribute names and values,
                                and/or role names and entities to add/modify.

        Returns:
            The reference to the (updated) relation.
        """
        assert all(
            isinstance(k, str) and
            isinstance(v, (EntityReference,) + ATTR_TYPES)
            for k, v in attrs_and_roles.items()
        )

        # Create updated roles and attributes
        roles = dict(self.roles)
        attrs = self.attrs.copy()
        for key, value in attrs_and_roles.items():
            if isinstance(value, EntityReference):
                if key in roles:
                    raise Exception(
                        "Attempting to change a relation template role"
                    )
                roles[key] = (value.type_name, value.name)
            else:
                attrs[key] = value
        roles = frozenset(roles.items())

        # If we're adding (not keeping or changing) roles
        if roles > self.roles:
            # Remove the attributes from the old roles
            self.graph._relation_types_roles_attrs[self.type_name]. \
                pop(self.roles, {})

        # Create the new template (and relation)
        return type(self)(self.graph, self.type_name, roles, attrs)


class RelationDomainAccessor:
    """An accessor for all graph relations"""

    def __init__(self, graph: Graph):
        """Initialize the relation accessor"""
        self.graph = graph

    def __getattr__(self, type_name: str) -> RelationTemplate:
        """Create a relation template for a type"""
        return RelationTemplate(self.graph, type_name, frozenset(), {})

    def __getitem__(self, type_name: str) -> RelationTemplate:
        """Create a relation template for a type"""
        return RelationTemplate(self.graph, type_name, frozenset(), {})
