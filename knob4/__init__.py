"""
KNOB - Knowledge builder - a module for creating knowledge (hyper)graphs.
"""

from typing import Dict, Set, Union, Optional
from functools import reduce
from itertools import product

# Calm down, pylint: disable=too-few-public-methods


class Node:
    """A graph node"""

    def __init__(self, **attrs: Dict[str, Union[str, int]]):
        """
        Initialize a node.

        Args:
            attrs:  A dictionary of the node's attribute names and values.
        """
        assert isinstance(attrs, dict)
        assert all(
            isinstance(k, str) and isinstance(v, (str, int))
            for k, v in attrs.items()
        )
        self.attrs = attrs.copy()

    def __repr__(self):
        return "(" + ", ".join(
            (k if k.isidentifier() else repr(k)) + "=" + repr(v)
            for k, v in self.attrs.items()
        ) + ")"


class Edge:
    """A graph edge"""

    def __init__(self, source: Node, target: Node, name: str = ""):
        """
        Initialize a graph edge.

        Args:
            source: The edge's source node.
            target: The edge's target node.
            name:   The name of the edge.
        """
        assert isinstance(source, Node)
        assert isinstance(target, Node)
        assert isinstance(name, str)
        self.source = source
        self.target = target
        self.name = name

    def __repr__(self):
        if self.name == "":
            arrow = "->"
        else:
            arrow = "-" + (
                self.name if self.name.isidentifier()
                else repr(self.name)
            ) + "->"
        return repr(self.source) + arrow + repr(self.target)

    def __hash__(self):
        return hash((self.name, self.source, self.target))

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return NotImplemented
        return self.name == other.name and \
            self.source == other.source and \
            self.target == other.target


class NodePattern:
    """A graph node pattern"""

    def __init__(self, create: bool, **attrs: Dict[str, Union[str, int]]):
        """
        Initialize a graph node pattern.

        Args:
            create: False, if the node should be matched. True, if created.
            attrs:  A dictionary of the node's attribute names and values
                    to be matched/created.
        """
        assert isinstance(create, bool)
        assert isinstance(attrs, dict)
        assert all(
            isinstance(n, str) and isinstance(v, (str, int))
            for n, v in attrs.items()
        )
        self.attrs = attrs.copy()
        self.create = create

    def __repr__(self):
        return ("", "+")[self.create] + "(" + ", ".join(
            (k if k.isidentifier() else repr(k)) + "=" + repr(v)
            for k, v in self.attrs.items()
        ) + ")"

    def matches(self, node: Node):
        """
        Check if the pattern matches a node.

        Args:
            node:    The node to match the pattern against.

        Returns:
            True, if the pattern matches the node. False, if not.
        """
        return set(self.attrs.items()) <= set(node.attrs.items())


class MatchingNodePattern(NodePattern):
    """A matching graph node pattern"""

    def __init__(self, **attrs: Dict[str, Union[str, int]]):
        """
        Initialize a matching graph node pattern.

        Args:
            attrs:  A dictionary of the node's attribute names and values
                    to be matched/created.
        """
        assert isinstance(attrs, dict)
        assert all(
            isinstance(n, str) and isinstance(v, (str, int))
            for n, v in attrs.items()
        )
        super().__init__(False, **attrs)


class CreatingNodePattern(NodePattern):
    """A creating graph node pattern"""

    def __init__(self, **attrs: Dict[str, Union[str, int]]):
        """
        Initialize a creating graph node pattern.

        Args:
            attrs:  A dictionary of the node's attribute names and values
                    to be matched/created.
        """
        assert isinstance(attrs, dict)
        assert all(
            isinstance(n, str) and isinstance(v, (str, int))
            for n, v in attrs.items()
        )
        super().__init__(True, **attrs)


class EdgePattern:
    """A graph's edge pattern"""

    def __init__(self, source: NodePattern, target: NodePattern,
                 name: str = None):
        """
        Initialize a graph's edge pattern.

        Args:
            source: The edge's source node pattern.
            target: The edge's target node pattern.
            name:   The name of the edge, or None to match any name.
        """
        assert isinstance(source, NodePattern)
        assert isinstance(target, NodePattern)
        assert name is None or isinstance(name, str)
        self.source = source
        self.target = target
        self.name = name

    def __repr__(self):
        if self.name is None:
            arrow = "=>"
        elif self.name == "":
            arrow = "->"
        else:
            arrow = "-" + (
                self.name if self.name.isidentifier()
                else repr(self.name)
            ) + "->"
        return repr(self.source) + arrow + repr(self.target)

    def __hash__(self):
        return hash((self.name, self.source, self.target))

    def __eq__(self, other):
        if not isinstance(other, EdgePattern):
            return NotImplemented
        return self.name == other.name and \
            self.source == other.source and \
            self.target == other.target

    def matches(self, edge: Edge):
        """
        Check if the pattern matches an edge.

        Args:
            edge:    The edge to match the pattern against.

        Returns:
            True, if the pattern matches the edge. False, if not.
        """
        return (self.name is None or self.name == edge.name) and \
            self.source.matches(edge.source) and \
            self.target.matches(edge.target)


