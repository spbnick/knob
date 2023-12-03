"""
KNOB - Knowledge builder - a module for creating knowledge (hyper)graphs.
"""

from typing import Dict, Set, Union, Optional, Tuple
from functools import reduce
import graphviz  # type: ignore

# Calm down, pylint: disable=too-few-public-methods
# NO, pylint: disable=use-dict-literal


class Node:
    """A graph node"""

    def __init__(self, **attrs: Union[str, int]):
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
        return str(id(self)) + "(" + ", ".join(
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

    def __init__(self, create: bool, **attrs: Union[str, int]):
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
        return ("", "+")[self.create] + str(id(self)) + "(" + ", ".join(
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

    def __init__(self, **attrs: Union[str, int]):
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

    def __init__(self, **attrs: Union[str, int]):
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
                 name: Optional[str] = None, create: bool = False):
        """
        Initialize a graph's edge pattern.

        Args:
            source: The edge's source node pattern.
            target: The edge's target node pattern.
            name:   The name of the edge, or None to match any name.
            create: If False, and both source and target have "create" False,
                    the edge should be matched. Otherwise, created.
        """
        assert isinstance(source, NodePattern)
        assert isinstance(target, NodePattern)
        assert name is None or isinstance(name, str)
        assert name is not None or not (source.create or target.create), \
            "Cannot create an edge without a name"
        assert isinstance(create, bool)
        self.source = source
        self.target = target
        self.name = name
        self.create = create or source.create or target.create

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
                 *element_patterns: Tuple[Union[NodePattern, EdgePattern]],
                 node_patterns: Optional[Set[NodePattern]] = None,
                 edge_patterns: Optional[Set[EdgePattern]] = None):
        """
        Initialize a graph pattern.

        Args:
            element_patterns:   A tuple of graph element patterns (node or
                                edge patterns).
            node_patterns:      A set of node patterns to add to the element
                                patterns, or None for empty set.
            edge_patterns:      A set of edge patterns to add to the element
                                patterns, or None for empty set.
        """
        assert isinstance(element_patterns, tuple)
        assert all(
            isinstance(element_pattern, (NodePattern, EdgePattern))
            for element_pattern in element_patterns
        )
        assert node_patterns is None or isinstance(node_patterns, set) and all(
            isinstance(node_pattern, NodePattern)
            for node_pattern in node_patterns
        )
        assert edge_patterns is None or isinstance(edge_patterns, set) and all(
            isinstance(edge_pattern, EdgePattern)
            for edge_pattern in edge_patterns
        )
        self.node_patterns: Set[NodePattern] = (node_patterns or set()).copy()
        self.edge_patterns: Set[EdgePattern] = (edge_patterns or set()).copy()
        for element_pattern in element_patterns:
            if isinstance(element_pattern, NodePattern):
                self.node_patterns.add(element_pattern)
            elif isinstance(element_pattern, EdgePattern):
                self.edge_patterns.add(element_pattern)
                self.node_patterns.add(element_pattern.source)
                self.node_patterns.add(element_pattern.target)

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
        for element in elements:
            if isinstance(element, Node):
                self.nodes.add(element)
            elif isinstance(element, Edge):
                self.edges.add(element)
                self.nodes.add(element.source)
                self.nodes.add(element.target)

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

    @classmethod
    def trim(cls, v: Union[str, int]):
        """Trim a value to a certain maximum length, if necessary"""
        return v[:61] + "..." if isinstance(v, str) and len(v) > 64 else v

    @classmethod
    def quote(cls, v: Union[str, int]):
        """Quote a value, if necessary"""
        return str(v) if isinstance(v, int) or v.isidentifier() else repr(v)

    def graphviz(self) -> str:
        """
        Render the graph into a Graphviz representation.

        Returns:
            The rendered Graphviz source code.
        """
        graph = graphviz.Digraph()
        for node in self.nodes:
            graph.node(
                str(id(node)),
                label="\n".join(
                    f"{self.quote(n)}={self.quote(self.trim(v))}"
                    for n, v in node.attrs.items()
                ),
                _attributes=dict(shape="box")
            )
        for edge in self.edges:
            graph.edge(
                str(id(edge.source)), str(id(edge.target)),
                label=edge.name
            )
        return graph.source

    def detailed_match(self, pattern: GraphPattern) -> Tuple[
        Optional["Graph"],
        Dict[NodePattern, Set[Node]],
        Dict[EdgePattern, Set[Edge]]
    ]:
        """
        Return the subgraph matching the matching part of a graph pattern,
        along with maps of node/edge patterns to their matching nodes/edges.

        Args:
            pattern:    The graph pattern to apply.

        Returns:
            Three values:
            * a graph containing the matched nodes and edges,
              or None, if not matched;
            * a dictionary of node patterns and sets of nodes they match;
            * a dictionary of edge patterns and sets of edges they match.
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
            if not edge_pattern.create
        }

        # While there are no nodes/edges to remove
        # Sorry, I don't really know what I'm doing here 🤦
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

        # If all patterns matched something
        if all(node_patterns_nodes.values()) and \
           all(edge_patterns_edges.values()):
            # mypy has problems with reduce():
            # https://github.com/python/mypy/issues/4673
            graph = Graph(
                nodes=reduce(lambda x, y: x | y,  # type: ignore
                             node_patterns_nodes.values(), set()),
                edges=reduce(lambda x, y: x | y,  # type: ignore
                             edge_patterns_edges.values(), set())
            )
        else:
            graph = None

        return graph, node_patterns_nodes, edge_patterns_edges

    def match(self, pattern: GraphPattern) -> Optional["Graph"]:
        """
        Return the subgraph matching the matching part of a graph pattern.

        Args:
            pattern:    The graph pattern to apply.

        Returns:
            A graph containing the matched nodes and edges, or None, if not
            matched.
        """
        return self.detailed_match(pattern)[0]

    def apply(self, pattern: GraphPattern) -> Union["Graph", None]:
        """
        Apply a graph pattern to the graph, returning a graph with nodes and
        edges created by the pattern.

        Args:
            pattern:    The graph pattern to apply.

        Returns:
            A graph containing nodes and edges to be added to the graph (can
            be empty), if the pattern matched, or None, if it didn't.
        """
        # A map of create flag, node patterns, and corresponding nodes
        create_node_patterns_nodes: \
            Dict[bool, Dict[NodePattern, Set[Node]]] = {False: {}, True: {}}
        # A map of create flag, edge patterns, and corresponding edges
        create_edge_patterns_edges: \
            Dict[bool, Dict[EdgePattern, Set[Edge]]] = {False: {}, True: {}}

        matched_graph, \
            create_node_patterns_nodes[False], \
            create_edge_patterns_edges[False] = \
            self.detailed_match(pattern)
        if matched_graph is None:
            return None

        # A map of create node patterns and a set of their created nodes
        create_node_patterns_nodes[True] = {
            node_pattern: {Node(**node_pattern.attrs)}
            for node_pattern in pattern.node_patterns
            if node_pattern.create
        }
        # A map of create edge patterns and a set of their created edges
        create_edge_patterns_edges[True] = {
            edge_pattern: {
                Edge(source, target, edge_pattern.name)
                for source in create_node_patterns_nodes
                [edge_pattern.source.create][edge_pattern.source]
                for target in create_node_patterns_nodes
                [edge_pattern.target.create][edge_pattern.target]
            }
            for edge_pattern in pattern.edge_patterns
            if edge_pattern.create and edge_pattern.name is not None
        }

        return Graph(
            # mypy has problems with reduce():
            # https://github.com/python/mypy/issues/4673
            nodes=reduce(lambda x, y: x | y,  # type: ignore
                         create_node_patterns_nodes[True].values(), set()),
            edges=reduce(lambda x, y: x | y,  # type: ignore
                         create_edge_patterns_edges[True].values(), set())
        )
