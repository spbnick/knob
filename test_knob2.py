import pytest
import knob2


@pytest.fixture
def g():
    """A graph"""
    return knob2.Graph()


@pytest.fixture
def e(g):
    """The graph's entity operand"""
    return g.entity


@pytest.fixture
def r(g):
    """The graph's relation operand"""
    return g.relation


def reprs(expr):
    """Format a representation of an expression and its evaluated pattern"""
    return repr(expr), repr(expr._eval())


def test_element(e, r):
    assert reprs(e) == ("e", "e0 < e0 > e0")
    assert reprs(r) == ("r", "r0 < r0 > r0")


def test_element_set_creation(e, r):
    assert reprs(+e) == ("+e", "e0 < +e0 > e0")
    assert reprs(-e) == ("-e", "e0 < e0 > e0")

    assert reprs(+r) == ("+r", "r0 < +r0 > r0")
    assert reprs(-r) == ("-r", "r0 < r0 > r0")


def test_element_update(e, r):
    assert reprs(e(x=1)) == ("e(x=1)", "e0 < e0(x=1) > e0")
    assert reprs(e(**{'foo bar': 'baz'})) == (
        "e(**{'foo bar': 'baz'})",
        "e0 < e0{'foo bar': 'baz'} > e0"
    )

    assert reprs(r(x=1)) == ("r(x=1)", "r0 < r0(x=1) > r0")
    assert reprs(r(**{'foo bar': 'baz'})) == (
        "r(**{'foo bar': 'baz'})",
        "r0 < r0{'foo bar': 'baz'} > r0"
    )


def test_element_update_set_creation(e, r):
    assert reprs(+e(x=1)) == ("+e(x=1)", "e0 < +e0(x=1) > e0")
    assert reprs(-e(x=1)) == ("-e(x=1)", "e0 < e0(x=1) > e0")

    assert reprs(+r(x=1)) == ("+r(x=1)", "r0 < +r0(x=1) > r0")
    assert reprs(-r(x=1)) == ("-r(x=1)", "r0 < r0(x=1) > r0")


def test_element_getattr(e, r):
    assert reprs(e.state) == ("e.state", "e0 < e0.state > e0")
    assert reprs(e.state.idle) == (
        "e.state.idle", "e0 < e0.state.idle > e0"
    )
    assert reprs(r.state) == ("r.state", "r0 < r0.state > r0")
    with pytest.raises(NotImplementedError):
        reprs(r.state.idle)


def test_element_getitem(e, r):
    assert reprs(e['foo bar']) == ("e['foo bar']", "e0 < e0['foo bar'] > e0")
    assert reprs(r['foo bar']) == ("r['foo bar']", "r0 < r0['foo bar'] > r0")


def test_element_getattr_set_creation(e, r):
    assert reprs(+e.state) == ("+e.state", "e0 < +e0.state > e0")
    assert reprs(-e.state) == ("-e.state", "e0 < e0.state > e0")
    assert reprs(+r.state) == ("+r.state", "r0 < +r0.state > r0")
    assert reprs(-r.state) == ("-r.state", "r0 < r0.state > r0")


def test_element_getitem_set_creation(e, r):
    assert reprs(+e['foo bar']) == (
        "+e['foo bar']",
        "e0 < +e0['foo bar'] > e0"
    )
    assert reprs(-e['foo bar']) == (
        "-e['foo bar']",
        "e0 < e0['foo bar'] > e0"
    )
    assert reprs(+r['foo bar']) == (
        "+r['foo bar']",
        "r0 < +r0['foo bar'] > r0"
    )
    assert reprs(-r['foo bar']) == (
        "-r['foo bar']",
        "r0 < r0['foo bar'] > r0"
    )


def test_element_role_name_cast(e, r):
    assert reprs(e - 'role') == ("e - 'role'", "e0 < e0 > e0-'role'")
    assert reprs('role' - e) == ("'role' - e", "'role'-e0 < e0 > e0")
    assert reprs(r - 'role') == ("r - 'role'", "r0 < r0 > r0-'role'")
    assert reprs('role' - r) == ("'role' - r", "'role'-r0 < r0 > r0")


def test_element_role_name_open(e, r):
    with pytest.raises(TypeError):
        _ = e * 'role'
    with pytest.raises(TypeError):
        _ = 'role' * e
    assert reprs(r * 'role') == ("r * 'role'", "r0 < r0 > r0*'role'")
    assert reprs('role' * r) == ("'role' * r", "'role'*r0 < r0 > r0")


def test_element_opening_cast(e, r):
    assert reprs(e - 'role' * r) == (
        "e - 'role' * r",
        "e0 < e0, r0:(role=e0) > r0"
    )
    assert reprs(e - 'ro le' * r) == (
        "e - 'ro le' * r",
        "e0 < e0, r0:{'ro le': e0} > r0"
    )
    assert reprs(r * 'role' - e) == (
        "r * 'role' - e",
        "r0 < e0, r0:(role=e0) > e0"
    )
    assert reprs(r * 'ro le' - e) == (
        "r * 'ro le' - e",
        "r0 < e0, r0:{'ro le': e0} > e0"
    )