class GraphPattern:
    """A pattern matching/creating a subgraph"""

    def __init__(self,
                 node_patterns: Optional[Set[NodePattern]] = None,
                 edge_patterns: Optional[Set[EdgePattern]] = None):
        """
        Initialize a graph pattern.

        Args:
            node_patterns:  A set of patterns for nodes to match/create.
                            Can be None to mean empty set.
            edge_patterns:  A set of patterns for edges to match/create.
                            Must reference node patterns from "node_patterns"
                            only. Can be None to mean empty set.
        """
        if node_patterns is None:
            node_patterns = set()
        assert isinstance(node_patterns, set)
        assert all(isinstance(np, NodePattern) for np in node_patterns)

        if edge_patterns is None:
            edge_patterns = set()
        assert isinstance(edge_patterns, set)
        assert all(isinstance(ep, EdgePattern) for ep in edge_patterns)

        assert node_patterns >= {
            node_pattern
            for edge_pattern in edge_patterns
            for node_pattern in (edge_pattern.source, edge_pattern.target)
        }

        self.node_patterns = node_patterns.copy()
        self.edge_patterns = edge_patterns.copy()
        self.sources_edge_patterns = {
            node_pattern: {
                edge_pattern
                for edge_pattern in self.edge_patterns
                if node_pattern is edge_pattern.source
            }
            for node_pattern in self.node_patterns
        }

    def __repr__(self):
        connected_node_patterns = {ep.source for ep in self.edge_patterns} | \
            {ep.target for ep in self.edge_patterns}
        return "{" + ", ".join(
            [repr(ep) for ep in self.edge_patterns] +
            [repr(np)
             for np in (self.node_patterns - connected_node_patterns)]
        ) + "}"


class Graph:
    """A graph"""

    def __init__(self,
                 nodes: Optional[Set[Node]] = None,
                 edges: Optional[Set[Edge]] = None):
        """
        Initialize a graph.

        Args:
            nodes:  A set of nodes belonging to the graph.
                    Can be None to mean empty set.
            edges:  A set of edges connecting the nodes.
                    Must reference nodes from "nodes" only.
                    Can be None to mean empty set.
        """
        if nodes is None:
            nodes = set()
        assert isinstance(nodes, set)
        assert all(isinstance(n, Node) for n in nodes)

        if edges is None:
            edges = set()
        assert isinstance(edges, set)
        assert all(isinstance(e, Edge) for e in edges)

        assert nodes >= {
            node
            for edge in edges
            for node in (edge.source, edge.target)
        }

        self.nodes = nodes.copy()
        self.edges = edges.copy()

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

    def match(self, pattern: GraphPattern) -> Optional["Graph"]:
        """
        Return the subgraph matching the matching part of a graph pattern.

        Args:
            pattern:    The graph pattern to apply.

        Returns:
            A graph containing the matched nodes and edges.
        """
        # A dictionary of matching (not "create") node patterns and
        # sets of nodes they match
        node_patterns_nodes = {
            node_pattern: set(
                filter(node_pattern.matches, self.nodes)
            )
            for node_pattern in pattern.node_patterns
            if not node_pattern.create
        }

        # A dictionary of matching (not "create") edge patterns and
        # sets of edges they match
        edge_patterns_edges = {
            edge_pattern: {
                edge
                for edge in self.edges
                if edge.source in node_patterns_nodes[edge_pattern.source] and
                edge.target in node_patterns_nodes[edge_pattern.target] and
                (edge_pattern.name is None or edge_pattern.name == edge.name)
            }
            for edge_pattern in pattern.edge_patterns
            if edge_pattern.source in node_patterns_nodes and
            edge_pattern.target in node_patterns_nodes
        }

        while True:
            prev_node_patterns_nodes = {
                node_pattern: nodes.copy()
                for node_pattern, nodes in node_patterns_nodes.items()
            }
            prev_edge_patterns_edges = {
                edge_pattern: edges.copy()
                for edge_pattern, edges in edge_patterns_edges.items()
            }

            # Remove nodes not matched by all edge patterns
            for node_pattern, nodes in node_patterns_nodes.items():
                for edge_pattern, edges in edge_patterns_edges.items():
                    # Remove nodes missing from sources
                    if edge_pattern.source is node_pattern:
                        nodes &= {edge.source for edge in edges}
                    # Remove nodes missing from targets
                    if edge_pattern.target is node_pattern:
                        nodes &= {edge.target for edge in edges}

            # Remove edges referencing removed nodes
            for edge_pattern, edges in edge_patterns_edges.items():
                edge_patterns_edges[edge_pattern] = {
                    edge
                    for edge in edges
                    if edge.source in node_patterns_nodes[edge_pattern.source]
                    and
                    edge.target in node_patterns_nodes[edge_pattern.target]
                }

            # If nothing was removed
            if edge_patterns_edges == prev_edge_patterns_edges and \
                    node_patterns_nodes == prev_node_patterns_nodes:
                break

        # If any patterns matched nothing
        if not all(node_patterns_nodes.values()) or \
           not all(edge_patterns_edges.values()):
            return None

        # mypy has problems with reduce():
        # https://github.com/python/mypy/issues/4673
        return Graph(
            reduce(lambda x, y: x | y,  # type: ignore
                   node_patterns_nodes.values(), set()),
            reduce(lambda x, y: x | y,  # type: ignore
                   edge_patterns_edges.values(), set())
        )

    def apply(self, pattern: GraphPattern) -> Union["Graph", None]:
        """
        Apply a graph pattern to the graph, creating the nodes and the
        edges requested by the pattern, if any.

        Args:
            pattern:    The graph pattern to apply.

        Returns:
            A graph containing nodes and edges added to the graph (can be
            empty), if the pattern applied, or None, if it didn't.
        """
        return None
