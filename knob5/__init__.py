"""
KNOB - Knowledge builder - a module for creating knowledge (hyper)graphs.
"""

from typing import Final, Generator, Dict, Set, Union, Optional, Tuple
from functools import reduce
from itertools import chain
import graphviz  # type: ignore
import inspect

# Calm down, pylint: disable=too-few-public-methods
# NO, pylint: disable=use-dict-literal

# Next ID to assign to a created element
ELEMENT_ID_NEXT = 1

# A dictionary of created element object IDs and their sequential IDs
ELEMENT_ID_MAP = {}


def _print_stack_indented(*args, **kwargs):
    indent = '    ' * (len(inspect.stack()) - 1)
    print(indent[:-1], *args, **kwargs)

class Element:
    """A graph's element (node/edge)"""

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
        # Oh, really, pylint: disable=global-statement
        global ELEMENT_ID_NEXT
        # Avoid actual reference to the element
        ELEMENT_ID_MAP[id(self)] = ELEMENT_ID_NEXT
        ELEMENT_ID_NEXT += 1

    def __hash__(self):
        return id(self)

    def __repr__(self):
        repr_str = str(ELEMENT_ID_MAP[id(self)])
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


class Edge(Element):
    """A graph's edge"""

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

    def __repr__(self):
        return (
            repr(self.source) +
            " --" + super().__repr__() + "-> " +
            repr(self.target)
        )


class Graph:
    """A graph"""

    def __init__(self, *elements: Tuple[Union[Node, Edge]],
                 nodes: Optional[Set[Node]] = None,
                 edges: Optional[Set[Edge]] = None):
        """
        Initialize a graph.

        Args:
            elements:   A tuple of graph elements (nodes or edges).
            nodes:      A set of nodes to add to the elements,
                        or None for empty set.
            edges:      A set of edges to add to the elements,
                        or None for empty set.
        """
        assert isinstance(elements, tuple)
        assert all(isinstance(element, (Node, Edge)) for element in elements)
        assert nodes is None or isinstance(nodes, set) and all(
            isinstance(node, Node) for node in nodes
        )
        assert edges is None or isinstance(edges, set) and all(
            isinstance(edge, Edge) for edge in edges
        )
        self.nodes: Set[Node] = (nodes or set()).copy()
        self.edges: Set[Edge] = (edges or set()).copy()
        self.add(*elements)

    def __hash__(self):
        return hash((frozenset(self.nodes), frozenset(self.edges)))

    def __eq__(self, other):
        if not isinstance(other, Graph):
            return NotImplemented
        return self.nodes == other.nodes and self.edges == other.edges

    def __repr__(self):
        connected_nodes = {e.source for e in self.edges} | \
            {e.target for e in self.edges}
        return "{" + ", ".join(
            [repr(e) for e in self.edges] +
            [repr(n) for n in (self.nodes - connected_nodes)]
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

    def add(self, *elements: Tuple[Union[Node, Edge]]):
        """
        Add elements to the graph.

        Args:
            elements:   A tuple of graph elements (nodes or edges).

        Returns:
            The modified graph (self).
        """
        assert all(isinstance(element, (Node, Edge)) for element in elements)
        for element in elements:
            if isinstance(element, Node):
                self.nodes.add(element)
            elif isinstance(element, Edge):
                self.edges.add(element)
                self.nodes.add(element.source)
                self.nodes.add(element.target)
        return self

    def graphviz(self) -> str:
        """
        Render the graph into a Graphviz representation.

        Returns:
            The rendered Graphviz source code.
        """
        def trim(v: Union[str, int]):
            """Trim a value to a certain maximum length, if necessary"""
            return v[:61] + "..." if isinstance(v, str) and len(v) > 64 else v

        def quote(v: Union[str, int]):
            """Quote a value, if necessary"""
            return str(v) if isinstance(v, int) or v.isidentifier() else repr(v)

        def format_label(element: Element):
            """Format a label for a graphviz element"""
            return "\n".join(
                [str(ELEMENT_ID_MAP[id(element)])] +
                [f"{quote(n)}={quote(trim(v))}"
                 for n, v in element.attrs.items()]
            )

        graph = graphviz.Digraph()
        for node in self.nodes:
            graph.node(
                str(id(node)),
                label=format_label(node),
                _attributes=dict(shape="box")
            )
        for edge in self.edges:
            graph.edge(
                str(id(edge.source)), str(id(edge.target)),
                label=format_label(edge)
            )
        return graph.source

    def get_incident_edges(self, node: Node) -> Set[Edge]:
        """
        Get edges incident to a node (both incoming and outgoing).
        The node is assumed to belong to the graph.

        Args:
            node:   The node to get the edges for.

        Returns:
            A set containing edges incident to the node.
        """
        assert node in self.nodes
        return set(filter(lambda e: node in (e.source, e.target), self.edges))

    def detailed_match(self, other: "Graph") -> \
            Generator[Dict[Element, Element], None, None]:
        """
        Find all matches of this graph, as a pattern, against another graph.

        Args:
            other:  The graph to match this graph against.

        Yields:
            A dictionary of each element from this graph, used as a pattern,
            and the matched element of the other graph, whenever this graph
            matches completely.
        """
        def match_components(matches: Dict[Element, Element],
                             self_node: Node, other_node: Node) -> \
                Generator[Dict[Element, Element], None, None]:
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

            #_print_stack_indented(f"match_components"
            #                      f"{(matches, self_node, other_node)}")

            rem_self_edges = self.get_incident_edges(self_node) - self_matches

            # If there are no edges left to match
            if not rem_self_edges:
                #_print_stack_indented(f"<- {matches}")
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

        def match_subgraphs(matches: Dict[Element, Element]) -> \
                Generator[Dict[Element, Element], None, None]:
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

            #_print_stack_indented(f"match_subgraphs({matches})")
            if self_matches == (self.nodes | self.edges):
                #_print_stack_indented(f"<- {matches}")
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

        #_print_stack_indented(f"detailed_match{(self, other)}")
        # TODO: Something smarter than this
        unique_matches = set()
        for matches in match_subgraphs({}):
            unique_matches.add(frozenset(matches.items()))
        for matches in unique_matches:
            matches = dict(matches)
            #_print_stack_indented(f"<- {matches}")
            yield matches

    def match(self, other: "Graph") -> Generator["Graph", None, None]:
        """
        Find all matches of this graph as a pattern against another graph.

        Args:
            other:  The graph to match this graph against.

        Yields:
            Subgraphs of the other graph that match this graph.
        """
        #_print_stack_indented(f"match{(self, other)}")
        for matches in self.detailed_match(other):
            g = Graph(*matches.values())
            #_print_stack_indented(f"<- {g}")
            yield g
