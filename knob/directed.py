"""
KNOB - The directed graph (pattern)
"""

from typing import cast, Final, Generator, Dict, Optional, Self
from copy import copy
import graphviz  # type: ignore
from knob.misc import AttrTypes, attrs_repr

# NO, pylint: disable=use-dict-literal
# We need them, pylint: disable=fixme
# We like our "id", pylint: disable=redefined-builtin


class Element:
    """A graph's element (node/edge)"""

    # The next ID to assign to a created element
    __NEXT_ID = 0

    def __init__(self, **attrs: AttrTypes):
        """
        Initialize a graph element.

        Args:
            attrs:  A dictionary of the element's attribute names and values.
        """
        assert isinstance(attrs, dict)
        assert all(
            isinstance(n, str) and isinstance(v, (str, int))
            for n, v in attrs.items()
        )
        self.attrs = attrs.copy()
        self.id = Element.__NEXT_ID
        Element.__NEXT_ID += 1

    def __hash__(self):
        return id(self)

    def ref_repr(self):
        """Format a reference representation of the element"""
        return f"#{self.id}"

    def attrs_repr(self):
        """Format a (preferably compact) representation of attributes"""
        return attrs_repr(self.attrs)

    def __repr__(self):
        return self.ref_repr() + self.attrs_repr()

    def matches(self, element: "Element"):
        """
        Check if this element used as a pattern matches another element.

        Args:
            element:    The element to match.

        Returns:
            True, if this pattern element matches the other element.
            False, if not.
        """
        if isinstance(element, type(self)):
            return set(self.attrs.items()) <= set(element.attrs.items())
        raise NotImplementedError


class Node(Element):
    """A graph's node"""

    def __copy__(self):
        return Node(**self.attrs)

    def ref_repr(self):
        """Format a reference representation of the node"""
        return f"n{super().ref_repr()}"


class Edge(Element):
    """A directed graph's edge"""

    def __init__(self, source: Node, target: Node, **attrs: AttrTypes):
        """
        Initialize a graph's edge.

        Args:
            source: The edge's source node.
            target: The edge's target node.
            attrs:  A dictionary of the edges's attribute names and values.
        """
        assert isinstance(source, Node)
        assert isinstance(target, Node)
        assert isinstance(attrs, dict)
        assert all(
            isinstance(n, str) and isinstance(v, (str, int))
            for n, v in attrs.items()
        )
        super().__init__(**attrs)
        self.source = source
        self.target = target

    def __copy__(self):
        return Edge(self.source, self.target, **self.attrs)

    def get_adjacent_node(self, node: Node) -> Node:
        """
        Get the node adjacent to an endpoint node.
        Assumes the node is an endpoint of this edge.
        """
        assert node in (self.source, self.target)
        return self.target if node is self.source else self.source

    def is_incoming(self, node: Node) -> bool:
        """
        Check if the edge is incoming to a specified node.

        Args:
            node:   The node to check direction for.
                    Assumed to be an edge endpoint.

        Returns:
            True if the edge is incoming for a node, false if outgoing.
        """
        assert node in (self.source, self.target)
        return node is self.target

    def ref_repr(self):
        """Format a reference representation of the edge"""
        return f"e{super().ref_repr()}"

    def __repr__(self):
        return f"{super()!r}" \
            f"[{self.source.ref_repr()}, {self.target.ref_repr()}]"


# Element types operated by the graph
ELEMENTS = (Node, Edge)
Elements = Node | Edge


