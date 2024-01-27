"""Knob5 knowledge graph tests."""
import pytest
from knob5.knowledge import Graph as KG

# Ah, come on, pylint: disable=invalid-name, redefined-outer-name
# Boooring, pylint: disable=missing-function-docstring
# It's not really protected, pylint: disable=protected-access
# No, it's not, pylint: disable=pointless-statement


@pytest.fixture
def g():
    """A graph"""
    return KG()


@pytest.fixture
def e0(g):
    """The first graph's entity atom operand"""
    return g.entity


@pytest.fixture
def e1(g):
    """The second graph's entity atom operand"""
    return g.entity


@pytest.fixture
def r0(g):
    """The first graph's relation atom operand"""
    return g.relation


@pytest.fixture
def r1(g):
    """The second graph's relation atom operand"""
    return g.relation


def reprs(expr):
    """Format a representation of an expression and its evaluated pattern"""
    return repr(expr), repr(expr._eval())


def test_element(e0, r0):
    assert reprs(e0) == ("e0", "e0 < e0 > e0")
    assert reprs(r0) == ("r0", "r0 < r0 > r0")


def test_element_set_creation(e0, r0):
    assert reprs(+e0) == ("+e0", "e0 < +e0 > e0")
    assert reprs(-e0) == ("-e0", "e0 < e0 > e0")

    assert reprs(+r0) == ("+r0", "r0 < +r0 > r0")
    assert reprs(-r0) == ("-r0", "r0 < r0 > r0")


def test_element_update(e0, r0):
    assert reprs(e0(x=1)) == ("e0(x=1)", "e0 < e0(x=1) > e0")
    assert reprs(e0(**{'foo bar': 'baz'})) == (
        "e0(**{'foo bar': 'baz'})",
        "e0 < e0{'foo bar': 'baz'} > e0"
    )

    assert reprs(r0(x=1)) == ("r0(x=1)", "r0 < r0(x=1) > r0")
    assert reprs(r0(**{'foo bar': 'baz'})) == (
        "r0(**{'foo bar': 'baz'})",
        "r0 < r0{'foo bar': 'baz'} > r0"
    )


def test_element_update_set_creation(e0, r0):
    assert reprs(+e0(x=1)) == ("+e0(x=1)", "e0 < +e0(x=1) > e0")
    assert reprs(-e0(x=1)) == ("-e0(x=1)", "e0 < e0(x=1) > e0")

    assert reprs(+r0(x=1)) == ("+r0(x=1)", "r0 < +r0(x=1) > r0")
    assert reprs(-r0(x=1)) == ("-r0(x=1)", "r0 < r0(x=1) > r0")


def test_element_getattr(e0, r0):
    assert reprs(e0.state) == ("e0.state", "e0 < e0.state > e0")
    assert reprs(e0.state.idle) == (
        "e0.state.idle", "e0 < e0.state.idle > e0"
    )
    assert reprs(r0.state) == ("r0.state", "r0 < r0.state > r0")
    with pytest.raises(NotImplementedError):
        reprs(r0.state.idle)


def test_element_getitem(e0, r0):
    assert reprs(e0['foo bar']) == ("e0['foo bar']", "e0 < e0['foo bar'] > e0")
    assert reprs(r0['foo bar']) == ("r0['foo bar']", "r0 < r0['foo bar'] > r0")


def test_element_getattr_set_creation(e0, r0):
    assert reprs(+e0.state) == ("+e0.state", "e0 < +e0.state > e0")
    assert reprs(-e0.state) == ("-e0.state", "e0 < e0.state > e0")
    assert reprs(+r0.state) == ("+r0.state", "r0 < +r0.state > r0")
    assert reprs(-r0.state) == ("-r0.state", "r0 < r0.state > r0")


def test_element_getitem_set_creation(e0, r0):
    assert reprs(+e0['foo bar']) == (
        "+e0['foo bar']",
        "e0 < +e0['foo bar'] > e0"
    )
    assert reprs(-e0['foo bar']) == (
        "-e0['foo bar']",
        "e0 < e0['foo bar'] > e0"
    )
    assert reprs(+r0['foo bar']) == (
        "+r0['foo bar']",
        "r0 < +r0['foo bar'] > r0"
    )
    assert reprs(-r0['foo bar']) == (
        "-r0['foo bar']",
        "r0 < r0['foo bar'] > r0"
    )


