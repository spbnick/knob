"""Knob6 pattern tests."""
import pytest
from knob6.pattern import EntityGraph as E, RelationGraph as R

# Ah, come on, pylint: disable=invalid-name, redefined-outer-name
# Boooring, pylint: disable=missing-function-docstring
# It's not really protected, pylint: disable=protected-access
# No, it's not, pylint: disable=pointless-statement


@pytest.fixture
def e1():
    """The first entity graph pattern"""
    return E()


@pytest.fixture
def e2():
    """The second entity graph pattern"""
    return E()


@pytest.fixture
def r1():
    """The first relation graph pattern"""
    return R()


@pytest.fixture
def r2():
    """The second relation graph pattern"""
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
    assert repr(r1 * ('role' - r2)) == "r1 < r1:(role=r2), r2 > r2"

    assert repr((r1.x - 'role') * r2.y) == "r1 < r1.x, r2.y:(role=r1) > r2"
    assert repr(r1.x * ('role' - r2.y)) == "r1 < r1.x:(role=r2), r2.y > r2"

    assert repr((r1.x(a=1) - 'role') * r2.y(b=2)) == \
        "r1 < r1.x(a=1), r2.y(b=2):(role=r1) > r2"
    assert repr(r1.x(a=1) * ('role' - r2.y(b=2))) == \
        "r1 < r1.x(a=1):(role=r2), r2.y(b=2) > r2"


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
    assert repr(e1 << e2) == "e1 < e1, e2, r1:(source=e2, target=e1) > e2"
    assert repr(e1 - 'target' * r1 * 'source' - e2) == \
        "e1 < e1, e2, r1:(source=e2, target=e1) > e2"


def test_element_edge_role(e1, r1):
    assert repr(e1 >> r1) == "e1 < e1, r1:(source=e1) > r1"
    assert repr(e1 << r1) == "e1 < e1, r1:(target=e1) > r1"
    assert repr(r1 >> e1) == "r1 < e1, r1:(target=e1) > e1"
    assert repr(r1 << e1) == "r1 < e1, r1:(source=e1) > e1"


def test_element_edge_role_edge_element(e1, r1, e2):
    assert repr(e1 >> (r1 >> e2)) == \
        "e1 < e1, e2, r1:(source=e1, target=e2) > e2"
    assert repr((e1 >> r1) >> e2) == \
        "e1 < e1, e2, r1:(source=e1, target=e2) > e2"
    assert repr(e1 >> r1 >> e2) == \
        "e1 < e1, e2, r1:(source=e1, target=e2) > e2"
    assert repr(e1 << r1 << e2) == \
        "e1 < e1, e2, r1:(source=e2, target=e1) > e2"


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
        'e1.x(attr1=10, attr2=20), '
        'e2.y, '
        'r1:(source=e1, target=e2), '
        'r2:(source=e2, target=e1) '
        '> e1'
    )
    x = None

    assert repr((x := E().x(attr1=10)) >> E().y >> x(attr1=20)) == (
        'e1 < '
        'e1.x(attr1=20), '
        'e2.y, '
        'r1:(source=e1, target=e2), '
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
        "e1.ll_state.Advertising(comment='Device is an \"advertiser\"'), "
        "e2.ll_state.Standby(comment='No transmit/receive'), "
        "r1.ll_state_transition:(source=e1, target=e2), "
        "r2.ll_state_transition:(source=e2, target=e1) "
        "> e1"
    )


def test_multidigit_ids():
    gp = E()
    for _ in range(9):
        gp >>= E()
    gp >>= gp
    assert repr(gp) == (
        'e1 < '
        'e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, '
        'r1:(source=e1, target=e2), '
        'r2:(source=e2, target=e3), '
        'r3:(source=e3, target=e4), '
        'r4:(source=e4, target=e5), '
        'r5:(source=e5, target=e6), '
        'r6:(source=e6, target=e7), '
        'r7:(source=e7, target=e8), '
        'r8:(source=e8, target=e9), '
        'r9:(source=e9, target=e10), '
        'r10:(source=e10, target=e1) '
        '> e10'
    )
