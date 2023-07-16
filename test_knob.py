import pytest
import knob

@pytest.fixture
def g():
    """A graph"""
    return knob.Graph()

@pytest.fixture
def e(g):
    """The graph's entity accessor"""
    return g.entities

@pytest.fixture
def n(e):
    """The graph's typeless entity (node) accessor"""
    return e[""]

@pytest.fixture
def r(g):
    """The graph's relation accessor"""
    return g.relations

@pytest.fixture
def a(r):
    """The graph's typeless relation (arc) accessor"""
    return r[""]

def test_entity_equality(e, n):
    """Check entity (in)equality conditions hold"""
    assert n[""] == n[""]
    assert n.Advertising == n.Advertising
    assert n.Advertising != n.Scanning
    assert e.ll_state[""] == e.ll_state[""]
    assert e.ll_state.Advertising == e.ll_state.Advertising
    assert e.ll_state.Advertising != e.ll_state.Scanning

def test_graphviz_empty(g):
    """Check empty graph can be rendered into graphviz"""
    assert g.render_graphviz() == "digraph {\n}\n"

def test_graphviz_node(g, n):
    """Check a node (typeless entity) can be rendered into graphviz"""
    n.Scanning
    assert g.render_graphviz() == """\
digraph {
\t"('', 'Scanning')" [label=Scanning knob_domain=entity knob_type="" shape=box]
}
"""

def test_graphviz_entity(g, e):
    """Check an entity can be rendered into graphviz"""
    e.ll_state.Scanning
    assert g.render_graphviz() == """\
digraph {
\t"('ll_state', 'Scanning')" \
[label="ll_state:\nScanning" knob_domain=entity knob_type=ll_state shape=box]
}
"""

def test_graphviz_nodes(g, n):
    """
    Check multiple nodes (typeless entities) can be rendered into graphviz
    """
    n.Scanning
    n.Advertising
    assert g.render_graphviz() == """\
digraph {
\t"('', 'Scanning')" [label=Scanning knob_domain=entity knob_type="" shape=box]
\t"('', 'Advertising')" [label=Advertising knob_domain=entity knob_type="" shape=box]
}
"""

def test_graphviz_entities(g, e):
    """Check an entity can be rendered into graphviz"""
    e.ll_state.Scanning
    e.ll_state.Advertising
    assert g.render_graphviz() == """\
digraph {
\t"('ll_state', 'Scanning')" \
[label="ll_state:\nScanning" \
knob_domain=entity knob_type=ll_state shape=box]
\t"('ll_state', 'Advertising')" \
[label="ll_state:\nAdvertising" \
knob_domain=entity knob_type=ll_state shape=box]
}
"""

def test_graphviz_arc(g, n):
    """Check arc (typeless relation) rendering into graphviz"""
    n.A >> n.B
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'A')" -> "('', 'B')" [label="" knob_domain=relation knob_type=""]
}
"""

def test_graphviz_arc_with_list(g, n):
    """Check rendering of arc connected to a list into graphviz"""
    n.A >> [n.B, n.C]
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'C')" [label=C knob_domain=entity knob_type="" shape=box]
\t"('', 'A')" -> "('', 'B')" [label="" knob_domain=relation knob_type=""]
\t"('', 'A')" -> "('', 'C')" [label="" knob_domain=relation knob_type=""]
}
"""

def test_graphviz_arc_with_tuple(g, n):
    """Check rendering of arc connected to a tuple into graphviz"""
    n.A >> (n.B, n.C)
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'C')" [label=C knob_domain=entity knob_type="" shape=box]
\t"('', 'A')" -> "('', 'B')" [label="" knob_domain=relation knob_type=""]
\t"('', 'A')" -> "('', 'C')" [label="" knob_domain=relation knob_type=""]
}
"""

def test_graphviz_arc_chain(g, n):
    """Check arc (typeless relation) chain rendering into graphviz"""
    n.A >> n.B >> n.C
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'C')" [label=C knob_domain=entity knob_type="" shape=box]
\t"('', 'A')" -> "('', 'B')" [label="" knob_domain=relation knob_type=""]
\t"('', 'B')" -> "('', 'C')" [label="" knob_domain=relation knob_type=""]
}
"""

