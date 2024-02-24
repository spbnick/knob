"""
KNOB - The directed graph (pattern)
"""

from typing import cast, Final, Generator, Dict, Set, Optional
from copy import copy
import graphviz  # type: ignore
from knob6.misc import AttrTypes, attrs_repr

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

    def __init__(self, *elements: Elements,
                 nodes: Optional[Set[Node]] = None,
                 edges: Optional[Set[Edge]] = None,
                 marked: Optional[Set[Elements]] = None):
        """
        Initialize a graph.

        Args:
            elements:   A tuple of graph elements (nodes or edges).
                        Nodes referenced by edges in this tuple are also added
                        to the graph.
            nodes:      A set of nodes to add to the elements,
                        or None for empty set.
            edges:      A set of edges to add to the elements,
                        or None for empty set.
                        Nodes referenced by these edges must exist in either
                        "elements" (possibly via edges) or "nodes".
            marked:     A set of elements considered "marked", or None for
                        empty set. Must be a subset of graph elements.
                        Nodes referenced by edges in this set are *not*
                        considered marked as well.
        """
        self.nodes: Set[Node] = set()
        self.edges: Set[Edge] = set()
        self.marked: Set[Elements] = set()
        self.add(*elements, nodes=nodes, edges=edges, marked=marked)

    def __hash__(self):
        return hash((frozenset(self.nodes),
                     frozenset(self.edges),
                     frozenset(self.marked)))

    def __eq__(self, other):
        if not isinstance(other, Graph):
            return NotImplemented
        return (
            self.nodes == other.nodes and
            self.edges == other.edges and
            self.marked == other.marked
        )

    def __repr__(self):
        # A map of nodes and their representations
        nodes = {
            node: (
                ("", "+")[node in self.marked],
                f"n{i + 1}",
                node.attrs_repr()
            )
            for i, node in enumerate(sorted(self.nodes, key=lambda n: n.id))
        }
        # A map of edges and their representations
        edges = {
            edge: (
                ("", "+")[edge in self.marked],
                f"e{i + 1}"
                f"[{nodes[edge.source][1]}->{nodes[edge.target][1]}]"
                f"{edge.attrs_repr()}"
            )
            for i, edge in enumerate(sorted(self.edges, key=lambda e: e.id))
        }
        return "{" + ", ".join(
            map("".join, list(nodes.values()) + list(edges.values()))
        ) + "}"

    def __copy__(self):
        return Graph(nodes=self.nodes, edges=self.edges, marked=self.marked)

    def __or__(self, other):
        if not isinstance(other, Graph):
            return NotImplemented
        return Graph(nodes=self.nodes | other.nodes,
                     edges=self.edges | other.edges,
                     marked=self.marked | other.marked)

    def __ior__(self, other):
        if not isinstance(other, Graph):
            return NotImplemented
        self.nodes |= other.nodes
        self.edges |= other.edges
        self.marked |= other.marked
        return self

    def add(self, *elements: Elements,
            nodes: Optional[Set[Node]] = None,
            edges: Optional[Set[Edge]] = None,
            marked: Optional[Set[Elements]] = None):
        """
        Add elements to the graph.

        Args:
            elements:   A tuple of graph elements (nodes or edges).
                        Nodes referenced by edges in this tuple are also added
                        to the graph.
            nodes:      A set of nodes to add to the elements,
                        or None for empty set.
            edges:      A set of edges to add to the elements,
                        or None for empty set.
                        Nodes referenced by these edges must exist in either
                        "elements" (possibly via edges) or "nodes".
            marked:     A set of elements to "mark", or None for empty set.
                        Must be a subset of existing and added graph elements.
                        Nodes referenced by edges in this set are *not*
                        considered marked as well.

        Returns:
            The modified graph (self).
        """
        assert isinstance(elements, tuple)
        assert all(isinstance(element, ELEMENTS) for element in elements)
        assert nodes is None or isinstance(nodes, set) and all(
            isinstance(node, Node) for node in nodes
        )
        assert edges is None or isinstance(edges, set) and all(
            isinstance(edge, Edge) for edge in edges
        )
        assert marked is None or isinstance(marked, set)

        for element in elements:
            if isinstance(element, Node):
                self.nodes.add(element)
            elif isinstance(element, Edge):
                self.edges.add(element)
                self.nodes.add(element.source)
                self.nodes.add(element.target)
        if nodes:
            self.nodes |= nodes
        if edges:
            assert all(
                edge.source in self.nodes and
                edge.target in self.nodes
                for edge in edges
            ), f"Edges {edges} reference nodes not in {nodes}"
            self.edges |= edges

        if marked:
            assert marked <= self.nodes | self.edges
            self.marked |= marked

        return self

    def remove(self, *elements: Elements,
               nodes: Optional[Set[Node]] = None,
               edges: Optional[Set[Edge]] = None,
               marked: Optional[Set[Elements]] = None):
        """
        Remove elements from the graph.

        Args:
            elements:   A tuple of graph elements (nodes or edges).
                        Any edges incident to the nodes in this tuple are
                        also removed from the graph.
            nodes:      A set of nodes to remove, or None for empty set.
                        Any edges incident to these nodes must exist in
                        either "elements" or "edges".
            edges:      A set of edges to remove, or None for empty set.
                        Must contain all edges incident to nodes in "nodes".
            marked:     A set of elements to "unmark", or None for empty set.
                        Must be a subset of existing elements.
                        Nodes referenced by edges in this set are *not*
                        considered marked as well.

        Returns:
            The modified graph (self).
        """
        assert isinstance(elements, tuple)
        assert all(isinstance(element, ELEMENTS) for element in elements)
        assert nodes is None or isinstance(nodes, set) and all(
            isinstance(node, Node) for node in nodes
        )
        assert edges is None or isinstance(edges, set) and all(
            isinstance(edge, Edge) for edge in edges
        )
        assert marked is None or \
            isinstance(marked, set) and marked <= self.nodes | self.edges

        if marked:
            self.marked -= marked

        if nodes is None:
            nodes = set()
        if edges is None:
            edges = set()
        for element in set(elements):
            if isinstance(element, Node):
                edges |= self.get_incident_edges(element)
                nodes.add(element)
            elif isinstance(element, Edge):
                edges.add(element)

        assert all(self.get_incident_edges(node) <= edges for node in nodes)
        self.nodes -= nodes
        self.edges -= edges
        self.marked -= nodes | edges

        return self

    def graphviz(self) -> str:
        """
        Render the graph into a Graphviz representation.

        Returns:
            The rendered Graphviz source code.
        """
        # A map of nodes and their graphviz IDs
        nodes = {
            node: str(i + 1)
            for i, node in enumerate(sorted(self.nodes, key=lambda n: n.id))
        }

        # A map of edges and their graphviz IDs
        edges = {
            edge: str(i + 1)
            for i, edge in enumerate(sorted(self.edges, key=lambda n: n.id))
        }

        # A map of elements and their graphviz IDs
        elements = nodes | edges

        def trim(v: AttrTypes):
            """Trim a value to a certain maximum length, if necessary"""
            return v[:61] + "..." if isinstance(v, str) and len(v) > 64 else v

        def quote(v: AttrTypes):
            """Quote a value, if necessary"""
            return (
                str(v)
                if isinstance(v, int) or v.isidentifier()
                else repr(v)
            )

        def format_label(element: Node | Edge):
            """Format a label for a graphviz element"""
            return "\\n".join(
                [("", "+")[element in self.marked] + elements[element]] +
                [f"{quote(n)}={quote(trim(v))}"
                 for n, v in element.attrs.items()]
            )

        graph = graphviz.Digraph(node_attr=dict(shape="box"))
        for node, id in nodes.items():
            graph.node(id, label=format_label(node))
        for edge in self.edges:
            graph.edge(nodes[edge.source], nodes[edge.target],
                       label=format_label(edge))
        return graph.source

    def get_incident_edges(self, node: Node) -> Set[Edge]:
        """
        Get edges incident to a node (both incoming and outgoing).

        Args:
            node:   The node to get the edges for.

        Returns:
            A set containing edges incident to the node.
        """
        return set(filter(lambda e: node in (e.source, e.target), self.edges))

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
                       s in self.nodes and o in other.nodes or
                       s in self.edges and o in other.edges
                       for s, o in matches.items())
            self_matches: Final[Set] = set(matches.keys())
            other_matches: Final[Set] = set(matches.values())
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

            rem_self_edges = self.get_incident_edges(self_node) - self_matches

            # If there are no edges left to match
            if not rem_self_edges:
                # print_stack_indented(f"<- {matches}")
                yield matches
                return

            rem_other_edges = other.get_incident_edges(other_node) - \
                other_matches

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
                       s in self.nodes and o in other.nodes or
                       s in self.edges and o in other.edges
                       for s, o in matches.items())
            self_matches: Final[Set] = set(matches.keys())
            other_matches: Final[Set] = set(matches.values())
            assert all(
                s.source in self_matches and s.target in self_matches
                for s in self_matches if isinstance(s, Edge)
            )
            assert all(
                o.source in other_matches and o.target in other_matches
                for o in other_matches if isinstance(o, Edge)
            )

            # print_stack_indented(f"match_subgraphs({matches})")
            if self_matches == (self.nodes | self.edges):
                # print_stack_indented(f"<- {matches}")
                yield matches
                return
            rem_self_nodes = self.nodes - self_matches
            rem_other_nodes = other.nodes - other_matches
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

    def match(self, other: "Graph") -> Generator["Graph", None, None]:
        """
        Find all matches of this graph as a pattern against another graph.

        Args:
            other:  The graph to match this graph against.

        Yields:
            Subgraphs of the other graph that match this graph.
        """
        # print_stack_indented(f"match{(self, other)}")
        for matches in self.detailed_match(other):
            g = Graph(*matches.values())
            # print_stack_indented(f"<- {g}")
            yield g

    def matches(self, other: "Graph") -> bool:
        """
        Check if this graph, used as a pattern, matches another graph.

        Args:
            other:  The graph to match this graph against.

        Returns:
            True if the graph matches the other graph.
        """
        return bool(next(self.detailed_match(other), False))

    def graft(self, other: "Graph"):
        """
        Graft another graph onto this one, adding marked elements from the
        other graph, connecting the nodes matching the rest.

        Args:
            other:      The graph to graft onto this one.
                        The "unmarked" elements of this graph will be matched
                        against this graph to find the nodes where the added
                        "marked" elements will be connected.

        Returns:
            A new graph with the elements grafted onto it,
            or None if there were no matches.
        """
        marked_nodes = {e for e in other.marked if isinstance(e, Node)}
        marked_edges = {e for e in other.marked if isinstance(e, Edge)}

        edges_internal = {
            edge for edge in marked_edges
            if {edge.source, edge.target} <= marked_nodes
        }
        edges_external = marked_edges - edges_internal

        edges_to_add = None
        for matches in Graph(
            nodes=other.nodes - marked_nodes,
            edges=other.edges - marked_edges
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

        return None if edges_to_add is None \
            else copy(self).add(nodes=marked_nodes, edges=edges_to_add)

    def prune(self, other: "Graph"):
        """
        Prune another graph from this one by matching, and removing the
        elements matching the specified ones.

        Args:
            other:      The graph to prune from this one.
                        It will be matched against this graph, and then
                        elements matching "marked" ones will be removed.

        Returns:
            A new graph with the elements pruned from it,
            or None if there were no matches.
        """
        pruned = None
        for matches in other.detailed_match(self):
            if pruned is None:
                pruned = copy(self)
            pruned.remove(*(
                matches[element] for element in other.marked
            ))
        return pruned
