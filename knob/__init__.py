"""
KNOB - Knowledge builder - a module for creating knowledge (hyper)graphs.

Class inheritance diagram:

    Graph

    Accessor
        DomainAccessor
            EntityAccessor
            RelationAccessor
        TypeAccessor
            EntityTypeAccessor
            RelationTypeAccessor

    Reference
        EntityReference
        RelationReference

An overview of various types and how they're used:

    Graph:
        entities: EntityAccessor
        relations: RelationAccessor

    EntityAccessor:
        __attr__(): EntityTypeAccessor

    EntityTypeAccessor:
        __call__(): EntityReference

    RelationAccessor:
        __attr__(): RelationTypeAccessor

    RelationTypeAccessor:
        __call__(): RelationReference

Usage examples:

    g = Graph()
    e = g.entities
    r = g.relations

    R.ll_state_transition(origin=advertising


    advertising = E.ll_state(attribute=10, attribute=20)

    E.ll_state("Standby", attribute=10, attribute=20) ==
                          R.ll_state_transition(attribute=True,
                                                role=E.ll_state("Scanning"))
        > E.ll_state("Advertising")
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
        self._entity_types_names_attrs = \
            defaultdict(lambda: defaultdict(dict))
        self._relation_types_roles_attrs = \
            defaultdict(lambda: defaultdict(dict))
        self.entities = EntityAccessor(self)
        self.relations = RelationAccessor(self)

    def render_graphviz(self):
        """
        Render the graph into Graphviz source code.

        Returns:
            The rendered Graphviz source code string.
        """
        def node_name(type_name, name):
            """
            Convert an entity tuple from the _entity_types_names_attrs
            dictionary to a Graphviz node name.

            Attrs:
                type:   The entity type name.
                name:   The entity name.

            Returns:
                The node name.
            """
            return name if type_name == "" else repr((type_name, name))

        # Create an empty graph
        graph = graphviz.Digraph()

        # Add entities
        for entity_type, names_attrs in \
                self._entity_types_names_attrs.items():
            for name, attrs in names_attrs.items():
                graph.node(
                    node_name(entity_type, name), label=name,
                    _attributes=dict(
                        [("shape", "box"),
                         ("knob_domain", "entity"),
                         ("knob_type", entity_type)] +
                        [("knob_attr_" + n, v) for n, v in attrs.items()]
                    )
                )

        # Add relations
        for relation_type, roles_attrs in \
                self._relation_types_roles_attrs.items():
            for roles, attrs in roles_attrs.items():
                roles_dict = dict(roles)
                # If this is a simple relation (source->target)
                if set(roles_dict) == {SOURCE_ROLE_NAME, TARGET_ROLE_NAME}:
                    # Create the relation edge
                    graph.edge(
                        node_name(*roles_dict[SOURCE_ROLE_NAME]),
                        node_name(*roles_dict[TARGET_ROLE_NAME]),
                        label=relation_type,
                        _attributes=dict(
                            [("knob_domain", "relation"),
                             ("knob_type", relation_type)] +
                            [("knob_attr_" + n, v) for n, v in attrs.items()]
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
                            name, node_name(*entity), label=role,
                            _attributes=dict(
                                style="dashed",
                                knob_domain="role",
                                knob_type=role
                            )
                        )

        # Return the graphviz source
        return graph.source


class Accessor:
    """A abstract (graph) accessor"""

    def __init__(self, graph: Graph):
        """
        Initialize the accessor.

        Args:
            graph:  The graph which the accessor is serving.
        """
        self.graph = graph


class TypeAccessor(Accessor):
    """An abstract object (entity/relation) type accessor"""

    def __init__(self, graph: Graph, type_name: str):
        super().__init__(graph)
        self.type_name = type_name


class Reference:
    """An abstract object (entity/relation) reference"""

    def __init__(self, graph: Graph, type_name: str):
        """
        Initialize an object reference (partially).

        Args:
            graph:      The graph the object belongs to.
            type_name:  The name of the type of the object.
        """
        self.graph = graph
        self.type_name = type_name


class DomainAccessor(Accessor):
    """A abstract domain (entities/relations) accessor"""

    # The type of type accessor to use
    type_accessor: type = TypeAccessor

    def __init__(self, graph: Graph):
        """
        Initialize the domain accessor.

        Args:
            graph:  The graph which the accessor is serving.
        """
        assert isinstance(type(self).type_accessor, type) and \
            issubclass(type(self).type_accessor, TypeAccessor)
        super().__init__(graph)

    def __getattr__(self, type_name: str) -> TypeAccessor:
        """
        Access an object type.

        Args:
            type_name:  The name of the type to access.

        Returns:
            An object type accessor (TypeAccessor).
        """
        return type(self).type_accessor(self.graph, type_name)

    def __getitem__(self, type_name: str) -> TypeAccessor:
        """
        Access an object type.

        Args:
            type_name:  The name of the type to access.

        Returns:
            An object type accessor (TypeAccessor).
        """
        return type(self).type_accessor(self.graph, type_name)


class EntityReference(Reference):
    """An entity reference"""

    def __init__(self, graph, type_name, name):
        """
        Initialize an entity reference.

        Args:
            graph:      The graph the object belongs to.
            type_name:  The name of the type of the object.
            name:       The name of the object.
        """
        assert isinstance(graph, Graph)
        assert isinstance(type_name, str)
        assert isinstance(name, str)
        super().__init__(graph, type_name)
        self.name = name

    def __hash__(self):
        return hash((id(self.graph), self.type_name, self.name))

    def __eq__(self, other):
        return isinstance(other, EntityReference) and \
            self.graph is other.graph and \
            self.type_name == other.type_name and \
            self.name == other.name

    def __rshift__(self, other):
        """
        Set yourself as the "source" role of an (implicit typeless) relation
        """
        if isinstance(other, EntityReference):
            other = self.graph.relations() >> other
        if not isinstance(other, RelationReference):
            return NotImplemented
        return other << self

    def __lshift__(self, other):
        """
        Set yourself as the "target" role of an (implicit typeless) relation
        """
        if isinstance(other, EntityReference):
            other = self.graph.relations() << other
        if not isinstance(other, RelationReference):
            return NotImplemented
        return other >> self

    def update_attrs(self, **attrs):
        """
        Update/add entity's attributes.

        Args:
            attrs:  The attributes to update/add.

        Returns:
            Self.
        """
        assert isinstance(attrs, dict)
        assert all(isinstance(k, str) and isinstance(v, ATTR_TYPES)
                   for k, v in attrs.items())
        self.graph._entity_types_names_attrs[self.type_name][self.name]. \
            update(attrs)
        return self


class RelationReference(Reference):
    """A relation reference"""

    def __init__(self, graph: Graph, type_name: str, **roles):
        """
        Initialize a relation reference.

        Args:
            graph:      The graph the object belongs to.
            type_name:  The name of the type of the object.
            roles:      A dictionary of role names and references to entities
                        fulfilling those roles.
        """
        assert isinstance(roles, dict)
        assert all(isinstance(k, str) and isinstance(v, EntityReference)
                   for k, v in roles.items())
        super().__init__(graph, type_name)
        self.roles = frozenset(
            (name, (entity.type_name, entity.name))
            for name, entity in roles.items()
        )

    def __hash__(self):
        return hash((id(self.graph), self.type_name, self.roles))

    def __eq__(self, other):
        return isinstance(other, RelationReference) and \
            self.graph is other.graph and \
            self.type_name == other.type_name and \
            self.roles == other.roles

    def __rshift__(self, other):
        """Set an entity as the "target" role"""
        if not isinstance(other, EntityReference):
            return NotImplemented
        return self.update_roles(**{TARGET_ROLE_NAME: other})

    def __lshift__(self, other):
        """Set an entity as the "source" role"""
        if not isinstance(other, EntityReference):
            return NotImplemented
        return self.update_roles(**{SOURCE_ROLE_NAME: other})

    def update_roles(self, **roles):
        """
        Update/add relation's roles.

        Args:
            roles:      A dictionary of role names and references to entities
                        fulfilling those roles to update/add.

        Returns:
            Self.
        """
        assert isinstance(roles, dict)
        assert all(isinstance(k, str) and isinstance(v, EntityReference)
                   for k, v in roles.items())
        new_roles = dict(self.roles)
        new_roles.update({
            name: (entity.type_name, entity.name)
            for name, entity in roles.items()
        })
        new_roles = frozenset(new_roles.items())
        self.graph._relation_types_roles_attrs[self.type_name][new_roles] = \
            self.graph._relation_types_roles_attrs[self.type_name]. \
            pop(self.roles)
        self.roles = new_roles
        return self

    def update_attrs(self, **attrs):
        """
        Update/add relation's attributes.

        Args:
            attrs:  The attributes to update/add.

        Returns:
            Self.
        """
        assert isinstance(attrs, dict)
        assert all(isinstance(k, str) and isinstance(v, ATTR_TYPES)
                   for k, v in attrs.items())
        self.graph._relation_types_roles_attrs[self.type_name][self.roles]. \
            update(attrs)
        return self


class EntityTypeAccessor(TypeAccessor):
    """An accessor for a type of entity"""
    def __call__(self, name: str, **attrs) -> EntityReference:
        """
        Access an entity of the type, with the specified name, and possibly
        change its attributes.

        Args:
            name:   The name of the entity.
            attrs:  The attributes of the entity to add/modify.

        Returns:
            The reference to the (updated) entity.
        """
        assert isinstance(name, str)
        assert all(isinstance(k, str) for k in attrs)
        ref = EntityReference(self.graph, self.type_name, name)
        ref.update_attrs(**attrs)
        return ref


class EntityAccessor(DomainAccessor):
    """An accessor for all graph entities"""
    type_accessor = EntityTypeAccessor

    def __call__(self, name: str, **attrs) -> EntityReference:
        """
        Access a typeless entity, with the specified name, and possibly change
        its attributes.

        Args:
            name:   The name of the entity.
            attrs:  The attributes of the object to add/modify.

        Returns:
            The reference to the (updated) object.
        """
        assert all(isinstance(k, str) for k in attrs)
        return self[""](name, **attrs)

class RelationTypeAccessor(TypeAccessor):
    """An accessor for a type of relation"""
    def __call__(self, **attrs_and_roles) -> RelationReference:
        """
        Access a relation of the type, with the roles, and possibly change its
        attributes.

        Args:
            attrs_and_roles:    A dictionary of attributes of the relation to
                                add/modify, as well as roles to identify the
                                relation by.

        Returns:
            The reference to the (updated) relation.
        """
        assert all(
            isinstance(k, str) and
            isinstance(v, (EntityReference,) + ATTR_TYPES)
            for k, v in attrs_and_roles.items()
        )
        roles = {}
        attrs = {}
        for key, value in attrs_and_roles.items():
            (roles if isinstance(value, EntityReference)
             else attrs)[key] = value
        ref = RelationReference(self.graph, self.type_name, **roles)
        ref.update_attrs(**attrs)
        return ref


class RelationAccessor(DomainAccessor):
    """An accessor for all graph relations"""
    type_accessor = RelationTypeAccessor

    def __call__(self, **attrs_and_roles) -> RelationReference:
        """
        Access a typeless relation, and possibly change
        its attributes and/or roles.

        Args:
            attrs_and_roles:    A dictionary of attributes of the relation to
                                add/modify, as well as roles to identify the
                                relation by.

        Returns:
            The reference to the (updated) object.
        """
        assert all(isinstance(k, str) for k in attrs_and_roles)
        return self[""](**attrs_and_roles)
