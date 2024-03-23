"""
KNOB - Knowledge graph
"""

import graphviz  # type: ignore
from knob6 import directed
from knob6.knowledge import pattern  # noqa: F401

# NO, pylint: disable=use-dict-literal
# We like our "id", pylint: disable=redefined-builtin


class Graph(directed.Graph):
    """A (directed) knowledge graph"""

    @classmethod
    def graphviz_format_label(cls, id: str, element: directed.Elements,
                              marked: bool):
        """Format a label for a graphviz element"""
        attrs = element.attrs.copy()
        keys = []
        for k in ("_type", "_name"):
            if v := attrs.pop(k, ""):
                keys.append(cls.graphviz_quote(v))
        return "\\n".join(
            [("", "+")[marked] + ".".join(keys)] +
            [f"{cls.graphviz_quote(n)}={cls.graphviz_trim(v)!r}"
             for n, v in attrs.items()]
        )

    def graphviz(self) -> str:
        """
        Render the graph into a Graphviz representation.

        Returns:
            The rendered Graphviz source code.
        """
        # We'll try to manage, pylint: disable=too-many-locals

        # A map of relation nodes and sets of their outgoing edges
        relations_edges: dict[directed.Node, set[directed.Edge]] = {}
        for edge in self.get_edges():
            if edge.source not in relations_edges:
                relations_edges[edge.source] = set()
            relations_edges[edge.source].add(edge)
        # A set of entity nodes
        entities: set[directed.Node] = \
            set(self.get_nodes()) - set(relations_edges)

        # A set of explicit relation nodes
        explicit_relations: set[directed.Node] = set()
        # A set of explicit functions (edges)
        explicit_functions: set[directed.Edge] = set()
        # A map of simple relation nodes and (source, target) tuples
        implicit_relations_endpoints: dict[
            directed.Node, tuple[directed.Node, directed.Node]
        ] = {}
        for relation, edges in relations_edges.items():
            if len(edges) == 2:
                one, two = edges
                if set(one.attrs.items()) | set(two.attrs.items()) == \
                   {("_type", "source"), ("_type", "target")}:
                    implicit_relations_endpoints[relation] = \
                        (one.target, two.target) \
                        if one.attrs["_type"] == "source" \
                        else (two.target, one.target)
                    continue
            explicit_relations.add(relation)
            explicit_functions |= edges

        def enumerated_elements(elements):
            return enumerate(sorted(elements, key=lambda n: n.id))

        # Generate element graphviz IDs
        element_ids = {
            # Entities (nodes)
            node: f"e{i + 1}"
            for i, node in enumerated_elements(entities)
        } | {
            # Explicit relations (nodes)
            node: f"r{i + 1}"
            for i, node in enumerated_elements(explicit_relations)
        } | {
            # Explicit functions (edges)
            edge: f"f{i + 1}"
            for i, edge in enumerated_elements(explicit_functions)
        } | {
            # Implicit relations (pseudo edges)
            node: f"ir{i + 1}"
            for i, node in enumerated_elements(implicit_relations_endpoints)
        }

        graph = graphviz.Digraph()

        for element, id in element_ids.items():
            label = self.graphviz_format_label(
                id, element, element in self.marked
            )
            # Add entity nodes
            if element in entities:
                graph.node(id, label=label, shape="box", style="rounded")
            # Add explicit relation nodes
            elif element in explicit_relations:
                graph.node(id, label=label, shape="diamond", style="rounded")
            # Add explicit function edges
            elif element in explicit_functions:
                if element.attrs.get("_type") == "source":
                    graph.edge(
                        element_ids[element.target], element_ids[element.source],
                        penwidth="2", arrowsize="2", arrowhead="onormal"
                    )
                elif element.attrs.get("_type") == "target":
                    graph.edge(
                        element_ids[element.source], element_ids[element.target],
                        penwidth="2", arrowsize="2", arrowhead="onormal"
                    )
                else:
                    graph.edge(
                        element_ids[element.source], element_ids[element.target],
                        label=label
                    )
            # Add implicit relations
            elif endpoints := implicit_relations_endpoints.get(element):
                graph.edge(
                    element_ids[endpoints[0]], element_ids[endpoints[1]],
                    label=label, penwidth="2", arrowsize="2"
                )

        return graph.source
