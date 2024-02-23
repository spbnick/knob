"""
KNOB - Knowledge graph patterns
"""

from typing import Optional, Tuple, Self
from knob6.misc import AttrTypes, attrs_repr

# Calm down, pylint: disable=too-few-public-methods
# NO, pylint: disable=use-dict-literal,no-else-return
# We like our "id", pylint: disable=redefined-builtin


class Element:
    """An abstract element (node or edge) pattern"""

    # The tuple of the names of implicit attributes in order of nesting
    IMPLICIT_ATTRS: Tuple[str, ...] = ("_type",)

    # The ID next created element pattern can use
    __NEXT_ID = 1

    @classmethod
    def is_valid_id(cls, id: int):
        """Check if an ID is valid for instances of this class"""
        return id > 0

    def __init__(self, id: int, attrs: dict[str, AttrTypes]):
        """
        Initialize the element pattern.

        Args:
            id:     The element ID.
                    Must be positive.
                    Zero to assign next available.
            attrs:  The attribute dictionary.
        """
        assert self.is_valid_id(id)
        if id == 0:
            id = Element.__NEXT_ID
        else:
            assert Element.is_valid_id(id)
            Element.__NEXT_ID = max(id, Element.__NEXT_ID)
        self.id = id
        Element.__NEXT_ID += 1

        # Substitute implicit attrs
        if "" in attrs:
            for implicit_attr in self.IMPLICIT_ATTRS:
                if implicit_attr not in attrs:
                    attrs[implicit_attr] = attrs.pop("")
                    break
            else:
                raise NotImplementedError("Implicit attributes exhausted")

        self.attrs = attrs

    def with_updated_attrs(self, attrs: dict[str, AttrTypes]) -> \
            Tuple[Self, Self]:
        """
        Duplicate the pattern with updated attributes.

        Args:
            attrs:  The attribute dictionary to update with.

        Returns:
            The self and the updated pattern.
        """
        return self, type(self)(self.id, self.attrs | attrs)

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

    @classmethod
    def ref_repr(cls, id: int):
        """Format a reference representation of a pattern ID"""
        assert cls.is_valid_id(id)
        return f"{cls.__name__}#{id}"

    def __repr__(self):
        return self.ref_repr(self.id) + self.attrs_repr()


class Node(Element):
    """A node pattern"""

    # The ID next created node pattern can use
    # Cannot ever match edge pattern IDs
    __NEXT_ID = 1

    @classmethod
    def is_valid_id(cls, id: int):
        """Check if an ID is valid for instances of this class"""
        return super().is_valid_id(id) and (id & 1) == 1

    def __init__(self, id: int, attrs: dict[str, AttrTypes]):
        """
        Initialize the node pattern.

        Args:
            id:     The node ID.
                    Must be odd and positive.
                    Zero to assign next available.
            attrs:  The attribute dictionary.
        """
        if id == 0:
            id = Node.__NEXT_ID
        else:
            assert Node.is_valid_id(id)
            Node.__NEXT_ID = max(id, Node.__NEXT_ID)
        Node.__NEXT_ID += 2
        super().__init__(id, attrs)

    def __or__(self, other) -> Self:
        """Merge two instances of the pattern together"""
        if other is self:
            return self
        if not isinstance(other, type(self)):
            return NotImplemented
        if other.id != self.id:
            raise ValueError
        return type(self)(self.id, self.attrs | other.attrs)


class Entity(Node):
    """An entity pattern"""

    # The tuple of the names of implicit attributes in order of nesting
    IMPLICIT_ATTRS: Tuple[str, ...] = Node.IMPLICIT_ATTRS + ("_name",)

    # The ID next created entity pattern can use
    __NEXT_ID = 1

    @classmethod
    def is_valid_id(cls, id: int):
        """Check if an ID is valid for instances of this class"""
        return super().is_valid_id(id) and (id & 3) == 1

    def __init__(self, id: int, attrs: dict[str, AttrTypes]):
        """
        Initialize the entity pattern.

        Args:
            id:     The entity ID.
                    Must be positive and conform to id % 4 == 1.
                    Zero to assign next available.
            attrs:  The attribute dictionary.
        """
        if id == 0:
            id = Entity.__NEXT_ID
        else:
            assert Entity.is_valid_id(id)
            Entity.__NEXT_ID = max(id, Entity.__NEXT_ID)
        Entity.__NEXT_ID += 4
        super().__init__(id, attrs)

    @classmethod
    def ref_repr(cls, id: int):
        """Format a reference representation of a pattern ID"""
        assert cls.is_valid_id(id)
        return f"e#{id}"


