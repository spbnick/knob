"""Knob6 directed graph tests."""
import itertools
import functools
from copy import copy
from typing import Optional
from knob6.directed import Node as N, Edge as E, Graph, Elements

# Ah, come on, pylint: disable=invalid-name, redefined-outer-name
# Boooring, pylint: disable=missing-function-docstring
# We need them, pylint: disable=fixme


class G(Graph):
    """A directed graph allowing indirect element specification"""
    def __init__(self, *elements: Elements,
                 marked: Optional[set[Elements]] = None):
        empty_elements: set[Elements] = set()
        super().__init__(
            elements=functools.reduce(
                lambda a, b: a | b,
                (
                    {e} if isinstance(e, N)
                    else {e, e.source, e.target}  # type: ignore
                    for e in elements
                ),
                empty_elements
            ),
            marked=marked
        )


def test_match_empty_both():
    assert set(G().match(G())) == {G()}


def test_match_empty_to_non_empty():
    assert set(G().match(G(E(N(x=1), N(x=2))))) == {G()}


def test_match_non_empty_to_empty():
    assert set(G(E(N(x=1), N(x=2))).match(G())) == set()


def test_match_one_node():
    g = G(N())
    assert set(G(N()).match(g)) == {g}
    assert set(G(N(y=2)).match(g)) == set()
    g = G(N(x=1))
    assert set(G(N()).match(g)) == {g}
    assert set(G(N(x=1)).match(g)) == {g}
    assert set(G(N(x=2)).match(g)) == set()
    assert set(G(N(y=2)).match(g)) == set()
    g = G(N(x=1, y=2))
    assert set(G(N()).match(g)) == {g}
    assert set(G(N(x=1)).match(g)) == {g}
    assert set(G(N(x=2)).match(g)) == set()
    assert set(G(N(y=2)).match(g)) == {g}
    assert set(G(N(y=1)).match(g)) == set()
    assert set(G(N(x=1, y=2)).match(g)) == {g}
    assert set(G(N(x=2, y=2)).match(g)) == set()
    assert set(G(N(x=1, y=1)).match(g)) == set()
    assert set(G(N(x=2, y=1)).match(g)) == set()


def test_match_two_nodes():
    n1_a = N(n=1)
    n1_b = N(n=1)
    n1 = n1_a
    n2 = N(n=2)
    assert set(G(N(n=1)).match(G(n1_a, n2))) == {G(n1_a)}
    assert set(G(N(n=1)).match(G(n1_b, n2))) == {G(n1_b)}
    assert set(G(N(n=1)).match(G(n1_a, n1_b))) == {G(n1_a), G(n1_b)}
    assert set(G(N()).match(G(n1_a, n1_b))) == {G(n1_a), G(n1_b)}
    assert set(G(N()).match(G(n1, n2))) == {G(n1), G(n2)}
    assert set(G(N(n=1), N(n=2)).match(G(n1, n2))) == {G(n1, n2)}
    assert set(G(N(n=1), N(n=3)).match(G(n1, n2))) == set()
    assert set(G(N(n=3)).match(G(n1, n2))) == set()


def test_match_one_edge():
    e = E(N(x=1), N(x=2))
    assert set(G(e).match(G(e))) == {G(e)}
    assert set(G(E(N(x=1), N(x=2))).match(G(e))) == {G(e)}
    assert set(G(E(N(x=2), N(x=1))).match(G(e))) == set()
    assert set(G(E(N(), N(x=2))).match(G(e))) == {G(e)}
    assert set(G(E(N(x=2), N())).match(G(e))) == set()
    assert set(G(E(N(x=1), N())).match(G(e))) == {G(e)}
    assert set(G(E(N(), N(x=1))).match(G(e))) == set()
    assert set(G(E(N(), N())).match(G(e))) == {G(e)}
    assert set(G(E(N(x=1), N(x=3))).match(G(e))) == set()
    assert set(G(E(N(x=3), N(x=2))).match(G(e))) == set()
    assert set(G(E(N(x=1), N(x=2), y=1)).match(G(e))) == set()

    e = E(N(x=1), N(x=2), y=1)
    assert set(G(E(N(), N(), y=1)).match(G(e))) == {G(e)}
    assert set(G(E(N(), N())).match(G(e))) == {G(e)}
    assert set(G(E(N(x=1), N(x=2), y=1)).match(G(e))) == {G(e)}
    assert set(G(E(N(x=2), N(x=1), y=1)).match(G(e))) == set()
    assert set(G(E(N(x=1), N(x=2))).match(G(e))) == {G(e)}
    assert set(G(E(N(x=2), N(x=1))).match(G(e))) == set()
    assert set(G(E(N(x=1), N(x=2), y=2)).match(G(e))) == set()
    assert set(G(E(N(), N(), y=2)).match(G(e))) == set()
    assert set(G(E(N(x=1), N(x=2), z=3)).match(G(e))) == set()


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
    assert set(G(ep11).match(G(e11))) == {G(e11)}
    assert set(G(ep11).match(G(e11, e22))) == {G(e11), G(e22)}
    assert set(G(ep11, ep22).match(G(e11, e22))) == {G(e11, e22)}
    assert set(G(ep11, ep22).match(G(e11, e22, e12))) == {G(e11, e22)}
    assert set(G(ep12).match(G(e11, e22, e12))) == {G(e12)}
    assert set(G(ep12).match(G(e11, e22))) == set()
    assert set(G(ep11, ep22).match(G(e11))) == set()
    assert set(G(ep11, ep22).match(G(e22))) == set()


