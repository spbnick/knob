"""Knob4 tests."""
import itertools
from knob4 import Node as N
from knob4 import Edge as E
from knob4 import Graph as G
from knob4 import MatchingNodePattern as MNP
from knob4 import CreatingNodePattern as CNP
from knob4 import EdgePattern as EP
from knob4 import GraphPattern as GP

# Ah, come on, pylint: disable=invalid-name, redefined-outer-name
# Boooring, pylint: disable=missing-function-docstring


def test_match_empty_both():
    assert G().match(GP()) == G()


def test_match_empty_graph_pattern():
    assert G(E(N(x=1), N(x=2))).match(GP()) == G()


def test_match_empty_graph():
    assert G().match(GP(EP(MNP(x=1), MNP(x=2)))) is None


def test_match_one_node():
    g = G(N())
    assert g.match(GP(MNP())) == g
    g = G(N(x=1))
    assert g.match(GP(MNP())) == g
    g = G(N(x=1))
    assert g.match(GP(MNP(x=1))) == g
    g = G(N(x=1, y=2))
    assert g.match(GP(MNP(x=1))) == g


def test_mismatch_one_node():
    gp = GP(MNP(x=2))
    assert G(N(x=1)).match(gp) is None
    assert G(N(y=2)).match(gp) is None


def test_match_one_out_of_two_node_patterns():
    g = G(N(x=2), N(x=3))
    gp = GP(MNP(x=1), MNP(x=2))
    assert g.match(gp) is None


def test_match_two_node():
    g = G(N(x=1), N(x=2))
    gp = GP(MNP(x=1), MNP(x=2))
    assert g.match(gp) == g


def test_match_one_edge():
    g = G(E(N(x=1), N(x=2)))
    gp = GP(EP(MNP(x=1), MNP(x=2)))
    assert g.match(gp) == g


def test_mismatch_one_edge():
    g = G(E(N(x=1), N(x=2), "a"))
    gp = GP(EP(MNP(x=1), MNP(x=2), "b"))
    assert g.match(gp) is None


def test_match_one_out_of_two_edge_patterns():
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


def test_match_self_loop():
    n = N()
    g = G(E(n, n))
    mnp = MNP()
    gp = GP(EP(mnp, mnp))
    assert g.match(gp) == g


def test_match_disconnected_node():
    g = G(E(N(x=1), N(x=2)), N(x=3))
    gp = GP(EP(MNP(x=1), MNP(x=2)), MNP(x=3))
    assert g.match(gp) == g


def test_match_three_nodes_two_edges():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    g = G(E(n1, n2), E(n2, n3))

    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    mnp3 = MNP(x=3)
    gp = GP(EP(mnp1, mnp2), EP(mnp2, mnp3))

    assert g.match(gp) == g


def test_mismatch_missing_edge():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    g = G(E(n1, n2), E(n2, n3))

    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    mnp3 = MNP(x=3)
    gp = GP(EP(mnp1, mnp2), EP(mnp2, mnp3), EP(mnp3, mnp1))
    assert g.match(gp) is None


def test_match_extra_edge():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    g = G(E(n1, n2), E(n2, n3), E(n3, n1))

    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    mnp3 = MNP(x=3)
    gp = GP(EP(mnp1, mnp2), EP(mnp2, mnp3))
    assert g.match(gp) == G(E(n1, n2), E(n2, n3))


def test_match_some_nodes():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)

    assert G(n1, n2).match(GP(mnp1)) == G(n1)
    assert G(n1, n2, n3).match(GP(mnp1, mnp2)) == G(n1, n2)


def test_match_some_edges():
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


def test_match_combination():
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


def test_match_loop():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    mnp1 = MNP()
    mnp2 = MNP()
    mnp3 = MNP()
    g = G(E(n1, n2), E(n2, n3), E(n3, n1))
    assert g.match(GP(
        EP(mnp1, mnp2), EP(mnp2, mnp3), EP(mnp3, mnp1)
    )) == g


def test_match_disconnected_loops():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    n4 = N(x=4)
    n5 = N(x=5)
    n6 = N(x=6)
    mnp1 = MNP()
    mnp2 = MNP()
    mnp3 = MNP()
    g = G(
        E(n1, n2), E(n2, n3), E(n3, n1),
        E(n4, n5), E(n5, n6), E(n6, n4),
    )
    assert g.match(GP(
        EP(mnp1, mnp2), EP(mnp2, mnp3), EP(mnp3, mnp1)
    )) == g


