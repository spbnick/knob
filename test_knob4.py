"""Knob4 tests."""
import pytest
from knob4 import Node as N
from knob4 import Edge as E
from knob4 import Graph as G
from knob4 import NodePattern as NP
from knob4 import MatchingNodePattern as MNP
from knob4 import EdgePattern as EP
from knob4 import GraphPattern as GP

# Ah, come on, pylint: disable=invalid-name, redefined-outer-name
# Boooring, pylint: disable=missing-function-docstring

def test_empty_both():
    assert G().match(GP()) == G()

def test_empty_graph_pattern():
    n1 = N(x=1)
    n2 = N(x=2)
    e = E(n1, n2)
    assert G({n1, n2}, {e}).match(GP()) == G()

def test_empty_graph():
    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    ep = EP(mnp1, mnp2)
    assert G().match(GP({mnp1, mnp2}, {ep})) is None

def test_one_node_match():
    n = N()
    mnp = MNP()
    assert G({n}).match(GP({mnp})) == G({n})
    n = N(x=1)
    mnp = MNP()
    assert G({n}).match(GP({mnp})) == G({n})
    n = N(x=1)
    mnp = MNP(x=1)
    assert G({n}).match(GP({mnp})) == G({n})
    n = N(x=1, y=2)
    mnp = MNP(x=1)
    assert G({n}).match(GP({mnp})) == G({n})

def test_one_node_mismatch():
    mnp = MNP(x=2)
    gp = GP({mnp})

    n = N(x=1)
    g = G({n})
    assert g.match(gp) is None

    n = N(y=2)
    g = G({n})
    assert g.match(gp) is None

def test_one_out_of_two_node_patterns_match():
    n1 = N(x=2)
    n2 = N(x=3)
    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    g = G({n1, n2})
    gp = GP({mnp1, mnp2})
    assert g.match(gp) is None

def test_two_node_match():
    n1 = N(x=1)
    n2 = N(x=2)
    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    assert G({n1, n2}).match(GP({mnp1, mnp2})) == G({n1, n2})

def test_one_edge_match():
    n1 = N(x=1)
    n2 = N(x=2)
    e = E(n1, n2)
    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    ep = EP(mnp1, mnp2)
    g = G({n1, n2}, {e})
    assert g.match(GP({mnp1, mnp2}, {ep})) == g

def test_one_edge_mismatch():
    n1 = N(x=1)
    n2 = N(x=2)
    e = E(n1, n2, "a")
    g = G({n1, n2}, {e})

    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    ep = EP(mnp1, mnp2, "b")
    gp = GP({mnp1, mnp2}, {ep})
    assert g.match(gp) is None

def test_one_out_of_two_edge_patterns_match():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    mnp3 = MNP(x=3)

    g = G({n1, n2, n3}, {E(n1, n2, "a"), E(n2, n3, "b")})
    gp = GP({mnp1, mnp2, mnp3}, {EP(mnp1, mnp2, "a"), EP(mnp2, mnp3, "a")})
    assert g.match(gp) is None

    g = G({n1, n2, n3}, {E(n1, n2), E(n2, n3)})
    gp = GP({mnp1, mnp2, mnp3}, {EP(mnp1, mnp2), EP(mnp3, mnp2)})
    assert g.match(gp) is None

def test_self_loop_match():
    n = N()
    e = E(n, n)
    g = G({n}, {e})
    mnp = MNP()
    ep = EP(mnp, mnp)
    gp = GP({mnp}, {ep})
    assert g.match(gp) == g

def test_disconnected_node_match():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    g = G({n1, n2, n3}, {E(n1, n2)})

    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    mnp3 = MNP(x=3)
    gp = GP({mnp1, mnp2, mnp3}, {EP(mnp1, mnp2)})

    assert g.match(gp) == g

def test_three_nodes_two_edges_match():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    g = G({n1, n2, n3}, {E(n1, n2), E(n2, n3)})

    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    mnp3 = MNP(x=3)
    gp = GP({mnp1, mnp2, mnp3}, {EP(mnp1, mnp2), EP(mnp2, mnp3)})

    assert g.match(gp) == g

def test_missing_edge_mismatch():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    g = G({n1, n2, n3}, {E(n1, n2), E(n2, n3)})

    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    mnp3 = MNP(x=3)
    gp = GP({mnp1, mnp2, mnp3},
            {EP(mnp1, mnp2), EP(mnp2, mnp3), EP(mnp3, mnp1)})
    assert g.match(gp) is None

def test_extra_edge_match():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    g = G({n1, n2, n3}, {E(n1, n2), E(n2, n3), E(n3, n1)})

    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    mnp3 = MNP(x=3)
    gp = GP({mnp1, mnp2, mnp3},
            {EP(mnp1, mnp2), EP(mnp2, mnp3)})
    assert g.match(gp) == G({n1, n2, n3}, {E(n1, n2), E(n2, n3)})

def test_some_nodes_match():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)

    assert G({n1, n2}).match(GP({mnp1})) == G({n1})
    assert G({n1, n2, n3}).match(GP({mnp1, mnp2})) == G({n1, n2})

def test_some_edges_match():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    mnp3 = MNP(x=3)

    assert G({n1, n2}, {E(n1, n2), E(n2, n1)}).match(
        GP({mnp1, mnp2}, {EP(mnp1, mnp2)})
    ) == G({n1, n2}, {E(n1, n2)})

    assert G({n1, n2, n3}, {E(n1, n2), E(n2, n3), E(n3, n1)}).match(
        GP({mnp1, mnp2, mnp3}, {EP(mnp1, mnp2), EP(mnp2, mnp3)})
    ) == G({n1, n2, n3}, {E(n1, n2), E(n2, n3)})