class Relation(Node):
    """A relation pattern"""

    # The ID next created relation pattern can use
    __NEXT_ID = 3

    @classmethod
    def is_valid_id(cls, id: int):
        """Check if an ID is valid for instances of this class"""
        return super().is_valid_id(id) and (id & 3) == 3

    def __init__(self, id: int, attrs: dict[str, AttrTypes]):
        """
        Initialize the relation pattern.

        Args:
            id:     Relation ID.
                    Must be positive and conform to id % 4 == 3.
                    Zero to assign next available.
            attrs:  The attribute dictionary.
        """
        if id == 0:
            id = Relation.__NEXT_ID
        else:
            assert Relation.is_valid_id(id)
            Relation.__NEXT_ID = max(id, Relation.__NEXT_ID)
        Relation.__NEXT_ID += 4
        super().__init__(id, attrs)

    @classmethod
    def ref_repr(cls, id: int):
        """Format a reference representation of a pattern ID"""
        assert cls.is_valid_id(id)
        return f"r#{id}"


class Edge(Element):
    """An edge pattern"""

    # The ID next created edge pattern can use
    # Cannot ever match node pattern IDs
    __NEXT_ID = 2

    @classmethod
    def is_valid_id(cls, id: int):
        """Check if an ID is valid for instances of this class"""
        return super().is_valid_id(id) and (id & 1) == 0

    def __init__(self, id: int, attrs: dict[str, AttrTypes],
                 source: int = 0, target: int = 0):
        """
        Initialize the edge pattern.

        Args:
            id:     The edge ID.
                    Must be even and positive.
                    Zero to assign next available.
            attrs:  The attribute dictionary.
            source: The ID of the source node, or zero if none.
            target: The ID of the target node, or zero if none.
        """
        assert source == 0 or Node.is_valid_id(source)
        assert target == 0 or Node.is_valid_id(target)
        if id == 0:
            id = Edge.__NEXT_ID
        else:
            assert Edge.is_valid_id(id)
            Edge.__NEXT_ID = max(id, Edge.__NEXT_ID)
        Edge.__NEXT_ID += 2
        super().__init__(id, attrs)
        self.source = source
        self.target = target

    def __repr__(self):
        return super().__repr__() + (
            "[" +
            (Node.ref_repr(self.source) if self.source else "-") +
            (Node.ref_repr(self.target) if self.target else "-") +
            "]"
        )

    def with_updated_endpoints(
        self, source: int = 0, target: int = 0
    ) -> Tuple[Self, Self]:
        """
        Duplicate the pattern with endpoints updated

        Args:
            source: The ID of the source node, or zero to keep original.
            target: The ID of the target node, or zero to keep original.

        Returns:
            Self and the updated pattern.
        """
        return self, type(self)(
            self.id,
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
        if other.id != self.id:
            raise ValueError
        return type(self)(
            self.id,
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

    def __init__(self, id: int, attrs: dict[str, AttrTypes],
                 source: int = 0, target: int = 0):
        """
        Initialize the function edge pattern.

        Args:
            id:     The function ID.
                    Must be even and positive.
                    Zero to assign next available.
            attrs:  The attribute dictionary.
                    Can only be empty or contain the "_type" string attribute.
            source: The ID of the source relation, or zero if none.
            target: The ID of the target node, or zero if none.
        """
        assert isinstance(attrs, dict)
        if not self.are_attrs_valid(attrs):
            raise ValueError
        assert source == 0 or Relation.is_valid_id(source)
        assert target == 0 or Node.is_valid_id(target)
        super().__init__(id, attrs, source, target)

    @classmethod
    def ref_repr(cls, id: int):
        """Format a reference representation of a pattern ID"""
        assert cls.is_valid_id(id)
        return f"f#{id}"

    def __repr__(self):
        return self.ref_repr(self.id) + repr(self.attrs["_type"]) + (
            "[" +
            (Relation.ref_repr(self.source) if self.source else "") +
            "->" +
            (Node.ref_repr(self.target) if self.target else "") +
            "]"
        )

    def with_updated_attrs(self, attrs: dict[str, AttrTypes]) -> \
            Tuple[Self, Self]:
        """
        Duplicate the pattern with updated attributes.

        Args:
            attrs:  The attribute dictionary to update with.
                    Can only be empty or contain the "_type" string attribute.

        Returns:
            The self and the updated pattern.
        """
        assert isinstance(attrs, dict)
        if not self.are_attrs_valid(attrs):
            raise ValueError
        return super().with_updated_attrs(attrs)


# Element pattern types operated by the graph pattern
GRAPH_ELEMENTS = (Entity, Relation, Function)
GraphElements = Entity | Relation | Function


class Graph:
    """A graph pattern"""

    def __init__(self,
                 elements: dict[int, GraphElements],
                 marks: set[int],
                 left: int, right: int):
        """
        Initialize the graph pattern.

        Args:
            elements:   A dictionary of element IDs and corresponding element
                        (entity/relation/function) patterns. The pattern IDs
                        must match corresponding dictionary keys.
            marks:      A set of IDs of marked elements. Must be a subset of
                        "elements" keys.
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
        assert left != 0
        assert right != 0
        assert all(
            isinstance(id, int) and
            isinstance(e, GRAPH_ELEMENTS) and
            id == e.id
            for id, e in elements.items()
        )
        assert isinstance(marks, set)
        assert marks <= set(elements)
        assert all(
            (not e.source or e.source in elements) and
            (not e.target or e.target in elements)
            for e in elements.values() if isinstance(e, Function)
        ), "A function references an unknown node"

        self.elements = elements
        self.marks = marks
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
                # Skip complete functions
                if element.source and element.target and \
                   "_type" in element.attrs:
                    continue
                function_ids.append(id)
                element_reprs[id] = (f"f{len(function_ids)}",)

        # A dictionary of IDs of relations and lists of tuples of their
        # mark characters, function names, and corresponding actor node IDs.
        relation_functions = {id: [] for id in relation_ids}

        # Collect both complete and incomplete functions (edges)
        for id, element in self.elements.items():
            if not isinstance(element, Function):
                continue
            # If the function is complete
            if element.source and element.target and \
               "_type" in element.attrs:
                relation_functions[element.source].append((
                    ("", "+")[id in self.marks],
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
                    ) if element.source or element.target else "",
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
            ("", "+")[id in self.marks] + "".join(element_reprs[id])
            for id in (entity_ids + relation_ids + function_ids)
        ) + f" > {element_reprs[self.right][0]}"

    def with_replaced_element(
        self, old: GraphElements, new: GraphElements
    ) -> 'Graph':
        """Create a duplicate graph pattern with a pattern replaced"""
        assert old.id in self.elements, "Replacing unknown element pattern"
        assert type(old) is type(new), "Cannot change element type"
        assert old.id == new.id, \
            f"New element has different ID ({new.id} != {old.id})"
        elements = self.elements.copy()
        elements[new.id] = new
        gp = Graph(elements, self.marks, self.left, self.right)
        # print(f"{self} . with_replaced_atom({old}, {new}) -> {gp}")
        return gp

    def __or__(self, other) -> 'Graph':
        """Merge two graph patterns"""
        if not isinstance(other, Graph):
            return NotImplemented
        elements = self.elements.copy()
        for id, element in other.elements.items():
            elements[id] = elements.get(id, element) | element
        return Graph(elements, other.marks, self.left, other.right)

    def __pos__(self):
        """Mark all elements in the graph pattern"""
        return Graph(
            self.elements,
            set(self.elements),
            self.left,
            self.right
        )

    def __neg__(self):
        """Unmark all elements in the graph pattern"""
        return Graph(
            self.elements,
            set(),
            self.left,
            self.right
        )

    def __getattr__(self, key: str) -> 'Graph':
        """Update the implicit attribute of the right element"""
        return self[key]

    def __getitem__(self, key) -> 'Graph':
        """Update the implicit attribute of the right element"""
        element = self.elements[self.right]
        if isinstance(element, Element):
            return self.with_replaced_element(
                *element.with_updated_attrs({"": key})
            )
        raise ValueError

    def __call__(self, **attrs) -> 'Graph':
        """Update attributes of the right element"""
        element = self.elements[self.right]
        if isinstance(element, Element):
            return self.with_replaced_element(
                *element.with_updated_attrs(attrs)
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
            node = left_element
            if isinstance(right_element, Function):
                function = right_element
            else:
                raise ValueError
        # Else, if the node is on the right
        elif isinstance(right_element, Node):
            node = right_element
            if isinstance(left_element, Function):
                function = left_element
            else:
                raise ValueError
        else:
            raise ValueError

        # If the function is already filled
        if function.target:
            raise ValueError

        combined = left | right
        function = combined.elements[function.id]
        return combined.with_replaced_element(
            *function.with_updated_endpoints(target=node.id)
        )

    def __sub__(self, other) -> 'Graph':
        """Fill a function with an element (for S - O expression)"""
        return self._fill(self, other)

    def __rsub__(self, other) -> 'Graph':
        """Fill a function with an element (for O - S expression)"""
        return self._fill(other, self)

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
            relation = left_element
            if isinstance(right_element, Function):
                function = right_element
            else:
                raise ValueError
        # Else, if the relation is on the right
        elif isinstance(right_element, Relation):
            relation = right_element
            if isinstance(left_element, Function):
                function = left_element
            else:
                raise ValueError
        else:
            raise ValueError

        # If the function is already assigned
        if function.source:
            raise ValueError

        combined = left | right
        function = combined.elements[function.id]
        return combined.with_replaced_element(
            *function.with_updated_endpoints(source=relation.id)
        )

    def __mul__(self, other) -> 'Graph':
        """Assign a function (for S * O expression)"""
        return self._assign(self, other)

    def __rmul__(self, other) -> 'Graph':
        """Assign a function (for O * S expression)"""
        return self._assign(other, self)

    @staticmethod
    def _shift(left, op: str, right) -> 'Graph':
        """Create a relation or a function for a shift operator"""
        # No it's not, pylint: disable=too-many-return-statements
        assert op in {"<<", ">>"}

        if not isinstance(left, Graph) or not isinstance(right, Graph):
            return NotImplemented

        ltr = op == ">>"
        left_element = left.elements[left.right]
        right_element = right.elements[right.left]

        if isinstance(left_element, Entity) and \
           isinstance(right_element, Entity) or \
           isinstance(left_element, Relation) and \
           isinstance(right_element, Relation):
            relation = RelationGraph()
            if ltr:
                return left - "source" * relation * "target" - right
            else:
                return left - "target" * relation * "source" - right
        elif isinstance(left_element, Relation) and \
                isinstance(right_element, Entity):
            if ltr:
                return left * "target" - right
            else:
                return left * "source" - right
        elif isinstance(left_element, Entity) and \
                isinstance(right_element, Relation):
            if ltr:
                return left - "source" * right
            else:
                return left - "target" * right

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


class EntityGraph(Graph):
    """A single-entity graph pattern"""

    def __init__(self, **attrs: AttrTypes):
        """
        Initialize the single-node graph pattern.

        Args:
            attrs:  The attribute dictionary.
        """
        ep = Entity(0, attrs)
        super().__init__({ep.id: ep}, set(), ep.id, ep.id)


class RelationGraph(Graph):
    """A single-relation graph pattern"""

    def __init__(self, **attrs: AttrTypes):
        """
        Initialize the single-relation graph pattern.

        Args:
            attrs:  The relation's attribute dictionary.
        """
        rp = Relation(0, attrs)
        super().__init__({rp.id: rp}, set(), rp.id, rp.id)


class FunctionGraph(Graph):
    """A single-function graph pattern"""

    def __init__(self, type: Optional[str] = None):
        """
        Initialize the single-function graph pattern.

        Args:
            type:   The function's type name, or None for none.
        """
        fp = Function(0, {} if type is None else dict(_type=type))
        super().__init__({fp.id: fp}, set(), fp.id, fp.id)
