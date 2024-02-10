"""Knob5 knowledge graph tests."""
import pytest
from knob5.knowledge import EntityGraphPattern as E, RelationGraphPattern as R

# Ah, come on, pylint: disable=invalid-name, redefined-outer-name
# Boooring, pylint: disable=missing-function-docstring
# It's not really protected, pylint: disable=protected-access
# No, it's not, pylint: disable=pointless-statement


@pytest.fixture
def e1():
    """The first graph's entity atom operand"""
    return E()


@pytest.fixture
def e2():
    """The second graph's entity atom operand"""
    return E()


@pytest.fixture
def r1():
    """The first graph's relation atom operand"""
    return R()


@pytest.fixture
def r2():
    """The second graph's relation atom operand"""
    return R()


def test_element(e1, r1):
    assert repr(e1) == "e1 < e1 > e1"
    assert repr(r1) == "r1 < r1 > r1"


def test_element_mark(e1, r1):
    assert repr(+e1) == "e1 < +e1 > e1"
    assert repr(-e1) == "e1 < e1 > e1"

    assert repr(+r1) == "r1 < +r1 > r1"
    assert repr(-r1) == "r1 < r1 > r1"


def test_element_update(e1, r1):
    assert repr(e1(x=1)) == "e1 < e1(x=1) > e1"
    assert repr(e1(**{'foo bar': 'baz'})) == "e1 < e1{'foo bar': 'baz'} > e1"

    assert repr(r1(x=1)) == "r1 < r1(x=1) > r1"
    assert repr(r1(**{'foo bar': 'baz'})) == "r1 < r1{'foo bar': 'baz'} > r1"


def test_element_update_mark(e1, r1):
    assert repr(+e1(x=1)) == "e1 < +e1(x=1) > e1"
    assert repr(-e1(x=1)) == "e1 < e1(x=1) > e1"

    assert repr(+r1(x=1)) == "r1 < +r1(x=1) > r1"
    assert repr(-r1(x=1)) == "r1 < r1(x=1) > r1"


def test_element_getattr(e1, r1):
    assert repr(e1.state) == "e1 < e1.state > e1"
    assert repr(e1.state.idle) == "e1 < e1.state.idle > e1"
    assert repr(r1.state) == "r1 < r1.state > r1"
    with pytest.raises(NotImplementedError):
        repr(r1.state.idle)


def test_element_getitem(e1, r1):
    assert repr(e1['foo bar']) == "e1 < e1['foo bar'] > e1"
    assert repr(r1['foo bar']) == "r1 < r1['foo bar'] > r1"


def test_element_getattr_mark(e1, r1):
    assert repr(+e1.state) == "e1 < +e1.state > e1"
    assert repr(-e1.state) == "e1 < e1.state > e1"
    assert repr(+r1.state) == "r1 < +r1.state > r1"
    assert repr(-r1.state) == "r1 < r1.state > r1"


def test_element_getitem_mark(e1, r1):
    assert repr(+e1['foo bar']) == "e1 < +e1['foo bar'] > e1"
    assert repr(-e1['foo bar']) == "e1 < e1['foo bar'] > e1"
    assert repr(+r1['foo bar']) == "r1 < +r1['foo bar'] > r1"
    assert repr(-r1['foo bar']) == "r1 < r1['foo bar'] > r1"


def test_element_role_name_cast(e1, r1):
    assert repr(e1 - 'role') == "e1 < e1 > e1-'role'"
    assert repr('role' - e1) == "'role'-e1 < e1 > e1"
    assert repr(r1 - 'role') == "r1 < r1 > r1-'role'"
    assert repr('role' - r1) == "'role'-r1 < r1 > r1"


def test_element_role_name_open(e1, r1):
    with pytest.raises(ValueError):
        _ = e1 * 'role'
    with pytest.raises(ValueError):
        _ = 'role' * e1
    assert repr(r1 * 'role') == "r1 < r1 > r1*'role'"
    assert repr('role' * r1) == "'role'*r1 < r1 > r1"


def test_element_opening_cast(e1, r1):
    assert repr(e1 - 'role' * r1) == "e1 < e1, r1:(role=e1) > r1"
    assert repr(e1 - 'ro le' * r1) == "e1 < e1, r1:{'ro le': e1} > r1"
    assert repr(r1 * 'role' - e1) == "r1 < e1, r1:(role=e1) > e1"
    assert repr(r1 * 'ro le' - e1) == "r1 < e1, r1:{'ro le': e1} > e1"