def test_graphviz_arc_mixed_chain(g, n):
    """Check arc (typeless relation) mixed chain rendering into graphviz"""
    n.A >> n.B << n.C
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'C')" [label=C knob_domain=entity knob_type="" shape=box]
\t"('', 'A')" -> "('', 'B')" [label="" knob_domain=relation knob_type=""]
\t"('', 'C')" -> "('', 'B')" [label="" knob_domain=relation knob_type=""]
}
"""

def test_graphviz_binary_relation(g, n, r):
    """Check binary relation rendering into graphviz"""
    n.A >> r.X >> n.B
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'A')" -> "('', 'B')" [label=X knob_domain=relation knob_type=X]
}
"""

def test_graphviz_binary_relation_list(g, n, r):
    """Check binary relation list rendering into graphviz"""
    n.A >> [r.X, r.Y] >> n.B
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'A')" -> "('', 'B')" [label=X knob_domain=relation knob_type=X]
\t"('', 'A')" -> "('', 'B')" [label=Y knob_domain=relation knob_type=Y]
}
"""

def test_graphviz_binary_relation_tuple(g, n, r):
    """Check binary relation tuple rendering into graphviz"""
    n.A >> (r.X, r.Y) >> n.B
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'A')" -> "('', 'B')" [label=X knob_domain=relation knob_type=X]
\t"('', 'A')" -> "('', 'B')" [label=Y knob_domain=relation knob_type=Y]
}
"""

def test_graphviz_binary_relation_entity_list_source(g, n, r):
    """
    Check graphviz rendering of a binary relation having entity list as the
    source.
    """
    [n.A, n.B] >> r.X >> n.C
    assert g.render_graphviz() == """\
digraph {
	"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
	"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
	"('', 'C')" [label=C knob_domain=entity knob_type="" shape=box]
	"('', 'A')" -> "('', 'C')" [label=X knob_domain=relation knob_type=X]
	"('', 'B')" -> "('', 'C')" [label=X knob_domain=relation knob_type=X]
}
"""

def test_graphviz_binary_relation_entity_list_target(g, n, r):
    """
    Check graphviz rendering of a binary relation having entity list as the
    target.
    """
    n.A >> r.X >> [n.B, n.C]
    print(g.render_graphviz())
    assert g.render_graphviz() == """\
digraph {
	"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
	"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
	"('', 'C')" [label=C knob_domain=entity knob_type="" shape=box]
	"('', 'A')" -> "('', 'B')" [label=X knob_domain=relation knob_type=X]
	"('', 'A')" -> "('', 'C')" [label=X knob_domain=relation knob_type=X]
}
"""