def test_element_role_name_cast(e0, r0):
    assert reprs(e0 - 'role') == ("e0 - 'role'", "e0 < e0 > e0-'role'")
    assert reprs('role' - e0) == ("'role' - e0", "'role'-e0 < e0 > e0")
    assert reprs(r0 - 'role') == ("r0 - 'role'", "r0 < r0 > r0-'role'")
    assert reprs('role' - r0) == ("'role' - r0", "'role'-r0 < r0 > r0")


def test_element_role_name_open(e0, r0):
    with pytest.raises(TypeError):
        _ = e0 * 'role'
    with pytest.raises(TypeError):
        _ = 'role' * e0
    assert reprs(r0 * 'role') == ("r0 * 'role'", "r0 < r0 > r0*'role'")
    assert reprs('role' * r0) == ("'role' * r0", "'role'*r0 < r0 > r0")


def test_element_opening_cast(e0, r0):
    assert reprs(e0 - 'role' * r0) == (
        "e0 - 'role' * r0",
        "e0 < e0, r0:(role=e0) > r0"
    )
    assert reprs(e0 - 'ro le' * r0) == (
        "e0 - 'ro le' * r0",
        "e0 < e0, r0:{'ro le': e0} > r0"
    )
    assert reprs(r0 * 'role' - e0) == (
        "r0 * 'role' - e0",
        "r0 < e0, r0:(role=e0) > e0"
    )
    assert reprs(r0 * 'ro le' - e0) == (
        "r0 * 'ro le' - e0",
        "r0 < e0, r0:{'ro le': e0} > e0"
    )


def test_element_casting_open(e0, r0, r1):
    assert reprs((e0 - 'role') * r0) == (
        "(e0 - 'role') * r0",
        "e0 < e0, r0:(role=e0) > r0"
    )
    assert reprs(r0 * ('role' - e0)) == (
        "r0 * ('role' - e0)",
        "r0 < e0, r0:(role=e0) > e0"
    )

    with pytest.raises(TypeError):
        (r0 - 'role') * e0
    with pytest.raises(TypeError):
        e0 * ('role' - r0)
    with pytest.raises(TypeError):
        (e0 - 'role') * e0
    with pytest.raises(TypeError):
        e0 * ('role' - e0)

    assert reprs((r0 - 'role') * r1) == (
        "(r0 - 'role') * r1",
        "r0 < r0, r1:(role=r0) > r1"
    )
    assert reprs(r0 * ('role' - r1)) == (
        "r0 * ('role' - r1)",
        "r0 < r1, r0:(role=r1) > r1"
    )

    assert reprs((r0.x - 'role') * r1.y) == (
        "(r0.x - 'role') * r1.y",
        "r0 < r0.x, r1.y:(role=r0) > r1"
    )
    assert reprs(r0.x * ('role' - r1.y)) == (
        "r0.x * ('role' - r1.y)",
        "r0 < r1.y, r0.x:(role=r1) > r1"
    )

    assert reprs((r0.x(a=1) - 'role') * r1.y(b=2)) == (
        "(r0.x(a=1) - 'role') * r1.y(b=2)",
        "r0 < r0.x(a=1), r1.y(b=2):(role=r0) > r1"
    )
    assert reprs(r0.x(a=1) * ('role' - r1.y(b=2))) == (
        "r0.x(a=1) * ('role' - r1.y(b=2))",
        "r0 < r1.y(b=2), r0.x(a=1):(role=r1) > r1"
    )


def test_double_cast(e0):
    assert repr(e0 - 'role' - e0) == "e0 - 'role' - e0"
    with pytest.raises(ValueError):
        (e0 - 'role' - e0)._eval()


def test_double_open(r0):
    assert repr(r0 * 'role' * r0) == "r0 * 'role' * r0"
    with pytest.raises(ValueError):
        (r0 * 'role' * r0)._eval()


def test_element_edge_element(e0, e1, r0):
    assert reprs(e0 >> e1) == (
        "e0 - 'source' * r1 * 'target' - e1",
        "e0 < e0, e1, r1:(source=e0, target=e1) > e1"
    )
    assert reprs(e0 - 'source' * r0 * 'target' - e1) == (
        "e0 - 'source' * r0 * 'target' - e1",
        "e0 < e0, e1, r0:(source=e0, target=e1) > e1"
    )
    assert reprs(e0 << e1) == (
        "e0 - 'target' * r2 * 'source' - e1",
        "e0 < e0, e1, r2:(target=e0, source=e1) > e1"
    )
    assert reprs(e0 - 'target' * r0 * 'source' - e1) == (
        "e0 - 'target' * r0 * 'source' - e1",
        "e0 < e0, e1, r0:(target=e0, source=e1) > e1"
    )