class Graph:
    """A directed graph"""

    class Mismatch(Exception):
        """Graph didn't match the pattern"""

    def __init__(self,
                 elements: Optional[set[Elements]] = None,
                 marked: Optional[set[Elements]] = None):
        """
        Initialize a graph.

        Args:
            elements:   The set of graph elements (nodes or edges), or None
                        for empty set. Edges in this set can only reference
                        nodes from the same set.
            marked:     The set of elements considered "marked", or None for
                        empty set. Must be a subset of graph elements.
        """
        self.elements: set[Elements] = set()
        self.marked: set[Elements] = set()
        self.add(elements=elements, marked=marked)

    @classmethod
    def coerce(cls, other):
        """
        Try coercing a value to an instance of this class, using the
        to_dg() method, if present.

        Args:
            other: The value to coerce.

        Returns:
            The potentially coerced value.
        """
        if callable(getattr(other, "to_dg", None)):
            other = other.to_dg()
            assert isinstance(other, Graph)
        return other

    def __hash__(self):
        return hash((frozenset(self.elements), frozenset(self.marked)))

    def __eq__(self, other):
        other = self.coerce(other)
        if not isinstance(other, Graph):
            return NotImplemented
        return self.elements == other.elements and self.marked == other.marked

    def get_nodes(self) -> Generator[Node, None, None]:
        """Extract the set of nodes from the set of graph elements"""
        for element in self.elements:
            if isinstance(element, Node):
                yield element

    def get_edges(self) -> Generator[Edge, None, None]:
        """Extract the set of edges from the set of graph elements"""
        for element in self.elements:
            if isinstance(element, Edge):
                yield element

    def get_marked_nodes(self) -> set[Node]:
        """Extract the set of nodes from the set of marked graph elements"""
        return set(filter(
            lambda e: isinstance(e, Node),  # type: ignore
            self.marked
        ))

    def get_marked_edges(self) -> set[Edge]:
        """Extract the set of edges from the set of marked graph elements"""
        return set(filter(
            lambda e: isinstance(e, Edge),  # type: ignore
            self.marked
        ))

    def __repr__(self):
        # Collect node element representations
        elements = {
            node: (
                ("", "+")[node in self.marked],
                f"n{i + 1}",
                node.attrs_repr()
            )
            for i, node in
            enumerate(sorted(self.get_nodes(), key=lambda n: n.id))
        }
        # Add edge element representations
        elements |= {
            edge: (
                ("", "+")[edge in self.marked],
                f"e{i + 1}"
                f"[{elements[edge.source][1]}->{elements[edge.target][1]}]"
                f"{edge.attrs_repr()}"
            )
            for i, edge in
            enumerate(sorted(self.get_edges(), key=lambda n: n.id))
        }
        return "{" + ", ".join(map("".join, list(elements.values()))) + "}"

    def __copy__(self):
        return type(self)(elements=self.elements, marked=self.marked)

    def __or__(self, other):
        other = self.coerce(other)
        if not isinstance(other, Graph):
            return NotImplemented
        return type(self)(elements=self.elements | other.elements,
                          marked=self.marked | other.marked)

    def __ior__(self, other):
        other = self.coerce(other)
        if not isinstance(other, Graph):
            return NotImplemented
        self.elements |= other.elements
        self.marked |= other.marked
        return self

    def __sub__(self, other):
        other = self.coerce(other)
        if not isinstance(other, Graph):
            return NotImplemented
        return type(self)(elements=self.elements - other.elements,
                          marked=self.marked - other.marked)

    def __isub__(self, other):
        other = self.coerce(other)
        if not isinstance(other, Graph):
            return NotImplemented
        self.elements -= other.elements
        self.marked -= other.marked
        return self

    def __and__(self, other):
        other = self.coerce(other)
        if not isinstance(other, Graph):
            return NotImplemented
        return type(self)(elements=self.elements & other.elements,
                          marked=self.marked & other.marked)

    def __iand__(self, other):
        other = self.coerce(other)
        if not isinstance(other, Graph):
            return NotImplemented
        self.elements &= other.elements
        self.marked &= other.marked
        return self

    def __xor__(self, other):
        other = self.coerce(other)
        if not isinstance(other, Graph):
            return NotImplemented
        return type(self)(elements=self.elements ^ other.elements,
                          marked=self.marked ^ other.marked)

    def __ixor__(self, other):
        other = self.coerce(other)
        if not isinstance(other, Graph):
            return NotImplemented
        self.elements ^= other.elements
        self.marked ^= other.marked
        return self

    def add(self,
            elements: Optional[set[Elements]] = None,
            marked: Optional[set[Elements]] = None) -> Self:
        """
        Add elements to the graph.

        Args:
            elements:   The set of graph elements (nodes or edges) to add, or
                        None for empty set. Edges can only reference nodes
                        from this or the existing set of elements.
            marked:     The set of elements to consider "marked", or None for
                        empty set. Must be a subset of existing and added
                        elements.

        Returns:
            The modified graph (self).
        """
        if elements is None:
            elements = set()
        assert isinstance(elements, set)
        assert all(isinstance(e, ELEMENTS) for e in elements)
        new_elements = self.elements | elements
        assert all(
            not isinstance(e, Edge) or
            e.source in new_elements and
            e.target in new_elements
            for e in elements
        ), "Edges reference unknown nodes"
        if marked is None:
            marked = set()
        assert isinstance(marked, set)
        assert marked <= new_elements, "Unknown elements are being marked"
        self.elements = new_elements
        self.marked |= marked
        return self

    def remove(self,
               elements: Optional[set[Elements]] = None,
               marked: Optional[set[Elements]] = None) -> Self:
        """
        Remove elements from the graph.

        Args:
            elements:   The set of graph elements (nodes or edges) to remove.
                        Must contain all existing edges incident to any nodes
                        in the set. Unknown elements are ignored.
            marked:     A set of elements to "unmark", or None for empty set.
                        Unknown elements, or already unmarked elements are
                        ignored.

        Returns:
            The modified graph (self).
        """
        if elements is None:
            elements = set()
        assert isinstance(elements, set)
        assert all(isinstance(e, ELEMENTS) for e in elements)
        if marked is None:
            marked = set()
        assert isinstance(marked, set)
        assert self.get_incident_edges(
            {e for e in elements if isinstance(e, Node)}
        ) <= elements, "Incident edges are not being removed"
        self.marked -= marked
        self.marked -= elements
        self.elements -= elements
        return self

    @classmethod
    def graphviz_trim(cls, v: AttrTypes):
        """
        Trim a value to a certain maximum length, if necessary, for graphviz.
        """
        return v[:61] + "..." if isinstance(v, str) and len(v) > 64 else v

    @classmethod
    def graphviz_quote(cls, v: AttrTypes):
        """Quote a value, if necessary, for graphviz"""
        return (
            str(v)
            if isinstance(v, int) or v.isidentifier()
            else repr(v)
        )

    @classmethod
    def graphviz_format_label(cls, id: str, element: Elements, marked: bool):
        """Format a label for a graphviz element"""
        return "\\n".join(
            [("", "+")[marked] + id] +
            [f"{cls.graphviz_quote(n)}={cls.graphviz_trim(v)!r}"
             for n, v in element.attrs.items()]
        )

    def graphviz(self) -> str:
        """
        Render the graph into a Graphviz representation.

        Returns:
            The rendered Graphviz source code.
        """
        # Generate element graphviz IDs
        element_ids = {
            node: str(i + 1)
            for i, node in
            enumerate(sorted(self.get_nodes(), key=lambda n: n.id))
        } | {
            edge: str(i + 1)
            for i, edge in
            enumerate(sorted(self.get_edges(), key=lambda n: n.id))
        }

        graph = graphviz.Digraph(node_attr=dict(shape="box"))
        for element, id in element_ids.items():
            label = self.graphviz_format_label(
                str(id), element, element in self.marked
            )
            if isinstance(element, Node):
                graph.node(id, label=label)
            elif isinstance(element, Edge):
                graph.edge(
                    element_ids[element.source], element_ids[element.target],
                    label=label
                )
        return graph.source

    def get_incident_edges(self, nodes: set[Node] | Node) -> set[Edge]:
        """
        Get edges incident to nodes in the specified set (both incoming and
        outgoing).

        Args:
            nodes:  The set of nodes, or a single node to get the incident
                    edges for.

        Returns:
            A set containing edges incident to the nodes.
        """
        if isinstance(nodes, Node):
            nodes = {nodes}
        return set(filter(
            lambda e: isinstance(e, Edge) and  # type: ignore
            {e.source, e.target} & nodes,
            self.elements
        ))

    def detailed_match(self, other: "Graph") -> Generator[
        Dict[Elements, Elements], None, None
    ]:
        """
        Find all matches of this graph, as a pattern, against another graph.

        Args:
            other:  The graph to match this graph against.

        Yields:
            A dictionary of each element from this graph, used as a pattern,
            and the matched element of the other graph, whenever this graph
            matches completely.
        """
        self_nodes = set(self.get_nodes())
        self_edges = set(self.get_edges())
        other_nodes = set(other.get_nodes())
        other_edges = set(other.get_edges())

        def match_components(
            matches: Dict[Elements, Elements],
            self_node: Node,
            other_node: Node
        ) -> Generator[
            Dict[Elements, Elements], None, None
        ]:
            """
            Find all subgraphs of a component of the other graph fully
            matching a component of this graph, used as a pattern.

            A component is defined as a node (assumed matching, and in
            "matches"), all nodes reachable from it, and all edges in between,
            minus whatever is already in "matches".

            Args:
                matches:        A dictionary of each element from this graph,
                                used as a pattern, and the element of the
                                other graph that has matched so far.
                self_node:      The node belonging to the pattern component of
                                this graph. Must match "other_node", and be in
                                "matched_self".
                other_node:     The node belonging to the component of the
                                other graph, to be matched. Must be matched by
                                "self_node", and be in "matched_other".

            Yields:
                A dictionary of each element from this graph, used as a
                pattern, and the matched element of the other graph
                ("matches"), whenever a component match is complete.
            """
            assert isinstance(matches, dict)
            assert all(type(s) is type(o) and
                       isinstance(s, Element) and
                       s in self_nodes and o in other_nodes or
                       s in self_edges and o in other_edges
                       for s, o in matches.items())
            self_matches: Final[set] = set(matches.keys())
            other_matches: Final[set] = set(matches.values())
            assert all(
                s.source in self_matches and s.target in self_matches
                for s in self_matches if isinstance(s, Edge)
            )
            assert all(
                o.source in other_matches and o.target in other_matches
                for o in other_matches if isinstance(o, Edge)
            )
            assert matches.get(self_node) is other_node

            # print_stack_indented(f"match_components"
            #                      f"{(matches, self_node, other_node)}")

            rem_self_edges = \
                self.get_incident_edges(self_node) - self_matches

            # If there are no edges left to match
            if not rem_self_edges:
                # print_stack_indented(f"<- {matches}")
                yield matches
                return

            rem_other_edges = \
                other.get_incident_edges(other_node) - other_matches

            # For every combination of self and other edges
            for self_edge in rem_self_edges:
                self_adj_node = self_edge.get_adjacent_node(self_node)
                self_adj_matched = self_adj_node in self_matches
                for other_edge in rem_other_edges:
                    other_adj_node = other_edge.get_adjacent_node(other_node)
                    other_adj_matched = other_adj_node in other_matches
                    # If edge directions or attributes mismatch,
                    # or the adjacent node already matched something else
                    if not (
                        self_edge.is_incoming(self_node) ==
                        other_edge.is_incoming(other_node) and
                        self_edge.matches(other_edge) and
                        self_adj_matched == other_adj_matched and
                        matches.get(self_adj_node, other_adj_node) is
                        other_adj_node
                    ):
                        continue

                    # If the adjacents matched already
                    if self_adj_node in matches:
                        # Match remaining edges
                        yield from match_components(
                            matches | {self_edge: other_edge},
                            self_node, other_node
                        )
                        continue

                    # If the adjacents don't match
                    if not self_adj_node.matches(other_adj_node):
                        continue

                    # For each adjacent subgraph match
                    for new_matches in match_components(
                            matches | {self_edge: other_edge,
                                       self_adj_node: other_adj_node},
                            self_adj_node, other_adj_node
                    ):
                        # Match remaining edges
                        yield from match_components(
                            new_matches, self_node, other_node
                        )

        def match_subgraphs(
            matches: Dict[Elements, Elements]
        ) -> Generator[
            Dict[Elements, Elements], None, None
        ]:
            """
            Match this graph, used as a pattern, to subgraphs in the other.

            Args:
                matches:    A dictionary of each element from this graph, used
                            as a pattern, and the element of the other graph
                            that has matched so far.

            Yields:
                A dictionary of each element from this graph, used as a
                pattern, and the matched element of the other graph
                ("matches"), whenever this graph matches completely.
            """
            assert isinstance(matches, dict)
            assert all(type(s) is type(o) and
                       s in self_nodes and o in other_nodes or
                       s in self_edges and o in other_edges
                       for s, o in matches.items())
            self_matches: Final[set] = set(matches.keys())
            other_matches: Final[set] = set(matches.values())
            assert all(
                s.source in self_matches and s.target in self_matches
                for s in self_matches if isinstance(s, Edge)
            )
            assert all(
                o.source in other_matches and o.target in other_matches
                for o in other_matches if isinstance(o, Edge)
            )

            # print_stack_indented(f"match_subgraphs({matches})")
            if self_matches == self.elements:
                # print_stack_indented(f"<- {matches}")
                yield matches
                return
            rem_self_nodes = self_nodes - self_matches
            rem_other_nodes = other_nodes - other_matches
            for self_node in rem_self_nodes:
                for other_node in rem_other_nodes:
                    # If the nodes don't match
                    if not self_node.matches(other_node):
                        continue
                    # For each component match
                    for new_matches in match_components(
                        matches | {self_node: other_node},
                        self_node, other_node
                    ):
                        # Match the remaining components
                        yield from match_subgraphs(new_matches)

        # print_stack_indented(f"detailed_match{(self, other)}")
        # TODO: Something smarter than this
        matches_set = set()
        for matches in match_subgraphs({}):
            frozen_matches = frozenset(matches.items())
            if frozen_matches not in matches_set:
                # print_stack_indented(f"<- {matches}")
                yield matches
                matches_set.add(frozen_matches)

    def separate_match(self, other: "Graph") -> Generator["Graph", None, None]:
        """
        Find all matches of this graph as a pattern against another graph.

        Args:
            other:  The graph to match this graph against.

        Yields:
            Subgraphs of the other graph that match this graph.
        """
        # print_stack_indented(f"match{(self, other)}")
        for matches in self.detailed_match(other):
            g = type(other)(set(matches.values()))
            # print_stack_indented(f"<- {g}")
            yield g

    def match(self, other: "Graph") -> "Graph":
        """
        Produce a graph containing all matches of this graph as a pattern
        against another graph.

        Args:
            other:  The graph to match this graph against.

        Returns:
            The graph with all the matches of this graph against the other.

        Raises:
            Graph.Mismatch: the graph didn't match the other graph.
        """
        matched = False
        elements: set[Elements] = set()
        for matches in self.detailed_match(other):
            matched = True
            elements.update(matches.values())
        if matched:
            return type(other)(elements)
        raise Graph.Mismatch()

    def __matmul__(self, other):
        """Produce a subgraph matching another graph used as a pattern"""
        other = self.coerce(other)
        if isinstance(other, Graph):
            return other.match(self)
        return NotImplemented

    def __rmatmul__(self, other):
        """Produce a subgraph of another graph matching this pattern"""
        other = self.coerce(other)
        if isinstance(other, Graph):
            return self.match(other)
        return NotImplemented

    def matches(self, other: "Graph") -> bool:
        """
        Check if this graph, used as a pattern, matches another graph.

        Args:
            other:  The graph to match this graph against.

        Returns:
            True if the graph matches the other graph.
        """
        return bool(next(self.detailed_match(other), False))

    def graft(self, other: "Graph") -> Self:
        """
        Graft another graph onto this one, adding marked elements from the
        other graph, connecting the nodes matching the rest.

        Args:
            other:      The graph to graft onto this one.
                        The "unmarked" elements of this graph will be matched
                        against this graph to find the nodes where the added
                        "marked" elements will be connected.

        Returns:
            The graph with the elements grafted onto it.

        Raises:
            Graph.Mismatch: the graph didn't match the other graph.
        """
        marked_nodes = other.get_marked_nodes()
        marked_edges = other.get_marked_edges()

        edges_internal = {
            edge for edge in marked_edges
            if {edge.source, edge.target} <= marked_nodes
        }
        edges_external = marked_edges - edges_internal

        edges_to_add = None
        for matches in type(self)(
            other.elements - marked_nodes - marked_edges -
            other.get_incident_edges(marked_nodes)
        ).detailed_match(self):
            if edges_to_add is None:
                edges_to_add = edges_internal
            edges_to_add |= {
                Edge(
                    source=edge.source
                    if edge.source in marked_nodes
                    else cast(Node, matches[edge.source]),
                    target=edge.target
                    if edge.target in marked_nodes
                    else cast(Node, matches[edge.target]),
                    **edge.attrs
                )
                for edge in edges_external
            }

        if edges_to_add is None:
            raise Graph.Mismatch()
        return self.add(marked_nodes | edges_to_add)

    def __pow__(self, other):
        """Graft the other graph onto this one"""
        other = self.coerce(other)
        if isinstance(other, Graph):
            return copy(self).graft(other)
        return NotImplemented

    def __ipow__(self, other):
        """Graft the other graph onto this one, in-place"""
        other = self.coerce(other)
        if isinstance(other, Graph):
            return self.graft(other)
        return NotImplemented

    def prune(self, other: "Graph") -> Self:
        """
        Prune another graph from this one by matching, and removing the
        elements matching the specified ones.

        Args:
            other:      The graph to prune from this one.
                        It will be matched against this graph, and then
                        elements matching "marked" ones will be removed.

        Returns:
            A new graph with the elements pruned from it.

        Raises:
            Graph.Mismatch: the graph didn't match the other graph.
        """
        pruned = None
        for matches in other.detailed_match(self):
            if pruned is None:
                pruned = self
            pruned.remove({matches[element] for element in other.marked})
        if pruned is None:
            raise Graph.Mismatch()
        return pruned

    def __floordiv__(self, other):
        """Prune the other graph from this one"""
        other = self.coerce(other)
        if isinstance(other, Graph):
            return copy(self).prune(other)
        return NotImplemented

    def __ifloordiv__(self, other):
        """Prune the other graph from this one, in-place"""
        other = self.coerce(other)
        if isinstance(other, Graph):
            return self.prune(other)
        return NotImplemented