def test_element_casting_open(e, r):
    assert reprs((e - 'role') * r) == (
        "(e - 'role') * r",
        "e0 < e0, r0:(role=e0) > r0"
    )
    assert reprs(r * ('role' - e)) == (
        "r * ('role' - e)",
        "r0 < e0, r0:(role=e0) > e0"
    )

    with pytest.raises(TypeError):
        (r - 'role') * e
    with pytest.raises(TypeError):
        e * ('role' - r)
    with pytest.raises(TypeError):
        (e - 'role') * e
    with pytest.raises(TypeError):
        e * ('role' - e)

    assert reprs((r - 'role') * r) == (
        "(r - 'role') * r",
        "r0 < r0, r1:(role=r0) > r1"
    )
    assert reprs(r * ('role' - r)) == (
        "r * ('role' - r)",
        "r1 < r0, r1:(role=r0) > r0"
    )

    assert reprs((r.x - 'role') * r.y) == (
        "(r.x - 'role') * r.y",
        "r0 < r0.x, r1.y:(role=r0) > r1"
    )
    assert reprs(r.x * ('role' - r.y)) == (
        "r.x * ('role' - r.y)",
        "r1 < r0.y, r1.x:(role=r0) > r0"
    )

    assert reprs((r.x(a=1) - 'role') * r.y(b=2)) == (
        "(r.x(a=1) - 'role') * r.y(b=2)",
        "r0 < r0.x(a=1), r1.y(b=2):(role=r0) > r1"
    )
    assert reprs(r.x(a=1) * ('role' - r.y(b=2))) == (
        "r.x(a=1) * ('role' - r.y(b=2))",
        "r1 < r0.y(b=2), r1.x(a=1):(role=r0) > r0"
    )


def test_double_cast(e):
    assert repr(e - 'role' - e) == "e - 'role' - e"
    with pytest.raises(ValueError):
        (e - 'role' - e)._eval()


def test_double_open(r):
    assert repr(r * 'role' * r) == "r * 'role' * r"
    with pytest.raises(ValueError):
        (r * 'role' * r)._eval()


def test_element_edge_element(e, r):
    assert reprs(e >> e) == (
        "e - 'source' * r * 'target' - e",
        "e0 < e0, e1, r0:(source=e0, target=e1) > e1"
    )
    assert reprs(e - 'source' * r * 'target' - e) == (
        "e - 'source' * r * 'target' - e",
        "e0 < e0, e1, r0:(source=e0, target=e1) > e1"
    )
    assert reprs(e << e) == (
        "e - 'target' * r * 'source' - e",
        "e0 < e0, e1, r0:(target=e0, source=e1) > e1"
    )
    assert reprs(e - 'target' * r * 'source' - e) == (
        "e - 'target' * r * 'source' - e",
        "e0 < e0, e1, r0:(target=e0, source=e1) > e1"
    )


def test_element_edge_role(e, r):
    assert reprs(e >> r) == (
        "e - 'source' * r",
        "e0 < e0, r0:(source=e0) > r0"
    )
    assert reprs(e << r) == (
        "e - 'target' * r",
        "e0 < e0, r0:(target=e0) > r0"
    )
    assert reprs(r >> e) == (
        "r * 'target' - e",
        "r0 < e0, r0:(target=e0) > e0"
    )
    assert reprs(r << e) == (
        "r * 'source' - e",
        "r0 < e0, r0:(source=e0) > e0"
    )


def test_element_edge_role_edge_element(e, r):
    assert reprs(e >> (r >> e)) == (
        "e - 'source' * (r * 'target' - e)",
        "e0 < e0, e1, r0:(target=e1, source=e0) > e1"
    )
    assert reprs((e >> r) >> e) == (
        "(e - 'source' * r) * 'target' - e",
        "e0 < e0, e1, r0:(source=e0, target=e1) > e1"
    )
    assert reprs(e >> r >> e) == (
        "(e - 'source' * r) * 'target' - e",
        "e0 < e0, e1, r0:(source=e0, target=e1) > e1"
    )
    assert reprs(e << r << e) == (
        "(e - 'target' * r) * 'source' - e",
        "e0 < e0, e1, r0:(target=e0, source=e1) > e1"
    )


def test_complex(e, r):
    s = e.ll_state
    t = r.ll_state_transition
    assert repr(
        (a := s.Advertising(comment='Device is an "advertiser"')) >> t >>
        s.Standby(comment='No transmit/receive') >> t >> a
    ) == \
    "(" \
        "(" \
            "e.ll_state.Advertising(" \
                "comment='Device is an \"advertiser\"'" \
            ") - " \
            "'source' * r.ll_state_transition" \
        ") * 'target' - " \
        "e.ll_state.Standby(comment='No transmit/receive') - " \
        "'source' * r.ll_state_transition" \
    ") * " \
    "'target' - " \
    "e.ll_state.Advertising(" \
        "comment='Device is an \"advertiser\"'" \
    ")"
