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

def _test_basics(g, e, r):
    """Test the basics"""
    # Connect an entity as the default "source" role of a typed relation
    g = knob.Graph()
    e = g.entities
    r = g.relations
    from pprint import pprint
    e.ll_state("Standby") > r.ll_state_transition()
    print(g.render_graphviz())
    assert False
    r.ll_state_transition() < e.ll_state("Standby")
    # Connect an entity as the default "target" role of a typed relation
    r.ll_state_transition() > e.ll_state("Scanning")
    e.ll_state("Scanning") < r.ll_state_transition()
    # Connect two entities as the default "source" and "target" roles of a
    # typed relation
    e.ll_state("Standby") > r.ll_state_transition() > e.ll_state("Scanning")
    e.ll_state("Scanning") < r.ll_state_transition() < e.ll_state("Standby")

    # Connect two entities with the default "" relationship
    e.basic("A") > e.basic("B")

    # Connect three entities with the default "" relationship
    e.basic("C") > e.basic("D") > e.basic("E")

    # Connect an entity in the specified role to a relationship
    e.ll_state("Standby") > \
        r.ll_state_transition(trigger=e.ll_packet("Advertisement")) > \
        e.ll_state("Connection")

    assert True