def test_match_loops():
    n = [N() for n in range(0, 4)]
    e = [[E(n1, n2) for n2 in n] for n1 in n]
    np = [N() for np in range(0, 4)]
    ep = [[E(np1, np2) for np2 in np] for np1 in np]

    assert set(G(ep[0][1], ep[1][2], ep[2][0]).match(
        G(e[0][1], e[1][2], e[2][0])
    )) == {G(e[0][1], e[1][2], e[2][0])}
    assert set(G(ep[0][1], ep[1][2], ep[2][0]).match(
        G(e[0][1], e[1][2], e[0][2])
    )) == set()
    assert set(G(ep[0][1], ep[1][2], ep[2][0]).match(
        G(e[0][1], e[1][2], e[2][0], e[2][3])
    )) == {G(e[0][1], e[1][2], e[2][0])}
    assert set(G(ep[0][1], ep[1][2], ep[2][0]).match(
        G(e[0][1], e[1][2], e[2][0], e[2][3], e[3][1])
    )) == {
        G(e[0][1], e[1][2], e[2][0]),
        G(e[1][2], e[2][3], e[3][1])
    }
    assert set(G(ep[0][1], ep[1][2], ep[2][0]).match(
        G(e[0][1], e[1][2], e[2][0], e[2][3], e[1][3])
    )) == {G(e[0][1], e[1][2], e[2][0])}
    assert set(G(ep[0][1], ep[1][2], ep[2][0]).match(
        G(e[0][1], e[1][2], e[0][2], e[2][3], e[1][3])
    )) == set()
    assert set(G(ep[0][1], ep[1][2], ep[2][3], ep[3][0]).match(
        G(e[0][1], e[1][2], e[2][3], e[3][0])
    )) == {G(e[0][1], e[1][2], e[2][3], e[3][0])}
    assert set(G(ep[0][1], ep[1][2], ep[2][3], ep[3][0]).match(
        G(e[1][0], e[2][1], e[3][2], e[0][3])
    )) == {G(e[1][0], e[2][1], e[3][2], e[0][3])}

    assert set(G(ep[0][1], ep[1][0]).match(
        G(e[1][0], e[0][1], e[2][3], e[3][2])
    )) == {G(e[1][0], e[0][1]), G(e[2][3], e[3][2])}

    assert set(G(ep[0][0]).match(
        G(e[1][0], e[0][1])
    )) == set()

    assert set(G(ep[0][1], ep[1][0]).match(
        G(e[0][1], e[1][2], e[2][0])
    )) == set()

    assert set(G(ep[0][0]).match(
        G(e[0][1], e[1][2], e[2][0],
          e[0][0], e[1][1], e[2][2])
    )) == {G(e[0][0]), G(e[1][1]), G(e[2][2])}


def test_match_components():
    n = [N() for n in range(0, 6)]
    e = [[E(n1, n2) for n2 in n] for n1 in n]
    np = [N() for np in range(0, 6)]
    ep = [[E(np1, np2) for np2 in np] for np1 in np]

    assert set(G(
        ep[0][1], ep[1][2], ep[2][0]
    ).match(G(
        e[0][1], e[1][2], e[2][0],
        e[3][4], e[4][5], e[5][3]
    ))) == {
        G(e[0][1], e[1][2], e[2][0]),
        G(e[3][4], e[4][5], e[5][3])
    }

    assert set(G(
        ep[0][1], ep[1][2], ep[2][0],
        ep[3][4], ep[4][5], ep[5][3]
    ).match(G(
        e[0][1], e[1][2], e[2][0],
        e[3][4], e[4][5], e[5][3]
    ))) == {G(
        e[0][1], e[1][2], e[2][0],
        e[3][4], e[4][5], e[5][3]
    )}

    assert set(G(
        ep[0][1], ep[1][2], ep[2][0],
        ep[3][4], ep[4][5], ep[5][3]
    ).match(G(
        e[0][1], e[1][2], e[2][0]
    ))) == set()


def test_graft_empty_both():
    assert G().graft(G()) == G()


def test_graft_empty_pattern():
    g = G(E(N(x=1), N(x=2)))
    assert g.graft(G()) == g


def test_graft_mismatch():
    e = E(N(x=1), N(x=2))
    assert G().graft(G(e, marked={e})) is None


def test_graft_node_to_null():
    n = N()
    assert G().graft(G(n, marked={n})) == G(n)


def test_graft_node_to_non_null():
    n1 = N()
    n2 = N()
    assert G(n1).graft(G(n2, marked={n2})) == G(n1, n2)


