"""
KNOB - Knowledge builder
"""

from typing import cast, Final, Generator, Dict, Set, Union, Optional
from copy import copy
import inspect
import graphviz  # type: ignore

# Calm down, pylint: disable=too-few-public-methods
# NO, pylint: disable=use-dict-literal
# We need them, pylint: disable=fixme
# We like our "id", pylint: disable=redefined-builtin


def _print_stack_indented(*args, **kwargs):
    indent = '    ' * (len(inspect.stack()) - 1)
    print(indent[:-1], *args, **kwargs)


class Element:
    """A graph's element (node/edge)"""

    # The next ID to assign to a created element
    __NEXT_ID = 0

    def __init__(self, **attrs: Union[str, int]):
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

    def __repr__(self):
        repr_str = self.ref_repr()
        if self.attrs:
            repr_str += "(" + ", ".join(
                (k if k.isidentifier() else repr(k)) + "=" + repr(v)
                for k, v in self.attrs.items()
            ) + ")"
        return repr_str

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

    def __init__(self, source: Node, target: Node, **attrs: Union[str, int]):
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


class Graph:
    """A directed graph"""

    def __init__(self, *elements: Union[Node, Edge],
                 nodes: Optional[Set[Node]] = None,
                 edges: Optional[Set[Edge]] = None):
        """
        Initialize a graph.

        Args:
            elements:   A tuple of graph elements (nodes or edges).
                        Nodes references by edges in this tuple are also added
                        to the graph.
            nodes:      A set of nodes to add to the elements,
                        or None for empty set.
            edges:      A set of edges to add to the elements,
                        or None for empty set.
                        Nodes referenced by these edges must exist in either
                        "elements" (possibly via edges) or "nodes".
        """
        self.nodes: Set[Node] = set()
        self.edges: Set[Edge] = set()
        self.add(*elements, nodes=nodes, edges=edges)

    def __hash__(self):
        return hash((frozenset(self.nodes), frozenset(self.edges)))

    def __eq__(self, other):
        if not isinstance(other, Graph):
            return NotImplemented
        return self.nodes == other.nodes and self.edges == other.edges

    def __repr__(self):
        def format_attrs(attrs: dict[str, Union[str, int]]):
            if any(not k.isidentifier() for k in attrs):
                return "{" + ", ".join(
                    f"{k!r}: {v!r}" for k, v in attrs.items()
                ) + "}"
            if attrs:
                return "(" + ", ".join(
                    f"{k}={v!r}" for k, v in attrs.items()
                ) + ")"
            return ""

        # A map of nodes and their representations
        nodes = {
            node: (f"n{i + 1}", format_attrs(node.attrs))
            for i, node in enumerate(sorted(self.nodes, key=lambda n: n.id))
        }
        # A map of edges and their representations
        edges = {
            edge: (
                f"e{i + 1}"
                f"[{nodes[edge.source][0]}->{nodes[edge.target][0]}]"
                f"{format_attrs(edge.attrs)}",
            )
            for i, edge in enumerate(sorted(self.edges, key=lambda e: e.id))
        }
        return "{" + ", ".join(
            map("".join, list(nodes.values()) + list(edges.values()))
        ) + "}"

    def __copy__(self):
        return Graph(nodes=self.nodes, edges=self.edges)

    def __or__(self, other):
        if not isinstance(other, Graph):
            return NotImplemented
        return Graph(nodes=self.nodes | other.nodes,
                     edges=self.edges | other.edges)

    def __ior__(self, other):
        if not isinstance(other, Graph):
            return NotImplemented
        self.nodes |= other.nodes
        self.edges |= other.edges
        return self

    def add(self, *elements: Union[Node, Edge],
            nodes: Optional[Set[Node]] = None,
            edges: Optional[Set[Edge]] = None):
        """
        Add elements to the graph.

        Args:
            elements:   A tuple of graph elements (nodes or edges).
                        Nodes references by edges in this tuple are also added
                        to the graph.
            nodes:      A set of nodes to add to the elements,
                        or None for empty set.
            edges:      A set of edges to add to the elements,
                        or None for empty set.
                        Nodes referenced by these edges must exist in either
                        "elements" (possibly via edges) or "nodes".

        Returns:
            The modified graph (self).
        """
        assert isinstance(elements, tuple)
        assert all(isinstance(element, (Node, Edge)) for element in elements)
        assert nodes is None or isinstance(nodes, set) and all(
            isinstance(node, Node) for node in nodes
        )
        assert edges is None or isinstance(edges, set) and all(
            isinstance(edge, Edge) for edge in edges
        )
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
        return self

    def remove(self, *elements: Union[Node, Edge],
               nodes: Optional[Set[Node]] = None,
               edges: Optional[Set[Edge]] = None):
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

        Returns:
            The modified graph (self).
        """
        assert isinstance(elements, tuple)
        assert all(isinstance(element, (Node, Edge)) for element in elements)
        assert nodes is None or isinstance(nodes, set) and all(
            isinstance(node, Node) for node in nodes
        )
        assert edges is None or isinstance(edges, set) and all(
            isinstance(edge, Edge) for edge in edges
        )
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

        def trim(v: Union[str, int]):
            """Trim a value to a certain maximum length, if necessary"""
            return v[:61] + "..." if isinstance(v, str) and len(v) > 64 else v

        def quote(v: Union[str, int]):
            """Quote a value, if necessary"""
            return (
                str(v)
                if isinstance(v, int) or v.isidentifier()
                else repr(v)
            )

        def format_label(element: Node | Edge):
            """Format a label for a graphviz element"""
            return "\\n".join(
                [elements[element]] +
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
        Dict[Union[Node, Edge], Union[Node, Edge]], None, None
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
            matches: Dict[Union[Node, Edge], Union[Node, Edge]],
            self_node: Node,
            other_node: Node
        ) -> Generator[
            Dict[Union[Node, Edge], Union[Node, Edge]], None, None
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

            # _print_stack_indented(f"match_components"
            #                       f"{(matches, self_node, other_node)}")

            rem_self_edges = self.get_incident_edges(self_node) - self_matches

            # If there are no edges left to match
            if not rem_self_edges:
                # _print_stack_indented(f"<- {matches}")
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
            matches: Dict[Union[Node, Edge], Union[Node, Edge]]
        ) -> Generator[
            Dict[Union[Node, Edge], Union[Node, Edge]], None, None
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

            # _print_stack_indented(f"match_subgraphs({matches})")
            if self_matches == (self.nodes | self.edges):
                # _print_stack_indented(f"<- {matches}")
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

        # _print_stack_indented(f"detailed_match{(self, other)}")
        # TODO: Something smarter than this
        matches_set = set()
        for matches in match_subgraphs({}):
            frozen_matches = frozenset(matches.items())
            if frozen_matches not in matches_set:
                # _print_stack_indented(f"<- {matches}")
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
        # _print_stack_indented(f"match{(self, other)}")
        for matches in self.detailed_match(other):
            g = Graph(*matches.values())
            # _print_stack_indented(f"<- {g}")
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

    def graft(self, other: "Graph", *elements: Union[Node, Edge]):
        """
        Graft another graph onto this one, adding specified elements from the
        other graph, connecting the nodes matching the rest.

        Args:
            other:      The graph to graft onto this one.
                        The elements of this graph, which are not in
                        "elements" will be matched against this graph to find
                        the nodes where the added elements should be
                        connected.
            elements:   The elements of the drafted graph, which should be
                        added to this one. All elements must be from the
                        "other" graph.

        Returns:
            A new graph with the elements grafted onto it,
            or None if there were no matches.
        """
        element_set = set(elements)
        nodes = other.nodes & element_set
        edges = other.edges & element_set
        assert element_set == nodes | edges

        edges_internal = {
            edge for edge in edges
            if {edge.source, edge.target} <= nodes
        }
        edges_external = edges - edges_internal

        edges_to_add = None
        for matches in Graph(
            nodes=other.nodes - nodes,
            edges=other.edges - edges
        ).detailed_match(self):
            if edges_to_add is None:
                edges_to_add = edges_internal
            edges_to_add |= {
                Edge(
                    source=edge.source
                    if edge.source in nodes
                    else cast(Node, matches[edge.source]),
                    target=edge.target
                    if edge.target in nodes
                    else cast(Node, matches[edge.target]),
                    **edge.attrs
                )
                for edge in edges_external
            }

        return None if edges_to_add is None \
            else copy(self).add(nodes=nodes, edges=edges_to_add)

    def prune(self, other: "Graph", *elements: Union[Node, Edge]):
        """
        Prune another graph from this one by matching, and removing the
        elements matching the specified ones.

        Args:
            other:      The graph to prune from this one.
                        It will be matched against this graph, and then
                        elements matching the ones in "elements" will be
                        removed.
            elements:   The elements of the "other" graph, which should match
                        the elements to be removed from this one. All elements
                        must be from the "other" graph.

        Returns:
            A new graph with the elements pruned from it,
            or None if there were no matches.
        """
        element_set = set(elements)
        assert element_set <= (other.nodes | other.edges)
        pruned = None
        for matches in other.detailed_match(self):
            if pruned is None:
                pruned = copy(self)
            pruned.remove(*(
                matches[element] for element in element_set
            ))
        return pruned
