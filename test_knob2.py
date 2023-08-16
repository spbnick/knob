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


def test_element(e, r):
    assert repr(e) == "e"
    assert repr(r) == "r"


def test_element_set_creation(e, r):
    assert repr(+e) == "+e"
    assert repr(-e) == "-e"

    assert repr(+r) == "+r"
    assert repr(-r) == "-r"


def test_element_update(e, r):
    assert repr(e(x=1)) == "e(x=1)"
    assert repr(e(**{'foo bar': 'baz'})) == "e(**{'foo bar': 'baz'})"

    assert repr(r(x=1)) == "r(x=1)"
    assert repr(r(**{'foo bar': 'baz'})) == "r(**{'foo bar': 'baz'})"


def test_element_update_set_creation(e, r):
    assert repr(+e(x=1)) == "+e(x=1)"
    assert repr(-e(x=1)) == "-e(x=1)"

    assert repr(+r(x=1)) == "+r(x=1)"
    assert repr(-r(x=1)) == "-r(x=1)"


def test_element_getattr(e, r):
    assert repr(e.state) == "e.state"
    assert repr(r.state) == "r.state"


def test_element_getitem(e, r):
    assert repr(e['foo bar']) == "e['foo bar']"
    assert repr(r['foo bar']) == "r['foo bar']"


def test_element_getattr_set_creation(e, r):
    assert repr(+e.state) == "+e.state"
    assert repr(-e.state) == "-e.state"
    assert repr(+r.state) == "+r.state"
    assert repr(-r.state) == "-r.state"


def test_element_getitem_set_creation(e, r):
    assert repr(+e['foo bar']) == "+e['foo bar']"
    assert repr(-e['foo bar']) == "-e['foo bar']"
    assert repr(+r['foo bar']) == "+r['foo bar']"
    assert repr(-r['foo bar']) == "-r['foo bar']"


def test_element_role_name_cast(e, r):
    assert repr(e - 'role') == "e - 'role'"
    assert repr('role' - e) == "'role' - e"
    assert repr(r - 'role') == "r - 'role'"
    assert repr('role' - r) == "'role' - r"


def test_element_role_name_open(e, r):
    with pytest.raises(TypeError):
        _ = e * 'role'
    with pytest.raises(TypeError):
        _ = 'role' * e
    assert repr(r * 'role') == "r * 'role'"
    assert repr('role' * r) == "'role' * r"


def test_element_opening_cast(e, r):
    assert repr(e - 'role' * r) == "e - 'role' * r"
    assert repr(r * 'role' - e) == "r * 'role' - e"


def test_element_casting_open(e, r):
    assert repr((e - 'role') * r) == "(e - 'role') * r"
    assert repr(r * ('role' - e)) == "r * ('role' - e)"
    with pytest.raises(TypeError):
        (r - 'role') * e
    with pytest.raises(TypeError):
        e * ('role' - r)
    with pytest.raises(TypeError):
        (e - 'role') * e
    with pytest.raises(TypeError):
        e * ('role' - e)
    assert repr((r - 'role') * r) == "(r - 'role') * r"
    assert repr(r * ('role' - r)) == "r * ('role' - r)"


def test_element_edge_element(e, r):
    assert repr(e >> e) == "e - 'source' * r * 'target' - e"
    assert repr(e - 'source' * r * 'target' - e) == \
        "e - 'source' * r * 'target' - e"
    assert repr(e << e) == "e - 'target' * r * 'source' - e"
    assert repr(e - 'target' * r * 'source' - e) == \
        "e - 'target' * r * 'source' - e"


def test_element_edge_role(e, r):
    assert repr(e >> r) == "e - 'source' * r"
    assert repr(e << r) == "e - 'target' * r"
    assert repr(r >> e) == "r * 'target' - e"
    assert repr(r << e) == "r * 'source' - e"


def test_element_edge_role_edge_element(e, r):
    assert repr(e >> (r >> e)) == "e - 'source' * (r * 'target' - e)"
    assert repr((e >> r) >> e) == "(e - 'source' * r) * 'target' - e"
    assert repr(e >> r >> e) == "(e - 'source' * r) * 'target' - e"
    assert repr(e << r << e) == "(e - 'target' * r) * 'source' - e"


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
