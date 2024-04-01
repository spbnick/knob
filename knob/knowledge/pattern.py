"""
KNOB - The knowledge graph pattern
"""

from typing import Optional, Self, cast
from knob.misc import AttrTypes, attrs_repr
from knob import directed

# Calm down, pylint: disable=too-few-public-methods
# NO, pylint: disable=use-dict-literal,no-else-return
# We like our "id", pylint: disable=redefined-builtin


class Element:
    """An abstract element (node or edge) pattern"""

    # The tuple of the names of implicit attributes in order of nesting
    IMPLICIT_ATTRS: tuple[str, ...] = ("_type",)

    @classmethod
    def are_attrs_valid(cls, attrs: dict[str, AttrTypes]):
        """Check if attributes dictionary is valid for an element"""
        assert isinstance(attrs, dict)
        return True

    def __init__(self, attrs: dict[str, AttrTypes]):
        """
        Initialize the element pattern.

        Args:
            attrs:  The attribute dictionary.
        """
        # Substitute implicit attrs
        if "" in attrs:
            for implicit_attr in self.IMPLICIT_ATTRS:
                if implicit_attr not in attrs:
                    attrs[implicit_attr] = attrs.pop("")
                    break
            else:
                raise NotImplementedError("Implicit attributes exhausted")

        if not self.are_attrs_valid(attrs):
            raise ValueError

        self.attrs = attrs

    def with_updated_attrs(self, attrs: dict[str, AttrTypes]) -> Self:
        """
        Duplicate the pattern with updated attributes.

        Args:
            attrs:  The attribute dictionary to update with.

        Returns:
            The updated pattern.
        """
        return type(self)(self.attrs | attrs)

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
            result += attrs_repr(explicit_attrs)
        return result

    def __repr__(self):
        return self.__class__.__name__ + self.attrs_repr()


class Node(Element):
    """A node pattern"""

    def __or__(self, other) -> Self:
        """Merge two instances of the pattern together"""
        if other is self:
            return self
        if not isinstance(other, type(self)):
            return NotImplemented
        return type(self)(self.attrs | other.attrs)


class Entity(Node):
    """An entity pattern"""

    # The tuple of the names of implicit attributes in order of nesting
    IMPLICIT_ATTRS: tuple[str, ...] = Node.IMPLICIT_ATTRS + ("_name",)


class Relation(Node):
    """A relation pattern"""


class Edge(Element):
    """An edge pattern"""

    def __init__(self, attrs: dict[str, AttrTypes],
                 source: int = 0, target: int = 0):
        """
        Initialize the edge pattern.

        Args:
            attrs:  The attribute dictionary.
            source: The ID of the source node, or zero if none.
            target: The ID of the target node, or zero if none.
        """
        super().__init__(attrs)
        self.source = source
        self.target = target

    def __repr__(self):
        return super().__repr__() + (
            "[" +
            (f"#{self.source}" if self.source else "") +
            "->" +
            (f"#{self.target}" if self.target else "") +
            "]"
        )

    def with_updated_endpoints(
        self, source: int = 0, target: int = 0
    ) -> Self:
        """
        Duplicate the pattern with endpoints updated

        Args:
            source: The ID of the source node, or zero to keep original.
            target: The ID of the target node, or zero to keep original.

        Returns:
            The updated pattern.
        """
        return type(self)(
            self.attrs,
            source or self.source,
            target or self.target
        )

    def __or__(self, other) -> Self:
        """Merge two instances of the pattern together"""
        if other is self:
            return self
        if not isinstance(other, type(self)):
            return NotImplemented
        return type(self)(
            self.attrs | other.attrs,
            other.source or self.source,
            other.target or self.target
        )


class Function(Edge):
    """A function edge pattern"""

    @classmethod
    def are_attrs_valid(cls, attrs: dict[str, AttrTypes]):
        """Check if attributes dictionary is valid for a function"""
        assert isinstance(attrs, dict)
        return not attrs or (
            set(attrs) == {"_type"} and
            isinstance(attrs["_type"], str)
        )

    def __init__(self, attrs: dict[str, AttrTypes],
                 source: int = 0, target: int = 0):
        """
        Initialize the function edge pattern.

        Args:
            attrs:  The attribute dictionary.
                    Can only be empty or contain the "_type" string attribute.
            source: The ID of the source relation, or zero if none.
            target: The ID of the target node, or zero if none.
        """
        assert isinstance(attrs, dict)
        super().__init__(attrs, source, target)

    def __repr__(self):
        return self.__class__.__name__ + "." + (
            repr(self.attrs.get("_type")) +
            "[" +
            (f"#{self.source}" if self.source else "") +
            "->" +
            (f"#{self.target}" if self.target else "") +
            "]"
        )

    def is_complete(self):
        """
        Check if the function is complete, that is if it has source, target,
        and _type attribute.

        Returns:
            True if the function is complete, False otherwise.
        """
        return self.source and self.target and "_type" in self.attrs