def test_element_edge_role(e0, r0):
    assert reprs(e0 >> r0) == (
        "e0 - 'source' * r0",
        "e0 < e0, r0:(source=e0) > r0"
    )
    assert reprs(e0 << r0) == (
        "e0 - 'target' * r0",
        "e0 < e0, r0:(target=e0) > r0"
    )
    assert reprs(r0 >> e0) == (
        "r0 * 'target' - e0",
        "r0 < e0, r0:(target=e0) > e0"
    )
    assert reprs(r0 << e0) == (
        "r0 * 'source' - e0",
        "r0 < e0, r0:(source=e0) > e0"
    )


def test_element_edge_role_edge_element(e0, r0, e1):
    assert reprs(e0 >> (r0 >> e1)) == (
        "e0 - 'source' * (r0 * 'target' - e1)",
        "e0 < e0, e1, r0:(target=e1, source=e0) > e1"
    )
    assert reprs((e0 >> r0) >> e1) == (
        "(e0 - 'source' * r0) * 'target' - e1",
        "e0 < e0, e1, r0:(source=e0, target=e1) > e1"
    )
    assert reprs(e0 >> r0 >> e1) == (
        "(e0 - 'source' * r0) * 'target' - e1",
        "e0 < e0, e1, r0:(source=e0, target=e1) > e1"
    )
    assert reprs(e0 << r0 << e1) == (
        "(e0 - 'target' * r0) * 'source' - e1",
        "e0 < e0, e1, r0:(target=e0, source=e1) > e1"
    )


def test_refs():
    g = KG()
    assert reprs(
        (x := g.e.x).y >> x
    ) == (
        "e0.x.y - 'source' * r0 * 'target' - e0.x",
        'e0 < e0.x.y, r0:(source=e0, target=e0) > e0',
    )
    x = None

    g = KG()
    assert reprs(
        (x := g.e.x) >> x.y
    ) == (
        "e0.x - 'source' * r0 * 'target' - e0.x.y",
        'e0 < e0.x, r0:(source=e0, target=e0) > e0',
    )
    x = None

    g = KG()
    assert reprs(
        (x := g.e.x) >> +x
    ) == (
        "e0.x - 'source' * r0 * 'target' - +e0.x",
        'e0 < +e0.x, r0:(source=e0, target=e0) > e0',
    )
    x = None

    g = KG()
    assert reprs(
        (x := +g.e.x) >> -x
    ) == (
        "+e0.x - 'source' * r0 * 'target' - -(+e0.x)",
        'e0 < +e0.x, r0:(source=e0, target=e0) > e0',
    )
    x = None

    g = KG()
    assert reprs(
        (expr := (g.e.x >> g.e.y)) >> expr
    ) == (
        "e0.x - 'source' * r0 * 'target' - e1.y - 'source' * r1 * 'target' - "
        "(e0.x - 'source' * r0 * 'target' - e1.y)",
        'e0 < '
        'e0.x, e1.y, r0:(source=e0, target=e1), r1:(source=e1, target=e0) '
        '> e1',
    )
    expr = None

    g = KG()
    assert reprs(
        (x := g.e.x(attr1=10)) >> g.e.y >> x(attr2=20)
    ) == (
        "",
        ""
    )
    x = None


def test_complex(g):
    assert reprs(
        (a := g.e.ll_state.Advertising(
                comment='Device is an "advertiser"')) >>
        g.r.ll_state_transition >>
        g.e.ll_state.Standby(comment='No transmit/receive') >>
        g.r.ll_state_transition >> a
    ) == (
        "("
            "("  # noqa: E131
                "e0.ll_state.Advertising("  # noqa: E131
                    "comment='Device is an \"advertiser\"'"  # noqa: E131
                ") - "
                "'source' * r0.ll_state_transition"
            ") * 'target' - "
            "e1.ll_state.Standby(comment='No transmit/receive') - "
            "'source' * r1.ll_state_transition"
        ") * "
        "'target' - "
        "e0.ll_state.Advertising("
            "comment='Device is an \"advertiser\"'"
        ")",
        "e0 < "
        "e0.ll_state.Advertising(comment='Device is an \"advertiser\"'), "
        "e1.ll_state.Standby(comment='No transmit/receive'), "
        "r0.ll_state_transition:(source=e0, target=e1), "
        "r1.ll_state_transition:(source=e1, target=e0) "
        "> e0"
    )
