"""
KNOB - Knowledge builder - a module for creating knowledge (hyper)graphs.
"""

from typing import Dict, Set, Union, Optional, Tuple
from functools import reduce
from copy import copy
import graphviz  # type: ignore

# Calm down, pylint: disable=too-few-public-methods
# NO, pylint: disable=use-dict-literal

# Next ID to assign to a created element
ELEMENT_ID_NEXT = 1

# A dictionary of created element object IDs and their sequential IDs
ELEMENT_ID_MAP = {}


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
        global ELEMENT_ID_NEXT
        global ELEMENT_ID_MAP
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
            global ELEMENT_ID_MAP
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

    def detailed_match(self, other: "Graph") -> Tuple[
        Optional[Dict[Node, Set[Node]]],
        Optional[Dict[Edge, Set[Edge]]]
    ]:
        """
        Find all matches of this graph as a pattern against another graph.

        Return a dictionary of nodes and a dictionary of edges from this graph
        and sets of matching nodes/edges respectively, from the other graph.

        Return None, None if no matches were found.

        Args:
            other:  The graph to match this graph against.

        Returns:
            None, None if no matches were found,
            or two dictionaries containing:
            * nodes from this vs. sets of matching nodes from the other graph;
            * edges from this vs. sets of matching edges from the other graph.
        """



    def match(self, other: "Graph") -> Optional["Graph"]:
        """
        Find all matches of this graph as a pattern against another graph.

        Args:
            other:  The graph to match this graph against.

        Returns:
            A graph containing nodes and edges from all matches,
            or None, if no matches were found.
        """
        # TODO: Move to detailed_match()
        def match_components(matched_self, matched_other, self_node, other_node):
            """
            Find all subgraphs of a component of the other graph fully
            matching a component of this graph, used as a pattern.

            A component is defined as a node (assumed matching, and in
            corresonding matched_* graph), all nodes reachable from it, and
            all edges in between, minus whatever is already in the
            corresponding matched_* graph.

            Args:
                matched_self:   The graph containing matched elements of this
                                graph used as a pattern. Could be modified.
                matched_other:  The graph containing matched elements of the
                                other graph. Could be modified.
                self_node:      The node belonging to the pattern component of
                                this graph. Must match "other_node", and be in
                                "matched_self".
                other_node:     The node belonging to the component of the
                                other graph, to be matched. Must be matched by
                                "self_node", and be in "matched_other".

            Yields:
                A graph containing matching pattern elements from this graph
                ("matched_self"), and a graph containing matched elements from
                the other graph ("matched_other"), whenever a component match
                is complete.
            """
            assert self_node.matches(other_node)
            assert self_node in matched_self.nodes
            assert other_node in matched_other.nodes

            import inspect
            indent = '    ' * len(inspect.stack())
            print(f"{indent}match_components"
                  f"{(matched_self, matched_other, self_node, other_node)}")

            rem_self_edges = self.get_incident_edges(self_node) - \
                matched_self.get_incident_edges(self_node)

            # If there are no edges left to match
            if not rem_self_edges:
                print(f"{indent}<- {(matched_self, matched_other)}")
                yield matched_self, matched_other
                return

            rem_other_edges = other.get_incident_edges(other_node) - \
                matched_other.get_incident_edges(other_node)
            # For every combination of self and other edges
            for self_edge in rem_self_edges:
                for other_edge in rem_other_edges:
                    self_adj_node = self_edge.get_adjacent_node(self_node)
                    other_adj_node = other_edge.get_adjacent_node(other_node)
                    self_adj_matched = self_adj_node in matched_self.nodes
                    other_adj_matched = other_adj_node in matched_other.nodes
                    print(f"{indent}# "
                          f"{'-+'[self_adj_matched]}{self_adj_node} / "
                          f"{'-+'[other_adj_matched]}{other_adj_node}")
                    # If edge directions, attributes, or availability mismatch
                    if not (
                        self_edge.is_incoming(self_node) == \
                        other_edge.is_incoming(other_node) and \
                        self_edge.matches(other_edge) and \
                        self_adj_matched == other_adj_matched
                    ):
                        continue

                    # If the adjacent matched already
                    if self_adj_matched:
                        # Match remaining edges
                        yield from match_components(
                            copy(matched_self).add(self_edge),
                            copy(matched_other).add(other_edge),
                            self_node, other_node
                        )
                        continue

                    # If the adjacent doesn't match
                    if not self_adj_node.matches(other_adj_node):
                        continue

                    # For each adjacent subgraph match
                    for new_matched_self, new_matched_other in match_components(
                            # NOTE: Adding the edge adds connected nodes
                            copy(matched_self).add(self_edge),
                            copy(matched_other).add(other_edge),
                            self_adj_node, other_adj_node
                    ):
                        # Match remaining edges
                        yield from match_components(
                            new_matched_self, new_matched_other,
                            self_node, other_node
                        )

        # TODO: Move to detailed_match()
        def match_subgraphs(matched_self, matched_other):
            """
            Match this graph, used as a pattern, to subgraphs in the other.

            Args:
                matched_self:   The graph containing matched elements of this
                                graph used as a pattern. Could be modified.
                matched_other:  The graph containing matched elements of the
                                other graph. Could be modified.

            Yields:
                Subgraphs of the other graph which are completely matched by
                this graph being used as a pattern.
            """
            import inspect
            indent = '    ' * len(inspect.stack())
            print(f"{indent}match_subgraphs"
                  f"{(matched_self, matched_other)}")
            if matched_self == self:
                print(f"{indent}<- {(matched_other,)}")
                yield matched_other
                return
            rem_self_nodes = self.nodes - matched_self.nodes
            rem_other_nodes = other.nodes - matched_other.nodes
            for self_node in rem_self_nodes:
                for other_node in rem_other_nodes:
                    if not self_node.matches(other_node):
                        continue
                    # For each component match
                    for new_matched_self, new_matched_other in \
                            match_components(
                                copy(matched_self).add(self_node),
                                copy(matched_other).add(other_node),
                                self_node, other_node
                            ):
                        # Match the remaining components
                        yield from match_subgraphs(new_matched_self,
                                                   new_matched_other)

        # TODO: Rewrite to use detailed_match(), i.e.:
        # nodes, edges = self.detailed_match(other)
        # return Graph(nodes=nodes, edges=edges)
        return reduce(
            lambda x, y: (x or Graph()) | y,
            match_subgraphs(Graph(), Graph()),
            None
        )