def test_element_casting_open(e1, r1, r2):
    assert repr((e1 - 'role') * r1) == "e1 < e1, r1:(role=e1) > r1"
    assert repr(r1 * ('role' - e1)) == "r1 < e1, r1:(role=e1) > e1"

    with pytest.raises(ValueError):
        (r1 - 'role') * e1
    with pytest.raises(ValueError):
        e1 * ('role' - r1)
    with pytest.raises(ValueError):
        (e1 - 'role') * e1
    with pytest.raises(ValueError):
        e1 * ('role' - e1)

    assert repr((r1 - 'role') * r2) == "r1 < r1, r2:(role=r1) > r2"
    assert repr(r1 * ('role' - r2)) == "r2 < r1, r2:(role=r1) > r1"

    assert repr((r1.x - 'role') * r2.y) == "r1 < r1.x, r2.y:(role=r1) > r2"
    assert repr(r1.x * ('role' - r2.y)) == "r2 < r1.y, r2.x:(role=r1) > r1"

    assert repr((r1.x(a=1) - 'role') * r2.y(b=2)) == \
        "r1 < r1.x(a=1), r2.y(b=2):(role=r1) > r2"
    assert repr(r1.x(a=1) * ('role' - r2.y(b=2))) == \
        "r2 < r1.y(b=2), r2.x(a=1):(role=r1) > r1"


def test_double_cast(e1):
    with pytest.raises(ValueError):
        e1 - 'role' - e1


def test_double_open(r1):
    with pytest.raises(ValueError):
        r1 * 'role' * r1


def test_element_edge_element(e1, e2, r1):
    assert repr(e1 >> e2) == "e1 < e1, e2, r1:(source=e1, target=e2) > e2"
    assert repr(e1 - 'source' * r1 * 'target' - e2) == \
        "e1 < e1, e2, r1:(source=e1, target=e2) > e2"
    assert repr(e1 << e2) == "e1 < e1, e2, r1:(target=e1, source=e2) > e2"
    assert repr(e1 - 'target' * r1 * 'source' - e2) == \
        "e1 < e1, e2, r1:(target=e1, source=e2) > e2"


def test_element_edge_role(e1, r1):
    assert repr(e1 >> r1) == "e1 < e1, r1:(source=e1) > r1"
    assert repr(e1 << r1) == "e1 < e1, r1:(target=e1) > r1"
    assert repr(r1 >> e1) == "r1 < e1, r1:(target=e1) > e1"
    assert repr(r1 << e1) == "r1 < e1, r1:(source=e1) > e1"


def test_element_edge_role_edge_element(e1, r1, e2):
    assert repr(e1 >> (r1 >> e2)) == \
        "e1 < e1, e2, r1:(target=e2, source=e1) > e2"
    assert repr((e1 >> r1) >> e2) == \
        "e1 < e1, e2, r1:(source=e1, target=e2) > e2"
    assert repr(e1 >> r1 >> e2) == \
        "e1 < e1, e2, r1:(source=e1, target=e2) > e2"
    assert repr(e1 << r1 << e2) == \
        "e1 < e1, e2, r1:(target=e1, source=e2) > e2"


def test_refs():
    assert repr((x := E().x).y >> x) == \
        'e1 < e1.x.y, r1:(source=e1, target=e1) > e1'
    x = None

    assert repr((x := E().x) >> x.y) == \
        'e1 < e1.x.y, r1:(source=e1, target=e1) > e1'
    x = None

    assert repr((x := E().x) >> +x) == \
        'e1 < +e1.x, r1:(source=e1, target=e1) > e1'
    x = None

    assert repr((x := +E().x) >> -x) == \
        'e1 < e1.x, r1:(source=e1, target=e1) > e1'
    x = None

    assert repr(+(x := E().x) >> x) == \
        'e1 < e1.x, r1:(source=e1, target=e1) > e1'
    x = None

    assert repr((x := E().x >> E().y) >> x) == (
        'e1 < '
        'e1.x, e2.y, r1:(source=e1, target=e2), r2:(source=e2, target=e1) '
        '> e2'
    )
    x = None

    assert repr((x := E().x(attr1=10)) >> E().y >> x(attr2=20)) == (
        'e1 < '
        'e2.y, '
        'r1:(source=e1, target=e2), '
        'e1.x(attr1=10, attr2=20), '
        'r2:(source=e2, target=e1) '
        '> e1'
    )
    x = None

    assert repr((x := E().x(attr1=10)) >> E().y >> x(attr1=20)) == (
        'e1 < '
        'e2.y, '
        'r1:(source=e1, target=e2), '
        'e1.x(attr1=20), '
        'r2:(source=e2, target=e1) '
        '> e1'
    )
    x = None


def test_complex():
    assert repr(
        (a := E().ll_state.Advertising(
                comment='Device is an "advertiser"')) >>
        R().ll_state_transition >>
        E().ll_state.Standby(comment='No transmit/receive') >>
        R().ll_state_transition >> a
    ) == (
        "e1 < "
        "e2.ll_state.Standby(comment='No transmit/receive'), "
        "r1.ll_state_transition:(source=e1, target=e2), "
        "e1.ll_state.Advertising(comment='Device is an \"advertiser\"'), "
        "r2.ll_state_transition:(source=e2, target=e1) "
        "> e1"
    )