def test_graft_edge_to_null():
    e = E(N(), N())
    assert G().graft(G(e)) is None
    assert G().graft(G(e, marked={e})) is None
    assert G().graft(G(e, marked={e, e.source})) is None
    assert G().graft(G(e, marked={e, e.target})) is None
    assert G().graft(G(e, marked={e, e.source, e.target})) == G(e)


def test_graft_edge_to_non_null():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    e12 = E(n1, n2)
    e13 = E(n1, n3)
    e23 = E(n2, n3)
    assert G(n1, n2).graft(G(e12)) is None
    assert G(n1, n2).graft(G(e12, marked={e12})).matches(G(e12))
    assert G(n1, n2).graft(G(e13, marked={e13})) is None
    assert G(n1, n2).graft(G(e13, marked={e13, n3})).matches(G(e13, n2))
    assert G(n1).graft(
        G(e12, e13, e23, marked={e12, e13, e23, n2, n3})
    ).matches(
        G(e12, e13, e23)
    )
    assert G(n1, n2).graft(
        G(e12, e13, e23, marked={e12, e13, e23, n3})
    ).matches(
        G(e12, e13, e23)
    )
    assert G(n1, n2, n3).graft(
        G(e12, e13, e23, marked={e12, e13, e23})
    ).matches(
        G(e12, e13, e23)
    )


def test_graft_topographic():
    loops = tuple(range(0, 2))
    nodes = tuple(range(0, 3))
    n = [
        [
            N(loop=loop, node=node)
            for node in nodes
        ]
        for loop in loops
    ]
    g = G(
        # Loop one
        E(n[0][0], n[0][1]),
        E(n[0][1], n[0][2]),
        E(n[0][2], n[0][0]),
        # Loop two
        E(n[1][0], n[1][1]),
        E(n[1][1], n[1][2]),
        E(n[1][2], n[1][0]),
        # Connection between loops
        E(n[0][0], n[1][0])
    )
    new_edges = {
        E(n[0][1], n[1][1]),
        E(n[0][2], n[1][2]),
    }
    gp = copy(g).add(new_edges, new_edges)
    assert gp.matches(g.graft(gp))


def disabled_test_graft_connect_two_subgraphs():
    sides = tuple(range(0, 2))
    cycles = tuple(range(0, 2))
    nodes = tuple(range(0, 3))
    # Create the nodes
    n = [
        [
            [
                N(side=side, cycle=cycle, node=node)
                for node in nodes
            ]
            for cycle in cycles
        ]
        for side in sides
    ]
    g = G(*itertools.chain(
        # Make the cycles
        (
            E(n[side][cycle][node],
              n[side][cycle][(node + 1) % len(nodes)])
            for side in sides
            for cycle in cycles
            for node in nodes
        ),
        # Connect a pair of nodes between cycles on different sides
        (
            E(n[0][cycle][0], n[1][cycle][0])
            for cycle in cycles
        ),
    ))

    np = [
        [
            [
                N()
                for node in nodes
            ]
            for cycle in cycles
        ]
        for side in sides
    ]

    # Connect another pair of nodes between cycles
    add_edges = {
        E(np[0][cycle][1], np[1][cycle][1])
        for cycle in cycles
    }
    gp = G(*itertools.chain(
        # Make the cycle patterns
        (
            E(np[side][cycle][node],
              np[side][cycle][(node + 1) % len(nodes)])
            for side in sides
            for cycle in cycles
            for node in nodes
        ),
        # Mention the nodes connected between cycles
        (
            E(np[0][cycle][0], np[1][cycle][0])
            for cycle in cycles
        ),
        add_edges,
    ))
    print("G")
    print(g.graphviz())
    print("GP")
    print(gp.graphviz())
    print("GRAFTED")
    # FIXME: Takes a long time
    grafted = g.graft(gp, *add_edges)
    assert grafted is not None
    print(grafted.graphviz())
    print("GRAFTED_PATTERN")
    grafted_pattern = G(*itertools.chain(
        # Make the cycles
        (
            E(n[side][cycle][node],
              n[side][cycle][(node + 1) % len(nodes)])
            for side in sides
            for cycle in cycles
            for node in nodes
        ),
        # Connect a pair of nodes between cycles on different sides
        (
            E(n[0][cycle][0], n[1][cycle][0])
            for cycle in cycles
        ),
        (
            E(n[0][cycle][1], n[1][cycle][1])
            for cycle in cycles
            for times in range(0, 2)
        )
    ))
    print(grafted_pattern.graphviz())
    assert grafted_pattern.matches(grafted)
    # FIXME: This takes forever
    # list(grafted_pattern.detailed_match(grafted))


def test_prune_empty_both():
    assert G().prune(G()) == G()


def test_prune_empty_pattern():
    g = G(E(N(x=1), N(x=2)))
    assert g.prune(G()) == g


def test_prune_mismatch():
    e = E(N(x=1), N(x=2))
    assert G().prune(G(e, marked={e})) is None