# Element pattern types operated by the graph pattern
GRAPH_ELEMENTS = (Entity, Relation, Function)
GraphElements = Entity | Relation | Function


class Graph:
    """A graph pattern"""

    # Next available static ID
    __NEXT_STATIC_ID = 2

    @classmethod
    def is_valid_id(cls, id):
        """Check if an element ID is valid (a non-zero integer)"""
        return isinstance(id, int) and bool(id)

    @classmethod
    def is_dynamic_id(cls, id):
        """Check if an element ID is dynamic (odd)"""
        assert cls.is_valid_id(id)
        return bool(id & 1)

    @classmethod
    def is_static_id(cls, id):
        """Check if an element ID is static (even)"""
        assert cls.is_valid_id(id)
        return not id & 1

    def __init__(self,
                 elements: dict[int, GraphElements],
                 marked: dict[int, bool],
                 left: int, right: int):
        """
        Initialize the graph pattern.

        Args:
            elements:   A dictionary of element IDs and corresponding element
                        (entity/relation/function) patterns. The pattern IDs
                        must match corresponding dictionary keys.
            marked:     A dictionary of elements and their marked status:
                        either False, or True. Elements without their ID in
                        this dictionary are considered unmarked when the
                        pattern is applied, and unset, when the pattern is
                        merged with another. All keys in this dictionary must
                        exist in "elements".
            left:       The ID of the left-side element pattern. To use when
                        using the graph pattern on the right side of an
                        operator. The ID must be in "elements".
                        Cannot reference a complete function.
            right:      The ID of the right-side element pattern. To use when
                        using the graph pattern on the left side of an
                        operator. The ID must be in "elements".
                        Cannot reference a complete function.
        """
        assert isinstance(elements, dict)
        assert self.is_valid_id(left)
        assert self.is_valid_id(right)
        assert all(
            self.is_valid_id(id) and isinstance(e, GRAPH_ELEMENTS)
            for id, e in elements.items()
        )
        assert isinstance(marked, dict)
        assert set(marked) <= set(elements)
        assert all(isinstance(m, bool) for m in marked.values())
        assert all(
            (not e.source or isinstance(elements.get(e.source), Relation)) and
            (not e.target or isinstance(elements.get(e.target), Node))
            for e in elements.values() if isinstance(e, Function)
        ), "A function references an unknown node"

        self.elements = elements
        self.marked = marked
        self.left = left
        self.right = right

    def __repr__(self):
        # It's OK, pylint: disable=too-many-branches

        # A list of entity IDs
        entity_ids = []

        # A list of relation IDs
        relation_ids = []

        # A list of incomplete function IDs
        function_ids = []

        # A dictionary of element IDs and repr (signature, body) tuples
        element_reprs = {}

        # Generate graph pattern-unique element signatures
        for id, element in self.elements.items():
            if isinstance(element, Entity):
                entity_ids.append(id)
                element_reprs[id] = (f"e{len(entity_ids)}",)
            elif isinstance(element, Relation):
                relation_ids.append(id)
                element_reprs[id] = (f"r{len(relation_ids)}",)
            elif isinstance(element, Function):
                if element.is_complete():
                    continue
                function_ids.append(id)
                element_reprs[id] = (f"f{len(function_ids)}",)

        # A dictionary of IDs of relations and lists of tuples of their
        # mark characters, function types, and corresponding actor node IDs.
        relation_functions = {id: [] for id in relation_ids}

        # Collect both complete and incomplete functions (edges)
        for id, element in self.elements.items():
            if not isinstance(element, Function):
                continue
            if element.is_complete():
                relation_functions[element.source].append((
                    ("", "+")[self.marked.get(id, False)],
                    element.attrs["_type"],
                    element.target
                ))
            else:
                element_reprs[id] += (
                    element.attrs_repr() +
                    (
                        "[" +
                        element_reprs.get(element.source, ("", ))[0] +
                        "->" +
                        element_reprs.get(element.target, ("", ))[0] +
                        "]"
                        if element.source or element.target else ""
                    ),
                )

        # Generate entity and relation bodies
        for id, element in self.elements.items():
            if not isinstance(element, (Entity, Relation)):
                continue
            body = element.attrs_repr()
            if isinstance(element, Relation):
                functions = sorted(relation_functions[id])
                if any(not (n or "").isidentifier() for _, n, _ in functions):
                    body += ":{" + ", ".join(
                        f"{m}{n!r}: {element_reprs[a_id][0]}"
                        for m, n, a_id in functions
                    ) + "}"
                elif functions:
                    body += ":(" + ", ".join(
                        f"{m}{n}={element_reprs[a_id][0]}"
                        for m, n, a_id in functions
                    ) + ")"
            element_reprs[id] += (body,)

        # Put everything together
        return f"{element_reprs[self.left][0]} < " + ", ".join(
            ("", "+")[self.marked.get(id, False)] + "".join(element_reprs[id])
            for id in (entity_ids + relation_ids + function_ids)
        ) + f" > {element_reprs[self.right][0]}"

    def to_dg(self) -> directed.Graph:
        """Convert the knowledge graph pattern to a directed graph"""
        ids_elements: dict[int, directed.Elements] = {
            id: directed.Node(**element.attrs)
            for id, element in self.elements.items()
            if isinstance(element, Node)
        }
        ids_elements |= {
            id: directed.Edge(
                cast(directed.Node, ids_elements[element.source]),
                cast(directed.Node, ids_elements[element.target]),
                **element.attrs
            )
            for id, element in self.elements.items()
            if isinstance(element, Function) and element.is_complete()
        }
        return directed.Graph(
            elements=set(ids_elements.values()),
            marked={ids_elements[id] for id in self.marked}
        )

    def with_replaced_element(
        self, id: int, new: GraphElements
    ) -> 'Graph':
        """Create a duplicate graph pattern with an element replaced"""
        old = self.elements.get(id)
        assert old is not None, "Replacing unknown element pattern"
        assert type(old) is type(new), "Cannot change element type"
        elements = self.elements.copy()
        elements[id] = new
        gp = Graph(elements, self.marked, self.left, self.right)
        return gp

    def overlay(self, other, *graph_ids: tuple['Graph', int]):
        """
        Overlay a graph on top of this one.

        Args:
            other:      The graph to overlay on top of this one.
            graph_ids:  A tuple of 2-tuples, each containing one of the
                        participating graphs, and the ID of one of its
                        elements to have mapped to its new ID

        Returns:
            The overlaid "elements" dictionary, and the overlaid "marked"
            dictionary, followed by the mapped IDs corresponding to each tuple
            in graph_ids, in order.
        """
        assert isinstance(other, Graph)
        assert isinstance(graph_ids, tuple)
        assert all(
            isinstance(graph_id, tuple) and
            len(graph_id) == 2 and
            graph_id[0] in (self, other) and
            graph_id[1] in graph_id[0].elements
            for graph_id in graph_ids
        )

        next_dynamic_id = 1
        elements: dict[int, GraphElements] = {}
        marked: dict[int, bool] = {}
        graph_id_map: dict['Graph', dict[int, int]] = {}
        graph_id_map[self] = {0: 0}
        graph_id_map[other] = {0: 0}

        def overlay(graph: 'Graph'):
            nonlocal next_dynamic_id
            id_map = graph_id_map[graph]

            # Build ID map
            for id, element in graph.elements.items():
                if graph.is_static_id(id):
                    new_id = id
                else:
                    new_id = next_dynamic_id
                    next_dynamic_id += 2
                id_map[id] = new_id

            # Overlay elements
            for id, element in graph.elements.items():
                new_id = id_map[id]
                if isinstance(element, Edge):
                    element = element.with_updated_endpoints(
                        id_map[element.source], id_map[element.target]
                    )
                elements[new_id] = elements.get(new_id, element) | element
                if (marked_flag := graph.marked.get(id)) is not None:
                    marked[new_id] = marked_flag

        overlay(self)
        overlay(other)

        return elements, marked, *(
            graph_id_map[graph][id]
            for graph, id in graph_ids
        )

    def __or__(self, other) -> 'Graph':
        """Merge another graph pattern to the right of this one"""
        if not isinstance(other, Graph):
            return NotImplemented
        return Graph(*self.overlay(
            other, (self, self.left), (other, other.right)
        ))

    def __pos__(self):
        """Mark all elements in the graph pattern"""
        return Graph(
            self.elements,
            {id: True for id in self.elements},
            self.left,
            self.right
        )

    def __neg__(self):
        """Unmark all elements in the graph pattern"""
        return Graph(
            self.elements,
            {id: False for id in self.elements},
            self.left,
            self.right
        )

    def __invert__(self):
        """Swap static IDs and dynamic IDs of all elements"""
        id_map = {0: 0}
        next_dynamic_id = 1

        # Build ID map
        for id, element in self.elements.items():
            if self.is_static_id(id):
                id_map[id] = next_dynamic_id
                next_dynamic_id += 2
            else:
                id_map[id] = Graph.__NEXT_STATIC_ID
                Graph.__NEXT_STATIC_ID += 2

        return Graph(
            {
                id_map[id]:
                element.with_updated_endpoints(
                    id_map[element.source],
                    id_map[element.target]
                ) if isinstance(element, Edge) else element
                for id, element in self.elements.items()
            },
            {id_map[id]: mark for id, mark in self.marked.items()},
            id_map[self.left],
            id_map[self.right]
        )

    def __getattr__(self, key: str) -> 'Graph':
        """Update the implicit attribute of the right element"""
        return self[key]

    def __getitem__(self, key) -> 'Graph':
        """Update the implicit attribute of the right element"""
        element = self.elements[self.right]
        if isinstance(element, Element):
            return self.with_replaced_element(
                self.right,
                element.with_updated_attrs({"": key})
            )
        raise ValueError

    def __call__(self, **attrs) -> 'Graph':
        """Update attributes of the right element"""
        element = self.elements[self.right]
        if isinstance(element, Element):
            return self.with_replaced_element(
                self.right,
                element.with_updated_attrs(attrs)
            )
        raise ValueError

    @staticmethod
    def _fill(left, right) -> 'Graph':
        """Fill an (assigned) boundary function with a node"""
        # This will do, pylint: disable=too-many-branches
        assert isinstance(left, Graph) or \
            isinstance(right, Graph)

        if isinstance(left, str):
            left = FunctionGraph(left)
        elif not isinstance(left, Graph):
            return NotImplemented

        if isinstance(right, str):
            right = FunctionGraph(right)
        elif not isinstance(right, Graph):
            return NotImplemented

        left_element = left.elements[left.right]
        right_element = right.elements[right.left]

        # If the node is on the left
        if isinstance(left_element, Node):
            node_graph = left
            node_id = left.right
            if isinstance(right_element, Function):
                function_graph = right
                function_id = right.left
                function = right_element
            else:
                raise ValueError
        # Else, if the node is on the right
        elif isinstance(right_element, Node):
            node_graph = right
            node_id = right.left
            if isinstance(left_element, Function):
                function_graph = left
                function_id = left.right
                function = left_element
            else:
                raise ValueError
        else:
            raise ValueError

        # If the function is already filled
        if function.target:
            raise ValueError

        elements, marked, left_id, right_id, \
            function_id, node_id = left.overlay(
                right,
                (left, left.left), (right, right.right),
                (function_graph, function_id), (node_graph, node_id)
            )
        elements[function_id] = \
            elements[function_id].with_updated_endpoints(target=node_id)
        if marked.get(node_id):
            marked[function_id] = True
        return Graph(elements, marked, left_id, right_id)

    @staticmethod
    def _assign(left, right) -> 'Graph':
        """Assign a (filled) function to a boundary relation"""
        # This will do, pylint: disable=too-many-branches
        assert isinstance(left, Graph) or \
            isinstance(right, Graph)

        if isinstance(left, str):
            left = FunctionGraph(left)
        elif not isinstance(left, Graph):
            return NotImplemented

        if isinstance(right, str):
            right = FunctionGraph(right)
        elif not isinstance(right, Graph):
            return NotImplemented

        left_element = left.elements[left.right]
        right_element = right.elements[right.left]

        # If the relation is on the left
        if isinstance(left_element, Relation):
            relation_graph = left
            relation_id = left.right
            if isinstance(right_element, Function):
                function_graph = right
                function_id = right.left
                function = right_element
            else:
                raise ValueError
        # Else, if the relation is on the right
        elif isinstance(right_element, Relation):
            relation_graph = right
            relation_id = right.left
            if isinstance(left_element, Function):
                function_graph = left
                function_id = left.right
                function = left_element
            else:
                raise ValueError
        else:
            raise ValueError

        # If the function is already assigned
        if function.source:
            raise ValueError

        elements, marked, left_id, right_id, \
            function_id, relation_id = left.overlay(
                right,
                (left, left.left), (right, right.right),
                (function_graph, function_id), (relation_graph, relation_id)
            )
        elements[function_id] = \
            elements[function_id].with_updated_endpoints(source=relation_id)
        if marked.get(relation_id):
            marked[function_id] = True
        return Graph(elements, marked, left_id, right_id)

    @staticmethod
    def _shift(left, op: str, right) -> 'Graph':
        """Create a relation or a function for a shift operator"""
        # No it's not, pylint: disable=too-many-return-statements
        # It's OK, pylint: disable=too-many-branches
        assert op in {"<<", ">>"}

        if isinstance(left, str):
            left = FunctionGraph(left)
        elif not isinstance(left, Graph):
            return NotImplemented

        if isinstance(right, str):
            right = FunctionGraph(right)
        elif not isinstance(right, Graph):
            return NotImplemented

        marked = left.marked.get(left.right) or right.marked.get(right.left)
        ltr = op == ">>"
        left_element = left.elements[left.right]
        left_type = next(t for t in (Entity, Relation, Function)
                         if isinstance(left_element, t))
        right_element = right.elements[right.left]
        right_type = next(t for t in (Entity, Relation, Function)
                          if isinstance(right_element, t))
        if ltr:
            source_type = left_type
            target_type = right_type
        else:
            source_type = right_type
            target_type = left_type

        if left_type in (Entity, Relation) and right_type == left_type:
            relation = RelationGraph()
            if marked:
                relation = +relation
            if ltr:
                return left << "source" << relation >> "target" >> right
            else:
                return left << "target" << relation >> "source" >> right
        elif left_type == Relation and right_type == Entity:
            function = FunctionGraph("target" if ltr else "source")
            if marked:
                function = +function
            return left >> function >> right
        elif left_type == Entity and right_type == Relation:
            function = FunctionGraph("source" if ltr else "target")
            if marked:
                function = +function
            return left << function << right
        elif source_type == Relation and target_type == Function:
            return Graph._assign(left, right)
        elif source_type == Function and target_type in (Relation, Entity):
            return Graph._fill(left, right)

        raise ValueError

    def __rshift__(self, other) -> 'Graph':
        """Create a relation/function, for S >> O expression"""
        return self._shift(self, ">>", other)

    def __rrshift__(self, other) -> 'Graph':
        """Create a relation/function, for O >> S expression"""
        return self._shift(other, ">>", self)

    def __lshift__(self, other) -> 'Graph':
        """Create a relation/function, for S << O expression"""
        return self._shift(self, "<<", other)

    def __rlshift__(self, other) -> 'Graph':
        """Create a relation/function, for O << S expression"""
        return self._shift(other, "<<", self)


