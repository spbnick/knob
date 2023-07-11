import pytest
import knob

@pytest.fixture
def g():
    return knob.Graph()

@pytest.fixture
def e(g):
    return g.entities

@pytest.fixture
def r(g):
    return g.relations

def test_entity_equality(e):
    """Check entity (in)equality conditions hold"""
    assert e.ll_state("") == e.ll_state("")
    assert e.ll_state("Advertising") == e.ll_state("Advertising")
    assert e.ll_state("Advertising") != e.ll_state("Scanning")

def test_graphviz_empty(g):
    """Check empty graph can be rendered into graphviz"""
    assert g.render_graphviz() == "digraph {\n}\n"

def test_graphviz_typeless_entity(g, e):
    """Check typeless entity can be rendered into graphviz"""
    e("Scanning")
    assert g.render_graphviz() == """\
digraph {
\tScanning [label=Scanning knob_domain=entity knob_type="" shape=box]
}
"""

def test_graphviz_typeless_entities(g, e):
    """Check multiple typeless entities can be rendered into graphviz"""
    e("Scanning")
    e("Advertising")
    assert g.render_graphviz() == """\
digraph {
\tScanning [label=Scanning knob_domain=entity knob_type="" shape=box]
\tAdvertising [label=Advertising knob_domain=entity knob_type="" shape=box]
}
"""

def test_graphviz_typeless_relation(g, e, r):
    """Check typeless relation rendering into graphviz"""
    e("A") > e("B")
    assert g.render_graphviz() == """\
digraph {
\tA [label=A knob_domain=entity knob_type="" shape=box]
\tB [label=B knob_domain=entity knob_type="" shape=box]
\tA -> B [label="" knob_domain=relation knob_type=""]
}
"""