def test_graphviz_binary_relation_entity_list_both(g, n, r):
    """
    Check graphviz rendering of a binary relation having entity list as both
    the source and the target.
    """
    [n.A, n.B] >> r.X >> [n.C, n.D]
    print(g.render_graphviz())
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'C')" [label=C knob_domain=entity knob_type="" shape=box]
\t"('', 'D')" [label=D knob_domain=entity knob_type="" shape=box]
\t"('', 'A')" -> "('', 'C')" [label=X knob_domain=relation knob_type=X]
\t"('', 'A')" -> "('', 'D')" [label=X knob_domain=relation knob_type=X]
\t"('', 'B')" -> "('', 'C')" [label=X knob_domain=relation knob_type=X]
\t"('', 'B')" -> "('', 'D')" [label=X knob_domain=relation knob_type=X]
}
"""

def test_graphviz_ternary_relation_entity_list_all(g, n, r):
    """
    Check graphviz rendering of a binary relation having entity list as both
    the source and the target.
    """
    [n.A, n.B] >> r.X(middle=[n.C, n.D]) >> [n.E, n.F]
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'C')" [label=C knob_domain=entity knob_type="" shape=box]
\t"('', 'D')" [label=D knob_domain=entity knob_type="" shape=box]
\t"('', 'E')" [label=E knob_domain=entity knob_type="" shape=box]
\t"('', 'F')" [label=F knob_domain=entity knob_type="" shape=box]
\t"(('middle', ('', 'C')), ('source', ('', 'A')), ('target', ('', 'E')))" \
[label=X knob_domain=relation knob_type=X shape=diamond]
\t"('', 'C')" -> \
"(('middle', ('', 'C')), ('source', ('', 'A')), ('target', ('', 'E')))" \
[label=middle knob_domain=role knob_type=middle style=dashed]
\t"('', 'A')" -> \
"(('middle', ('', 'C')), ('source', ('', 'A')), ('target', ('', 'E')))" \
[knob_domain=role knob_type=source]
\t"(('middle', ('', 'C')), ('source', ('', 'A')), ('target', ('', 'E')))" -> \
"('', 'E')" [knob_domain=role knob_type=target]
\t"(('middle', ('', 'C')), ('source', ('', 'A')), ('target', ('', 'F')))" \
[label=X knob_domain=relation knob_type=X shape=diamond]
\t"('', 'C')" -> \
"(('middle', ('', 'C')), ('source', ('', 'A')), ('target', ('', 'F')))" \
[label=middle knob_domain=role knob_type=middle style=dashed]
\t"('', 'A')" -> \
"(('middle', ('', 'C')), ('source', ('', 'A')), ('target', ('', 'F')))" \
[knob_domain=role knob_type=source]
\t"(('middle', ('', 'C')), ('source', ('', 'A')), ('target', ('', 'F')))" -> \
"('', 'F')" [knob_domain=role knob_type=target]
\t"(('middle', ('', 'C')), ('source', ('', 'B')), ('target', ('', 'E')))" \
[label=X knob_domain=relation knob_type=X shape=diamond]
\t"('', 'C')" -> \
"(('middle', ('', 'C')), ('source', ('', 'B')), ('target', ('', 'E')))" \
[label=middle knob_domain=role knob_type=middle style=dashed]
\t"('', 'B')" -> \
"(('middle', ('', 'C')), ('source', ('', 'B')), ('target', ('', 'E')))" \
[knob_domain=role knob_type=source]
\t"(('middle', ('', 'C')), ('source', ('', 'B')), ('target', ('', 'E')))" -> \
"('', 'E')" [knob_domain=role knob_type=target]
\t"(('middle', ('', 'C')), ('source', ('', 'B')), ('target', ('', 'F')))" \
[label=X knob_domain=relation knob_type=X shape=diamond]
\t"('', 'C')" -> \
"(('middle', ('', 'C')), ('source', ('', 'B')), ('target', ('', 'F')))" \
[label=middle knob_domain=role knob_type=middle style=dashed]
\t"('', 'B')" -> \
"(('middle', ('', 'C')), ('source', ('', 'B')), ('target', ('', 'F')))" \
[knob_domain=role knob_type=source]
\t"(('middle', ('', 'C')), ('source', ('', 'B')), ('target', ('', 'F')))" -> \
"('', 'F')" [knob_domain=role knob_type=target]
\t"(('middle', ('', 'D')), ('source', ('', 'A')), ('target', ('', 'E')))" \
[label=X knob_domain=relation knob_type=X shape=diamond]
\t"('', 'D')" -> \
"(('middle', ('', 'D')), ('source', ('', 'A')), ('target', ('', 'E')))" \
[label=middle knob_domain=role knob_type=middle style=dashed]
\t"('', 'A')" -> \
"(('middle', ('', 'D')), ('source', ('', 'A')), ('target', ('', 'E')))" \
[knob_domain=role knob_type=source]
\t"(('middle', ('', 'D')), ('source', ('', 'A')), ('target', ('', 'E')))" -> \
"('', 'E')" [knob_domain=role knob_type=target]
\t"(('middle', ('', 'D')), ('source', ('', 'A')), ('target', ('', 'F')))" \
[label=X knob_domain=relation knob_type=X shape=diamond]
\t"('', 'D')" -> \
"(('middle', ('', 'D')), ('source', ('', 'A')), ('target', ('', 'F')))" \
[label=middle knob_domain=role knob_type=middle style=dashed]
\t"('', 'A')" -> \
"(('middle', ('', 'D')), ('source', ('', 'A')), ('target', ('', 'F')))" \
[knob_domain=role knob_type=source]
\t"(('middle', ('', 'D')), ('source', ('', 'A')), ('target', ('', 'F')))" -> \
"('', 'F')" [knob_domain=role knob_type=target]
\t"(('middle', ('', 'D')), ('source', ('', 'B')), ('target', ('', 'E')))" \
[label=X knob_domain=relation knob_type=X shape=diamond]
\t"('', 'D')" -> \
"(('middle', ('', 'D')), ('source', ('', 'B')), ('target', ('', 'E')))" \
[label=middle knob_domain=role knob_type=middle style=dashed]
\t"('', 'B')" -> \
"(('middle', ('', 'D')), ('source', ('', 'B')), ('target', ('', 'E')))" \
[knob_domain=role knob_type=source]
\t"(('middle', ('', 'D')), ('source', ('', 'B')), ('target', ('', 'E')))" -> \
"('', 'E')" [knob_domain=role knob_type=target]
\t"(('middle', ('', 'D')), ('source', ('', 'B')), ('target', ('', 'F')))" \
[label=X knob_domain=relation knob_type=X shape=diamond]
\t"('', 'D')" -> \
"(('middle', ('', 'D')), ('source', ('', 'B')), ('target', ('', 'F')))" \
[label=middle knob_domain=role knob_type=middle style=dashed]
\t"('', 'B')" -> \
"(('middle', ('', 'D')), ('source', ('', 'B')), ('target', ('', 'F')))" \
[knob_domain=role knob_type=source]
\t"(('middle', ('', 'D')), ('source', ('', 'B')), ('target', ('', 'F')))" -> \
"('', 'F')" [knob_domain=role knob_type=target]
}
"""