class MetaElementGraph(type):
    """A single-element graph pattern metaclass"""

    def __getattr__(cls, key: str) -> Graph:
        return cls()[key]

    def __getitem__(cls, key) -> Graph:
        return cls()[key]


class ElementGraph(Graph, metaclass=MetaElementGraph):
    """A single-element graph pattern"""


class EntityGraph(ElementGraph):
    """A single-entity graph pattern"""

    def __init__(self, **attrs: AttrTypes):
        """
        Initialize the single-node graph pattern.

        Args:
            attrs:  The attribute dictionary.
        """
        super().__init__({1: Entity(attrs)}, {}, 1, 1)


class RelationGraph(ElementGraph):
    """A single-relation graph pattern"""

    def __init__(self, **attrs: AttrTypes):
        """
        Initialize the single-relation graph pattern.

        Args:
            attrs:  The relation's attribute dictionary.
        """
        super().__init__({1: Relation(attrs)}, {}, 1, 1)


class FunctionGraph(ElementGraph):
    """A single-function graph pattern"""

    def __init__(self, type: Optional[str] = None):
        """
        Initialize the single-function graph pattern.

        Args:
            type:   The function's type name, or None for none.
        """
        fp = Function({} if type is None else dict(_type=type))
        super().__init__({1: fp}, {}, 1, 1)