def test_match_nested_loops():
    n1 = N(x=1)
    n2 = N(x=2)
    n3 = N(x=3)
    n4 = N(x=4)
    mnp1 = MNP()
    mnp2 = MNP()
    mnp3 = MNP()
    mnp4 = MNP()
    g = G(
        E(n1, n2), E(n2, n3),
        E(n3, n4), E(n4, n1),
        E(n2, n4), E(n4, n2)
    )
    assert g.match(GP(
        EP(mnp1, mnp2), EP(mnp2, mnp3),
        EP(mnp3, mnp4), EP(mnp4, mnp1),
        EP(mnp2, mnp4), EP(mnp4, mnp2)
    )) == g
    mnp1 = MNP(x=1)
    mnp2 = MNP(x=2)
    mnp3 = MNP(x=3)
    mnp4 = MNP(x=4)
    assert g.match(GP(
        EP(mnp1, mnp2), EP(mnp2, mnp3),
        EP(mnp3, mnp4), EP(mnp4, mnp1),
        EP(mnp2, mnp4), EP(mnp4, mnp2)
    )) == g
    assert g.match(GP(
        EP(mnp1, mnp2), EP(mnp2, mnp3), EP(mnp3, mnp4),
    )) == G(
        E(n1, n2), E(n2, n3), E(n3, n4),
    )
    assert g.match(GP(
        EP(mnp2, mnp4), EP(mnp4, mnp2),
    )) == G(
        E(n2, n4), E(n4, n2),
    )
    assert g.match(GP(EP(mnp1, mnp3))) is None


def test_match_disjointing_nodes():
    n1 = N(x=1)
    n2_1 = N(x=2)
    n2_2 = N(x=2)
    n3 = N(x=3)
    g = G(E(n1, n2_1), E(n2_2, n3))
    mnp1 = MNP(x=1)
    mnp2_1 = MNP(x=2)
    mnp2_2 = MNP(x=2)
    mnp3 = MNP(x=3)
    assert g.match(GP(EP(mnp1, mnp2_1), EP(mnp2_1, mnp3))) is None
    assert g.match(GP(EP(mnp1, mnp2_1), EP(mnp2_2, mnp3))) == g


def test_apply_empty_both():
    assert G().apply(GP()) == G()


def test_apply_empty_graph_pattern():
    assert G(E(N(x=1), N(x=2))).apply(GP()) == G()


def test_apply_empty_graph_and_matching_pattern():
    assert G().apply(GP(EP(MNP(x=1), MNP(x=2)))) is None


def test_apply_first_new_node():
    g = G().apply(GP(CNP()))
    assert g.match(GP(MNP())) == g


def test_apply_first_new_edge():
    mnp = MNP()
    g = G(N())
    assert g.apply(GP(EP(mnp, mnp, ""))) is None
    assert g.apply(GP(EP(mnp, mnp, "", create=False))) is None
    cg = g.apply(GP(EP(mnp, mnp, "", create=True)))
    assert cg.match(GP(mnp)) != cg
    assert cg.match(GP(EP(mnp, mnp))) == cg
    assert cg.match(GP(EP(mnp, mnp, ""))) == cg


def test_apply_topographic():
    sides = tuple(range(0, 2))
    nodes = tuple(range(0, 3))
    n = [
        [
            N(side=side, node=node)
            for node in nodes
        ]
        for side in sides
    ]
    g = G(
        E(n[0][0], n[0][1]), E(n[0][1], n[0][2]), E(n[0][2], n[0][0]),
        E(n[1][0], n[1][1]), E(n[1][1], n[1][2]), E(n[1][2], n[1][0]),
        E(n[0][0], n[1][0])
    )
    mnp = [[MNP() for node in nodes] for side in sides]
    gp = GP(
        EP(mnp[0][0], mnp[0][1]),
        EP(mnp[0][1], mnp[0][2]),
        EP(mnp[0][2], mnp[0][0]),

        EP(mnp[1][0], mnp[1][1]),
        EP(mnp[1][1], mnp[1][2]),
        EP(mnp[1][2], mnp[1][0]),

        EP(mnp[0][0], mnp[1][0]),

        EP(mnp[0][1], mnp[1][1], "new", True),
        EP(mnp[0][2], mnp[1][2], "new", True),
    )
    new_g = G(
        E(n[0][1], n[1][1], "new"),
        E(n[0][2], n[1][2], "new"),
    )
    print(new_g.graphviz())
    assert g.apply(gp) == new_g


def disabled_test_apply_connect_two_subgraphs():
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
        # List all the nodes just in case
        itertools.chain.from_iterable(itertools.chain.from_iterable(n))
    ))

    mnp = [
        [
            [
                MNP()
                for node in nodes
            ]
            for cycle in cycles
        ]
        for side in sides
    ]

    gp = GP(*itertools.chain(
        # Make the cycle patterns
        (
            EP(mnp[side][cycle][node],
               mnp[side][cycle][(node + 1) % len(nodes)])
            for side in sides
            for cycle in cycles
            for node in nodes
        ),
        # Mention the nodes connected between cycles
        (
            EP(mnp[0][cycle][0], mnp[1][cycle][0])
            for cycle in cycles
        ),
        # Connect another pair of nodes between cycles
        (
            EP(mnp[0][cycle][1], mnp[1][cycle][1], "", True)
            for cycle in cycles
        ),
        # List all the node patterns just in case
        itertools.chain.from_iterable(itertools.chain.from_iterable(mnp))
    ))
    #print(g.graphviz())
    #print(g.match(gp).graphviz())
    print(g.apply(gp).graphviz())

    assert False
