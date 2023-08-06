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

# Accepted entity/relation container types (must be a tuple of types)
CONT_TYPES = (list, tuple)

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
        self.entity_patterns = EntityTypePatternAccessor(self)
        self.relation_patterns = RelationPatternAccessor(self)

    def _render_graphviz_entities(self, graph):
        """
        Render the graph entities into a Graphviz graph.

        Args:
            graph:  The graphviz graph to render entities into.
        """
        def trim(s):
            return s[:61] + "..." if isinstance(s, str) and len(s) > 64 else s

        for entity_type, names_attrs in \
                self._entity_types_names_attrs.items():
            for name, attrs in names_attrs.items():
                graph.node(
                    repr((entity_type, name)),
                    label="\n".join(
                        [f"{entity_type}:\n{name}" if entity_type else name] +
                        [f"{n}={trim(v)!r}" for n, v in attrs.items()]
                    ),
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
                relation_attrs = dict(
                    label=relation_type,
                    knob_domain="relation",
                    knob_type=relation_type,
                    **{"knob_attr_" + n: str(v) for n, v in attrs.items()}
                )
                # If this is a simple relation (source->target)
                if set(roles_dict) == {SOURCE_ROLE_NAME, TARGET_ROLE_NAME}:
                    # Create the relation edge
                    graph.edge(
                        repr(roles_dict[SOURCE_ROLE_NAME]),
                        repr(roles_dict[TARGET_ROLE_NAME]),
                        **relation_attrs
                    )
                # Else this is a complex (non-binary) relation
                else:
                    sorted_roles = tuple(sorted(roles))
                    # Relation node name
                    name = repr(sorted_roles)
                    # Create the relation node
                    graph.node(name, **relation_attrs, shape="diamond")
                    # Create the role edges
                    for role, entity in sorted_roles:
                        edge_attrs = dict(knob_domain="role", knob_type=role)
                        if role == SOURCE_ROLE_NAME:
                            graph.edge(repr(entity), name, **edge_attrs)
                        elif role == TARGET_ROLE_NAME:
                            graph.edge(name, repr(entity), **edge_attrs)
                        else:
                            graph.edge(
                                repr(entity), name, label=role,
                                **edge_attrs, style="dashed"
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


class Object:
    """An abstract graph object (entity or relation)"""


def obj_or_cont_is_valid(obj_or_cont):
    """
    Check that an object or a (nested) container thereof is valid.

    That is if the "obj_or_cont" is either an Object, or a (nested) container
    thereof. Where "container" is one of "CONT_TYPES".

    Args:
        obj_or_cont:  The object (container) to check.

    Returns:
        True if the object (container) is valid, False otherwise.
    """
    if isinstance(obj_or_cont, Object):
        return True
    if isinstance(obj_or_cont, CONT_TYPES):
        return all(obj_or_cont_is_valid(sub_obj_or_cont)
                   for sub_obj_or_cont in obj_or_cont)
    return False


def obj_or_cont_iter(obj_or_cont):
    """
    Create a generator returning the Object instances for an Object instance
    or a (nested) container thereof, as defined by obj_or_cont_is_valid().

    Args:
        obj_or_cont:  The object (container) to iterate over.

    Returns:
        A generator returning Object instances.
    """
    assert obj_or_cont_is_valid(obj_or_cont)
    if isinstance(obj_or_cont, Object):
        yield obj_or_cont
    if isinstance(obj_or_cont, CONT_TYPES):
        for sub_obj_or_cont in obj_or_cont:
            yield from obj_or_cont_iter(sub_obj_or_cont)


class EntityReference(Object):
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

    def __rshift__(self, obj_or_cont):
        """
        Set yourself as the "source" role of (a container of) (implicit
        typeless) relations.
        """
        if not obj_or_cont_is_valid(obj_or_cont):
            return NotImplemented
        result_list = []
        for obj in obj_or_cont_iter(obj_or_cont):
            if isinstance(obj, EntityReference):
                self.graph.relations[""](**{SOURCE_ROLE_NAME: self,
                                            TARGET_ROLE_NAME: obj})
            elif isinstance(obj, RelationTemplate):
                obj = obj(**{SOURCE_ROLE_NAME: self})
            else:
                return NotImplemented
            result_list.append(obj)
        return result_list if len(result_list) > 1 else result_list[0]

    def __rlshift__(self, obj_or_cont):
        """
        Set yourself as the "source" role of (a container of) (implicit
        typeless) relations.
        """
        self.__rshift__(obj_or_cont)
        return self

    def __lshift__(self, obj_or_cont):
        """
        Set yourself as the "target" role of (a container of) (implicit
        typeless) relations.
        """
        if not obj_or_cont_is_valid(obj_or_cont):
            return NotImplemented
        result_list = []
        for obj in obj_or_cont_iter(obj_or_cont):
            if isinstance(obj, EntityReference):
                self.graph.relations[""](**{TARGET_ROLE_NAME: self,
                                            SOURCE_ROLE_NAME: obj})
            elif isinstance(obj, RelationTemplate):
                obj = obj(**{TARGET_ROLE_NAME: self})
            else:
                return NotImplemented
            result_list.append(obj)
        return result_list if len(result_list) > 1 else result_list[0]

    def __rrshift__(self, obj_or_cont):
        """
        Set yourself as the "target" role of (a container of) (implicit
        typeless) relations.
        """
        self.__lshift__(obj_or_cont)
        return self

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


class RelationTemplate(Object):
    """A template for a relation"""

    def relation_roles_iter(self, relation_roles=frozenset()):
        """
        Create a generator returning relation roles for the template roles.

        Args:
            relation_roles: The frozenset of already-collected relation roles
                            in the order of role names in self.roles.

        Returns:
            A generator returning frozensets of relation roles, each being a
            tuple containing:
            * a role name, and
            * a tuple of entity's type name and name.
        """
        assert isinstance(relation_roles, frozenset)
        assert all(isinstance(role, tuple) and len(role) == 2 and
                   isinstance(role[0], str) and
                   isinstance(role[1], tuple) and len(role[1]) == 2 and
                   isinstance(role[1][0], str) and isinstance(role[1][1], str)
                   for role in relation_roles)
        assert len(relation_roles) <= len(self.roles)
        assert set(tuple(self.roles)[0:len(relation_roles)]) == \
            {role[0] for role in relation_roles}

        if len(relation_roles) == len(self.roles):
            yield relation_roles
            return

        role_name = tuple(self.roles)[len(relation_roles)]
        for entity in self.roles[role_name]:
            yield from self.relation_roles_iter(
                relation_roles | frozenset(((role_name, entity),))
            )

    def __init__(self, graph: Graph, type_name: str,
                 roles: dict, attrs: dict):
        """
        Initialize a relation template.

        Args:
            graph:      The graph the relation belongs to.
            type_name:  The name of the type of the relation.
            roles:      A dictionary of role names and (non-empty) tuples of
                        tuples containing an entity's type name and name each.
            attrs:      A dictionary of attribute names and values.
        """
        assert all(
            isinstance(role, str) and
            isinstance(entities, tuple) and
            len(entities) > 0 and
            all(
                isinstance(entity, tuple) and len(entity) == 2 and
                isinstance(entity[0], str) and isinstance(entity[1], str)
                for entity in entities
            )
            for role, entities in roles.items()
        )
        assert all(
            isinstance(k, str) and isinstance(v, ATTR_TYPES)
            for k, v in attrs.items()
        )
        self.graph = graph
        self.type_name = type_name
        self.roles = roles
        self.attrs = attrs
        # Create/replace relations (attributes)
        for relation_roles in self.relation_roles_iter():
            self.graph._relation_types_roles_attrs \
                [self.type_name][relation_roles] = self.attrs.copy()

    def __rshift__(self, obj_or_cont):
        """
        Set (a container of) entities as the "target" role for the template
        relation.
        """
        if obj_or_cont_is_valid(obj_or_cont):
            self(**{TARGET_ROLE_NAME: obj_or_cont})
            return obj_or_cont
        return NotImplemented

    def __rlshift__(self, obj_or_cont):
        """
        Set (a container of) entities as the "target" role for the template
        relation.
        """
        if obj_or_cont_is_valid(obj_or_cont):
            return self(**{TARGET_ROLE_NAME: obj_or_cont})
        return NotImplemented

    def __lshift__(self, obj_or_cont):
        """
        Set (a container of) entities as the "source" role for the template
        relation.
        """
        if obj_or_cont_is_valid(obj_or_cont):
            self(**{SOURCE_ROLE_NAME: obj_or_cont})
            return obj_or_cont
        return NotImplemented

    def __rrshift__(self, obj_or_cont):
        """
        Set (a container of) entities as the "source" role for the template
        relation.
        """
        if obj_or_cont_is_valid(obj_or_cont):
            return self(**{SOURCE_ROLE_NAME: obj_or_cont})
        return NotImplemented

    def __call__(self, **attrs_and_roles) -> 'RelationTemplate':
        """
        Create a new relation template (and a relation) from this one with
        attributes and/or relations updated.

        Args:
            attrs_and_roles:    A dictionary of attribute names and values,
                                and/or role names and (containers of) entities
                                to add/modify.

        Returns:
            The reference to the (updated) relation.
        """
        assert all(
            isinstance(k, str) and
            (isinstance(v, ATTR_TYPES) or obj_or_cont_is_valid(v))
            for k, v in attrs_and_roles.items()
        )

        # Create updated roles and attributes
        roles = self.roles.copy()
        attrs = self.attrs.copy()
        for key, value in attrs_and_roles.items():
            if isinstance(value, ATTR_TYPES):
                attrs[key] = value
                continue
            for obj in obj_or_cont_iter(value):
                assert isinstance(obj, EntityReference), \
                       f"{obj!r} is not an entity reference"
                if key not in roles:
                    roles[key] = tuple()
                roles[key] += ((obj.type_name, obj.name),)

        # If we're adding new roles
        if set(roles) > set(self.roles):
            # Remove (the attributes from) the old roles
            for relation_roles in self.relation_roles_iter():
                self.graph._relation_types_roles_attrs[self.type_name]. \
                    pop(relation_roles, None)

        # Create the new template (and relations)
        return type(self)(self.graph, self.type_name, roles, attrs)


class RelationDomainAccessor:
    """An accessor for all graph relations"""

    def __init__(self, graph: Graph):
        """Initialize the relation accessor"""
        self.graph = graph

    def __getattr__(self, type_name: str) -> RelationTemplate:
        """Create a relation template for a type"""
        return RelationTemplate(self.graph, type_name, {}, {})

    def __getitem__(self, type_name: str) -> RelationTemplate:
        """Create a relation template for a type"""
        return RelationTemplate(self.graph, type_name, {}, {})


class ValuePattern:
    """An abstract value pattern"""

    def matches(self, value):
        """Check if the pattern matches a value"""
        raise NotImplementedError

    def matching(self, values):
        """Produce an iterator returning matching values from another one"""
        for value in values:
            if self.matches(value):
                yield value

    def is_enumerable(self):
        """Check if the pattern matches enumerable values"""
        raise NotImplementedError

    def enumerate(self):
        """Produce an iterator returning all matching values, if enumerable"""
        raise NotImplementedError


class EmptyPattern(ValuePattern):
    """A value pattern matching nothing"""
    def matches(self, value):
        return False

    def is_enumerable(self):
        return True

    def enumerate(self):
        iter(tuple())


# The pattern that matches nothing
EMPTY_PATTERN = EmptyPattern()


class UniversalPattern(ValuePattern):
    """A value pattern matching everything"""
    def matches(self, value):
        return True

    def is_enumerable(self):
        return False


# The pattern that matches everything
UNIVERSAL_PATTERN = UniversalPattern()


class StringPattern(ValuePattern):
    """A string value pattern"""

    def __init__(self, pattern: str):
        self.pattern = pattern

    def matches(self, value):
        return isinstance(value, str) and self.pattern == value

    def is_enumerable(self):
        return True

    def enumerate(self):
        yield self.pattern

class RegexPattern(ValuePattern):
    """A regular expression pattern matching string values"""

    def __init__(self, pattern: re.Pattern):
        self.pattern = pattern

    def matches(self, value):
        return isinstance(value, str) and self.pattern.fullmatch(value)

    def is_enumerable(self):
        return False


class MultiPattern(ValuePattern):
    """An abstract pattern matching multiple other patterns"""

    def __init__(self, patterns: list[ValuePattern]):
        self.patterns = patterns

    def is_enumerable(self):
        return all(pattern.is_enumerable() for pattern in self.patterns)


class OrPattern(MultiPattern):
    """A pattern matching one of a list of other patterns"""

    def matches(self, value):
        for pattern in self.patterns:
            if pattern.matches(value):
                return True
        return False

    def enumerate(self):
        for pattern in self.patterns:
            yield from pattern.enumerate()


class AndPattern(MultiPattern):
    """A pattern matching all patterns in a list"""

    def matches(self, value):
        for pattern in self.patterns:
            if not pattern.matches(value):
                return False
        return True

    def enumerate(self):
        # Python, y u no have the universal set?
        values = None
        # TODO Make order predictable (e.g. preserve it)
        for pattern in self.patterns:
            subvalues = set(pattern.enumerate())
            if values is None:
                values = subvalues
            else:
                values &= subvalues
        return iter(values or set())


class DictPattern(ValuePattern):
    """A pattern matching a dictionary"""

    def __init__(self,
                 required=None: None | dict[str, ValuePattern],
                 optional=None: None | dict[str, ValuePattern]):
        """
        Initialize the dictionary pattern.

        Args:
            required:   A dictionary of key names and value patterns matching
                        entries that must appear in the dictionary.
                        Can be None, meaning there are no required entries,
                        which is equivalent to an empty dictionary.
            optional:   A dictionary of key names and value patterns matching
                        entries that may appear in the dictionary.
                        Can be None, meaning any entries beside the required
                        ones are accepted.
        """
        if required is None:
            required = dict()
        self.required = required
        self.optional = optional

    def matches(self, dictionary):
        if not isinstance(dictionary, dict):
            return False
        remaining_dictionary = dictionary.copy()
        for key, value_pattern in self.required.items():
            if key in dictionary:
                if value_pattern.matches(dictionary[key])
                    remaining_dictionary.pop(key, None)
                    continue
            return False
        if self.optional is not None:
            for key, value in remaining_dictionary.items():
                if not self.optional.get(key, EMPTY_PATTERN).matches(value):
                    return False
        return True


class OperandPattern:
    """A graph expression operand pattern"""

    def __init__(self, graph: Graph):
        """
        Initialize the operand pattern.

        Args:
            graph: The graph the matched operands belong to.
        """
        self.graph = graph

    def is_enumerable(self):
        """Check if the pattern matches enumerable operands"""
        raise NotImplementedError

class ElementPattern(Operand):
    """An abstract element (relation or entity) pattern"""

    def __neg__(self):
        """Create a subgraph pattern matching this element pattern"""
        return GraphPattern(
            self.graph,
            elements={self: False},
            left=self,
            right=self
        )

    def __invert__(self):
        """
        Create a subgraph pattern creating any elements this (enumerable)
        pattern will match, if not found.
        """
        assert self.is_enumerable()
        return GraphPattern(
            self.graph,
            elements={self: None},
            left=self,
            right=self
        )

    def __pos__(self):
        """
        Create a subgraph pattern creating any elements this (enumerable)
        pattern will match, unconditionally.
        """
        assert self.is_enumerable()
        return GraphPattern(
            self.graph,
            elements={self: True},
            left=self,
            right=self
        )

class EntityPattern(ElementPattern):
    """A graph entity pattern"""

    def __init__(self,
                 graph: Graph,
                 type_name_pattern: ValuePattern,
                 name_pattern: ValuePattern,
                 attrs_pattern=UNIVERSAL_PATTERN: ValuePattern):
        """
        Initialize the entity pattern.

        Args:
            graph:              The graph the matched entities belong to.
            type_name_pattern:  The pattern for the entity type name.
            name_pattern:       The pattern for the entity name.
            attrs_pattern:      The pattern for the attribute dictionary.
        """
        self.graph = graph
        self.type_name_pattern = type_name_pattern
        self.name_pattern = name_pattern
        self.attrs_pattern = attrs_pattern

    def __rshift__(self, opd):
        """
        Create a graph pattern matching an (implicit) relation of this entity
        pattern (as the "source" role) with an operand pattern.
        """
        if not instance(opd, OperandPattern):
            return NotImplemented
        if isinstance(opd, EntityPattern):
            elements = {
                self: False,
                self.graph.relations[""](**{SOURCE_ROLE_NAME: self,
                                            TARGET_ROLE_NAME: opd}): False
            }
        elif isinstance(opd, RelationPattern):
            elements = {
                self: False,
                opd(**{SOURCE_ROLE_NAME: self}): False
            }
        else:
            return NotImplemented
        # TODO EXPLODE AND MERGE GRAPHS!
        return GraphPattern(
            self.graph,
            elements=elements,
            left=self,
            right=opd
        )


class RelationPattern(ElementPattern):
    """A graph relation pattern"""

    def __init__(self,
                 graph: Graph,
                 type_name_pattern: ValuePattern,
                 attrs_pattern=UNIVERSAL_PATTERN: ValuePattern,
                 role_patterns=None: None | dict[str, EntityPattern]):
        """
        Initialize the relation pattern.

        Args:
            graph:              The graph the matched relations belong to.
            type_name_pattern:  The pattern for the relation type name.
            attrs_pattern:      The pattern for the attribute dictionary.
            role_patterns:      A dictionary of role names and entity patterns
                                that must be present in the relation.
                                None, if roles should be ignored.
        """
        self.graph = graph
        self.type_name_pattern = type_name_pattern
        self.attrs_pattern = attrs_pattern
        self.role_patterns = role_patterns


class GraphPattern(Operand):
    """A (sub)graph pattern"""

    def __init__(self,
                 graph: Graph,
                 elements: dict[ElementPattern, None | bool],
                 left: ElementPattern,
                 right: ElementPattern):
        """
        Initialize the graph pattern.

        Args:
            graph:      The supergraph of the graph this pattern is matching.
                        All supplied elements must reference this graph.
            elements:   A dictionary of patterns matching elements
                        (entities or relations) belonging to the subgraph, and
                        one of the three values:
                        * False, if the element pattern should be matched.
                        * None, if any element matching the (enumerable)
                          pattern should be created, if they don't exist.
                        * True, if all elements matching the (enumerable)
                          pattern should be created unconditionally.
                        Roles in any relation patterns contained in this
                        dictionary can only reference entity patterns from the
                        same dictionary. All elements in this dictionary must
                        reference the supplied graph.
            left:       An element pattern considered to be the "leftmost" in
                        this subgraph. Must exist in the element dictionary.
            right:      An element considered to be the "rightmost" in
                        this subgraph. Must exist in the element dictionary.
        """
        assert all(e.graph is graph for e in elements)
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
            for entity in relation.role_patterns.values()
        }
        assert left in elements
        assert right in elements
        self.graph = graph
        self.elements = elements
        self.entities = entities
        self.relations = relations
        self.left = left
        self.right = right

    def __neg__(self):
        """Mark the subgraph pattern to be matched"""
        return GraphPattern(
            self.graph,
            elements={e: False for e in self.elements},
            left=self.left,
            right=self.right
        )

    def __invert__(self):
        """Mark the subgraph pattern to be created, if not matched"""
        return GraphPattern(
            self.graph,
            elements={e: None for e in self.elements},
            left=self.left,
            right=self.right
        )

    def __pos__(self):
        """Mark the subgraph pattern to be created, not matched"""
        return GraphPattern(
            self.graph,
            elements={e: True for e in self.elements},
            left=self.left,
            right=self.right
        )



class EntityPatternTypeAccessor:
    """An accessor for entity patterns with a particular type"""

    def __init__(self, graph: Graph, type_name: str):
        """Initialize the entity pattern accessor"""
        self.graph = graph
        self.type_name = type_name
        self.type_pattern = StringPattern(self.type_name)

    def __getattr__(self, name: str) -> EntityPattern:
        """Create a pattern with the accessor's type and specified name"""
        return EntityPattern(self.graph,
                             self.type_pattern,
                             StringPattern(name))

    def __getitem__(self, name: str) -> EntityPattern:
        """Create a pattern with the accessor's type and specified name"""
        return EntityPattern(self.graph,
                             self.type_pattern,
                             StringPattern(name))


class EntityPatternAccessor:
    """An accessor for entity patterns"""

    def __init__(self, graph: Graph):
        """Initialize the entity pattern accessor"""
        self.graph = graph

    def __getattr__(self, type_name: str) -> EntityPatternTypeAccessor:
        """Access entity patterns with a particular type"""
        return EntityPatternTypeAccessor(self.graph, type_name)

    def __getitem__(self, type_name: str) -> EntityPatternTypeAccessor:
        """Access entity patterns with a particular type"""
        return EntityPatternTypeAccessor(self.graph, type_name)


class RelationPatternAccessor:
    """An accessor for relation patterns"""

    def __init__(self, graph: Graph):
        """Initialize the relation pattern accessor"""
        self.graph = graph

    def __getattr__(self, type_name: str) -> RelationTemplate:
        """Create a relation pattern for a type"""
        return RelationPattern(self.graph, StringPattern(type_name))

    def __getitem__(self, type_name: str) -> RelationTemplate:
        """Create a relation pattern for a type"""
        return RelationPattern(self.graph, StringPattern(type_name))
