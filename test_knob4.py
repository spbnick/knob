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
    assert G(E(N(x=1), N(x=2))).match(GP()) == G()

def test_empty_graph():
    assert G().match(GP(EP(MNP(x=1), MNP(x=2)))) is None

def test_one_node_match():
    g = G(N())
    assert g.match(GP(MNP())) == g
    g = G(N(x=1))
    assert g.match(GP(MNP())) == g
    g = G(N(x=1))
    assert g.match(GP(MNP(x=1))) == g
    g = G(N(x=1, y=2))
    assert g.match(GP(MNP(x=1))) == g

def test_one_node_mismatch():
    gp = GP(MNP(x=2))
    assert G(N(x=1)).match(gp) is None
    assert G(N(y=2)).match(gp) is None

def test_one_out_of_two_node_patterns_match():
    g = G(N(x=2), N(x=3))
    gp = GP(MNP(x=1), MNP(x=2))
    assert g.match(gp) is None

def test_two_node_match():
    g = G(N(x=1), N(x=2))
    gp = GP(MNP(x=1), MNP(x=2))
    assert g.match(gp) == g

def test_one_edge_match():
    g = G(E(N(x=1), N(x=2)))
    gp = GP(EP(MNP(x=1), MNP(x=2)))
    assert g.match(gp) == g

def test_one_edge_mismatch():
    g = G(E(N(x=1), N(x=2), "a"))
    gp = GP(EP(MNP(x=1), MNP(x=2), "b"))
    assert g.match(gp) is None

def test_one_out_of_two_edge_patterns_match():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    mnp3 = MNP(x=3)

    g = G(E(n1, n2, "a"), E(n2, n3, "b"))
    gp = GP(EP(mnp1, mnp2, "a"), EP(mnp2, mnp3, "a"))
    assert g.match(gp) is None

    g = G(E(n1, n2), E(n2, n3))
    gp = GP(EP(mnp1, mnp2), EP(mnp3, mnp2))
    assert g.match(gp) is None

def test_self_loop_match():
    n = N()
    g = G(E(n, n))
    mnp = MNP()
    gp = GP(EP(mnp, mnp))
    assert g.match(gp) == g

def test_disconnected_node_match():
    g = G(E(N(x=1), N(x=2)), N(x=3))
    gp = GP(EP(MNP(x=1), MNP(x=2)), MNP(x=3))
    assert g.match(gp) == g

def test_three_nodes_two_edges_match():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    g = G(E(n1, n2), E(n2, n3))

    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    mnp3 = MNP(x=3)
    gp = GP(EP(mnp1, mnp2), EP(mnp2, mnp3))

    assert g.match(gp) == g

def test_missing_edge_mismatch():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    g = G(E(n1, n2), E(n2, n3))

    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    mnp3 = MNP(x=3)
    gp = GP(EP(mnp1, mnp2), EP(mnp2, mnp3), EP(mnp3, mnp1))
    assert g.match(gp) is None

def test_extra_edge_match():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    g = G(E(n1, n2), E(n2, n3), E(n3, n1))

    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    mnp3 = MNP(x=3)
    gp = GP(EP(mnp1, mnp2), EP(mnp2, mnp3))
    assert g.match(gp) == G(E(n1, n2), E(n2, n3))

def test_some_nodes_match():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)

    assert G(n1, n2).match(GP(mnp1)) == G(n1)
    assert G(n1, n2, n3).match(GP(mnp1, mnp2)) == G(n1, n2)

def test_some_edges_match():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    mnp3 = MNP(x=3)

    assert G(E(n1, n2), E(n2, n1)).match(
        GP(EP(mnp1, mnp2))
    ) == G(E(n1, n2))

    assert G(E(n1, n2), E(n2, n3), E(n3, n1)).match(
        GP(EP(mnp1, mnp2), EP(mnp2, mnp3))
    ) == G(E(n1, n2), E(n2, n3))

def test_combination_match():
    n = [[N(r=r, c=c) for c in range(0, 3)] for r in range(0, 2)]
    g = G(*(
        E(n[sr][sc], n[tr][sc + 1])
        for sc in range(0, 2)
        for sr in range(0, 2)
        for tr in range(0, 2)
    ))

    assert g.match(GP(EP(MNP(), MNP()))) == g

    mnp_c0 = MNP(c=0)
    mnp_c1_1 = MNP(c=1)
    mnp_c1_2 = MNP(c=1)
    mnp_c2 = MNP(c=2)

    gp = GP(EP(mnp_c0, mnp_c1_1), EP(mnp_c1_1, mnp_c2))
    assert g.match(gp) == g

    gp = GP(EP(mnp_c0, mnp_c1_1), EP(mnp_c0, mnp_c1_2),
            EP(mnp_c1_1, mnp_c2), EP(mnp_c1_2, mnp_c2))
    assert g.match(gp) == g

    assert g.match(GP(EP(MNP(r=0), MNP(r=1)))) == G(
        E(n[0][0], n[1][1]),
        E(n[0][1], n[1][2])
    )

    assert g.match(GP(EP(MNP(r=1), MNP(r=0)))) == G(
        E(n[1][0], n[0][1]),
        E(n[1][1], n[0][2])
    )

    assert g.match(GP(EP(MNP(r=0), MNP(r=0)))) == G(
        E(n[0][0], n[0][1]),
        E(n[0][1], n[0][2]),
    )

    assert g.match(GP(EP(MNP(r=1), MNP(r=1)))) == G(
        E(n[1][0], n[1][1]),
        E(n[1][1], n[1][2]),
    )

    assert g.match(GP(EP(MNP(c=0), MNP(c=1)))) == G(
        E(n[0][0], n[0][1]),
        E(n[0][0], n[1][1]),
        E(n[1][0], n[0][1]),
        E(n[1][0], n[1][1]),
    )

    assert g.match(GP(EP(MNP(c=1), MNP(c=0)))) is None
    assert g.match(GP(EP(MNP(c=2), MNP(c=1)))) is None
    assert g.match(GP(EP(MNP(c=2), MNP(c=0)))) is None
    assert g.match(GP(EP(MNP(c=0), MNP(c=2)))) is None
