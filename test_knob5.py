"""Knob5 tests."""
import itertools
from knob5 import Node as N
from knob5 import Edge as E
from knob5 import Graph as G

# Ah, come on, pylint: disable=invalid-name, redefined-outer-name
# Boooring, pylint: disable=missing-function-docstring


def test_match_empty_both():
    assert G().match(G()) == G()


def test_match_empty_to_non_empty():
    assert G().match(G(E(N(x=1), N(x=2)))) == G()


def test_match_non_empty_to_empty():
    assert G(E(N(x=1), N(x=2))).match(G()) is None


def test_match_one_node():
    g = G(N())
    assert G(N()).match(g) == g
    assert G(N(y=2)).match(g) is None
    g = G(N(x=1))
    assert G(N()).match(g) == g
    assert G(N(x=1)).match(g) == g
    assert G(N(x=2)).match(g) is None
    assert G(N(y=2)).match(g) is None
    g = G(N(x=1, y=2))
    assert G(N()).match(g) == g
    assert G(N(x=1)).match(g) == g
    assert G(N(x=2)).match(g) is None
    assert G(N(y=2)).match(g) == g
    assert G(N(y=1)).match(g) is None
    assert G(N(x=1, y=2)).match(g) == g
    assert G(N(x=2, y=2)).match(g) is None
    assert G(N(x=1, y=1)).match(g) is None
    assert G(N(x=2, y=1)).match(g) is None


def test_match_two_nodes():
    n1_a = N(n=1)
    n1_b = N(n=1)
    n1 = n1_a
    n2 = N(n=2)
    assert G(N(n=1)).match(G(n1_a, n2)) == G(n1_a)
    assert G(N(n=1)).match(G(n1_b, n2)) == G(n1_b)
    assert G(N(n=1)).match(G(n1_a, n1_b)) == G(n1_a, n1_b)
    assert G(N()).match(G(n1_a, n1_b)) == G(n1_a, n1_b)
    assert G(N()).match(G(n1, n2)) == G(n1, n2)
    assert G(N(n=1), N(n=2)).match(G(n1, n2)) == G(n1, n2)
    assert G(N(n=1), N(n=3)).match(G(n1, n2)) is None
    assert G(N(n=3)).match(G(n1, n2)) is None


def test_match_one_edge():
    e = E(N(x=1), N(x=2))
    assert G(e).match(G(e)) == G(e)
    assert G(E(N(x=1), N(x=2))).match(G(e)) == G(e)
    assert G(E(N(), N(x=2))).match(G(e)) == G(e)
    assert G(E(N(x=1), N())).match(G(e)) == G(e)
    assert G(E(N(), N())).match(G(e)) == G(e)
    assert G(E(N(x=1), N(x=3))).match(G(e)) is None
    assert G(E(N(x=3), N(x=2))).match(G(e)) is None
    assert G(E(N(x=1), N(x=2), y=1)).match(G(e)) is None

    e = E(N(x=1), N(x=2), y=1)
    assert G(E(N(), N(), y=1)).match(G(e)) == G(e)
    assert G(E(N(), N())).match(G(e)) == G(e)
    assert G(E(N(x=1), N(x=2), y=1)).match(G(e)) == G(e)
    assert G(E(N(x=1), N(x=2))).match(G(e)) == G(e)
    assert G(E(N(x=1), N(x=2), y=2)).match(G(e)) is None
    assert G(E(N(), N(), y=2)).match(G(e)) is None
    assert G(E(N(x=1), N(x=2), z=3)).match(G(e)) is None


def test_match_self_loop():
    n1 = N()
    n2 = N()
    e11 = E(n1, n1)
    e22 = E(n2, n2)
    e12 = E(n1, n2)

    np1 = N()
    np2 = N()
    ep11 = E(np1, np1)
    ep22 = E(np2, np2)
    ep12 = E(np1, np2)
    assert G(ep11).match(G(e11)) == G(e11)
    assert G(ep11).match(G(e11, e22)) == G(e11, e22)
    assert G(ep11, ep22).match(G(e11, e22)) == G(e11, e22)
    print(G(ep11, ep22).match(G(e11, e22, e12)))
    assert G(ep11, ep22).match(G(e11, e22, e12)) == G(e11, e22)
    assert G(ep11, ep22).match(G(e11)) is None
    assert G(ep11, ep22).match(G(e22)) is None


def test_match_self_loop_specific():
    n1 = N()
    n2 = N()
    e11 = E(n1, n1)
    e22 = E(n2, n2)
    e12 = E(n1, n2)
    g = G(e11, e22, e12)

    np1 = N()
    np2 = N()
    ep11 = E(np1, np1)
    ep22 = E(np2, np2)
    ep12 = E(np1, np2)
    gp = G(ep11, ep22)
    print(g.graphviz())
    print(gp.graphviz())
    assert gp.match(g) == G(e11, e22)