def test_graphviz_binary_relation_conflict(g, n, r):
    """Check binary relation conflict rendering into graphviz"""
    n.A >> r.X << n.B
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"(('source', ('', 'A')),)" \
[label=X knob_domain=relation knob_type=X shape=diamond]
\t"('', 'A')" -> "(('source', ('', 'A')),)" \
[knob_domain=role knob_type=source]
\t"(('source', ('', 'B')),)" \
[label=X knob_domain=relation knob_type=X shape=diamond]
\t"('', 'B')" -> "(('source', ('', 'B')),)" \
[knob_domain=role knob_type=source]
}
"""

def test_graphviz_binary_relation_chain(g, n, r):
    """Check binary relation chain rendering into graphviz"""
    n.A >> r.X >> n.B >> r.Y >> n.C
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'C')" [label=C knob_domain=entity knob_type="" shape=box]
\t"('', 'A')" -> "('', 'B')" [label=X knob_domain=relation knob_type=X]
\t"('', 'B')" -> "('', 'C')" [label=Y knob_domain=relation knob_type=Y]
}
"""

def test_graphviz_binary_relation_mixed_chain(g, n, r):
    """Check binary relation mixed chain rendering into graphviz"""
    n.A >> r.X >> n.B << r.Y << n.C
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'C')" [label=C knob_domain=entity knob_type="" shape=box]
\t"('', 'A')" -> "('', 'B')" [label=X knob_domain=relation knob_type=X]
\t"('', 'C')" -> "('', 'B')" [label=Y knob_domain=relation knob_type=Y]
}
"""

def test_graphviz_arcs(g, n):
    """Check multiple arc (typeless relation) rendering into graphviz"""
    n.A >> n.B
    n.A << n.B
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'A')" -> "('', 'B')" [label="" knob_domain=relation knob_type=""]
\t"('', 'B')" -> "('', 'A')" [label="" knob_domain=relation knob_type=""]
}
"""

def test_graphviz_arc_chains(g, n):
    """Check multiple arc (typeless relation) rendering into graphviz"""
    n.A >> n.B >> n.C
    n.A << n.B << n.C
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'C')" [label=C knob_domain=entity knob_type="" shape=box]
\t"('', 'A')" -> "('', 'B')" [label="" knob_domain=relation knob_type=""]
\t"('', 'B')" -> "('', 'C')" [label="" knob_domain=relation knob_type=""]
\t"('', 'B')" -> "('', 'A')" [label="" knob_domain=relation knob_type=""]
\t"('', 'C')" -> "('', 'B')" [label="" knob_domain=relation knob_type=""]
}
"""

def test_graphviz_binary_relations(g, n, r):
    """Check multiple binary relation rendering into graphviz"""
    x = r.X
    n.A >> x >> n.B
    n.A << x << n.B
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'A')" -> "('', 'B')" [label=X knob_domain=relation knob_type=X]
\t"('', 'B')" -> "('', 'A')" [label=X knob_domain=relation knob_type=X]
}
"""

def test_graphviz_binary_relation_chains(g, n, r):
    """Check multiple binary relation chains rendering into graphviz"""
    x = r.X
    y = r.Y
    n.A >> x >> n.B >> y >> n.C
    n.A << x << n.B << y << n.C
    assert g.render_graphviz() == """\
digraph {
\t"('', 'A')" [label=A knob_domain=entity knob_type="" shape=box]
\t"('', 'B')" [label=B knob_domain=entity knob_type="" shape=box]
\t"('', 'C')" [label=C knob_domain=entity knob_type="" shape=box]
\t"('', 'A')" -> "('', 'B')" [label=X knob_domain=relation knob_type=X]
\t"('', 'B')" -> "('', 'A')" [label=X knob_domain=relation knob_type=X]
\t"('', 'B')" -> "('', 'C')" [label=Y knob_domain=relation knob_type=Y]
\t"('', 'C')" -> "('', 'B')" [label=Y knob_domain=relation knob_type=Y]
}
"""
