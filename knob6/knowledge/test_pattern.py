"""Knob6 knowledge graph pattern tests."""
import pytest
from knob6.knowledge.pattern import \
    EntityGraph as E, RelationGraph as R, FunctionGraph as F
from knob6.directed import Graph as DG

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


@pytest.fixture
def f1():
    """The first function graph pattern"""
    return F()


@pytest.fixture
def f2():
    """The second function graph pattern"""
    return F()


# NO, pylint: disable=too-many-arguments
def test_element(e1, e2, r1, r2, f1, f2):
    assert repr(e1) == "e1 < e1 > e1"
    assert repr(e1 | e2) == "e1 < e1, e2 > e2"
    assert repr(r1) == "r1 < r1 > r1"
    assert repr(r1 | r2) == "r1 < r1, r2 > r2"
    assert repr(f1) == "f1 < f1 > f1"
    assert repr(f1 | f2) == "f1 < f1, f2 > f2"


def test_element_mark(e1, r1, f1):
    assert repr(+e1) == "e1 < +e1 > e1"
    assert repr(-e1) == "e1 < e1 > e1"

    assert repr(+r1) == "r1 < +r1 > r1"
    assert repr(-r1) == "r1 < r1 > r1"

    assert repr(+f1) == "f1 < +f1 > f1"
    assert repr(-f1) == "f1 < f1 > f1"


def test_element_update(e1, r1, f1):
    assert repr(e1(x=1)) == "e1 < e1(x=1) > e1"
    assert repr(e1(**{'foo bar': 'baz'})) == "e1 < e1{'foo bar': 'baz'} > e1"

    assert repr(r1(x=1)) == "r1 < r1(x=1) > r1"
    assert repr(r1(**{'foo bar': 'baz'})) == "r1 < r1{'foo bar': 'baz'} > r1"

    with pytest.raises(ValueError):
        f1(x=1)
    with pytest.raises(ValueError):
        f1(x="func")
    with pytest.raises(ValueError):
        f1(_type=1)
    assert repr(f1(_type="func")) == "f1 < f1.func > f1"


def test_element_update_mark(e1, r1, f1):
    assert repr(+e1(x=1)) == "e1 < +e1(x=1) > e1"
    assert repr(-e1(x=1)) == "e1 < e1(x=1) > e1"

    assert repr(+r1(x=1)) == "r1 < +r1(x=1) > r1"
    assert repr(-r1(x=1)) == "r1 < r1(x=1) > r1"

    assert repr(+f1(_type="func")) == "f1 < +f1.func > f1"
    assert repr(-f1(_type="func")) == "f1 < f1.func > f1"


def test_element_getattr(e1, r1, f1):
    assert repr(e1.state) == "e1 < e1.state > e1"
    assert repr(e1.state.idle) == "e1 < e1.state.idle > e1"
    assert repr(r1.state) == "r1 < r1.state > r1"
    with pytest.raises(NotImplementedError):
        r1.state.idle
    assert repr(f1.state) == "f1 < f1.state > f1"
    with pytest.raises(NotImplementedError):
        f1.state.idle


def test_element_getitem(e1, r1, f1):
    assert repr(e1['foo bar']) == "e1 < e1['foo bar'] > e1"
    assert repr(r1['foo bar']) == "r1 < r1['foo bar'] > r1"
    assert repr(f1['foo bar']) == "f1 < f1['foo bar'] > f1"


def test_element_getattr_mark(e1, r1, f1):
    assert repr(+e1.state) == "e1 < +e1.state > e1"
    assert repr(-e1.state) == "e1 < e1.state > e1"
    assert repr(+r1.state) == "r1 < +r1.state > r1"
    assert repr(-r1.state) == "r1 < r1.state > r1"
    assert repr(+f1.state) == "f1 < +f1.state > f1"
    assert repr(-f1.state) == "f1 < f1.state > f1"


def test_element_getitem_mark(e1, r1, f1):
    assert repr(+e1['foo bar']) == "e1 < +e1['foo bar'] > e1"
    assert repr(-e1['foo bar']) == "e1 < e1['foo bar'] > e1"
    assert repr(+r1['foo bar']) == "r1 < +r1['foo bar'] > r1"
    assert repr(-r1['foo bar']) == "r1 < r1['foo bar'] > r1"
    assert repr(+f1['foo bar']) == "f1 < +f1['foo bar'] > f1"
    assert repr(-f1['foo bar']) == "f1 < f1['foo bar'] > f1"


def test_func_fill(e1, r1, f1):
    assert repr(e1 - f1.func) == "e1 < e1, f1.func[->e1] > f1"
    assert repr(e1 - 'func') == "e1 < e1, f1.func[->e1] > f1"
    assert repr('func' - e1) == "f1 < e1, f1.func[->e1] > e1"
    assert repr(f1.func - e1) == "f1 < e1, f1.func[->e1] > e1"
    assert repr(r1 - f1.func) == "r1 < r1, f1.func[->r1] > f1"
    assert repr(r1 - 'func') == "r1 < r1, f1.func[->r1] > f1"
    assert repr('func' - r1) == "f1 < r1, f1.func[->r1] > r1"
    assert repr(f1.func - r1) == "f1 < r1, f1.func[->r1] > r1"


def test_func_assign(e1, r1, f1):
    with pytest.raises(ValueError):
        _ = e1 * f1
    with pytest.raises(ValueError):
        _ = e1 * f1.func
    with pytest.raises(ValueError):
        _ = e1 * 'func'
    with pytest.raises(ValueError):
        _ = f1 * e1
    with pytest.raises(ValueError):
        _ = f1.func * e1
    with pytest.raises(ValueError):
        _ = 'func' * e1
    assert repr(r1 * f1) == "r1 < r1, f1[r1->] > f1"
    assert repr(r1 * f1.func) == "r1 < r1, f1.func[r1->] > f1"
    assert repr(r1 * 'func') == "r1 < r1, f1.func[r1->] > f1"
    assert repr(f1 * r1) == "f1 < r1, f1[r1->] > r1"
    assert repr(f1.func * r1) == "f1 < r1, f1.func[r1->] > r1"
    assert repr('func' * r1) == "f1 < r1, f1.func[r1->] > r1"


def test_func_assign_and_fill(e1, r1, f1):
    assert repr(e1 - f1 * r1) == "e1 < e1, r1, f1[r1->e1] > r1"
    assert repr(r1 * f1 - e1) == "r1 < e1, r1, f1[r1->e1] > e1"


def test_func_complete(e1, r1, f1):
    assert repr(e1 - f1.func * r1) == "e1 < e1, r1:(func=e1) > r1"
    assert repr(e1 - 'func' * r1) == "e1 < e1, r1:(func=e1) > r1"
    assert repr(e1 - 'ro le' * r1) == "e1 < e1, r1:{'ro le': e1} > r1"
    assert repr(r1 * f1.func - e1) == "r1 < e1, r1:(func=e1) > e1"
    assert repr(r1 * 'func' - e1) == "r1 < e1, r1:(func=e1) > e1"
    assert repr(r1 * 'ro le' - e1) == "r1 < e1, r1:{'ro le': e1} > e1"


def test_assign_filled_func(e1, r1, r2):
    assert repr((e1 - 'func') * r1) == "e1 < e1, r1:(func=e1) > r1"
    assert repr(r1 * ('func' - e1)) == "r1 < e1, r1:(func=e1) > e1"

    with pytest.raises(ValueError):
        (r1 - 'func') * e1
    with pytest.raises(ValueError):
        e1 * ('func' - r1)
    with pytest.raises(ValueError):
        (e1 - 'func') * e1
    with pytest.raises(ValueError):
        e1 * ('func' - e1)

    assert repr((r1 - 'func') * r2) == "r1 < r1, r2:(func=r1) > r2"
    assert repr(r1 * ('func' - r2)) == "r1 < r1:(func=r2), r2 > r2"

    assert repr((r1.x - 'func') * r2.y) == "r1 < r1.x, r2.y:(func=r1) > r2"
    assert repr(r1.x * ('func' - r2.y)) == "r1 < r1.x:(func=r2), r2.y > r2"

    assert repr((r1.x(a=1) - 'func') * r2.y(b=2)) == \
        "r1 < r1.x(a=1), r2.y(b=2):(func=r1) > r2"
    assert repr(r1.x(a=1) * ('func' - r2.y(b=2))) == \
        "r1 < r1.x(a=1):(func=r2), r2.y(b=2) > r2"


def test_double_fill(e1):
    with pytest.raises(ValueError):
        e1 - 'func' - e1


def test_double_assign(r1):
    with pytest.raises(ValueError):
        r1 * 'func' * r1


def test_entity_shift_entity(e1, e2, r1):
    assert repr(e1 >> e2) == "e1 < e1, e2, r1:(source=e1, target=e2) > e2"
    assert repr(e1 - 'source' * r1 * 'target' - e2) == \
        "e1 < e1, e2, r1:(source=e1, target=e2) > e2"
    assert repr(e1 << e2) == "e1 < e1, e2, r1:(source=e2, target=e1) > e2"
    assert repr(e1 - 'target' * r1 * 'source' - e2) == \
        "e1 < e1, e2, r1:(source=e2, target=e1) > e2"


def test_entity_shift_relation(e1, r1):
    assert repr(e1 >> r1) == "e1 < e1, r1:(source=e1) > r1"
    assert repr(e1 << r1) == "e1 < e1, r1:(target=e1) > r1"
    assert repr(r1 >> e1) == "r1 < e1, r1:(target=e1) > e1"
    assert repr(r1 << e1) == "r1 < e1, r1:(source=e1) > e1"


def test_entity_shift_relation_shift_entity(e1, r1, e2):
    assert repr(e1 >> (r1 >> e2)) == \
        "e1 < e1, e2, r1:(source=e1, target=e2) > e2"
    assert repr((e1 >> r1) >> e2) == \
        "e1 < e1, e2, r1:(source=e1, target=e2) > e2"
    assert repr(e1 >> r1 >> e2) == \
        "e1 < e1, e2, r1:(source=e1, target=e2) > e2"
    assert repr(e1 << r1 << e2) == \
        "e1 < e1, e2, r1:(source=e2, target=e1) > e2"


def test_relation_shift_relation(r1, r2):
    assert repr(r1 >> r2) == "r1 < r1, r2:(source=r1, target=r3), r3 > r3"
    assert repr(r1 << r2) == "r1 < r1, r2:(source=r3, target=r1), r3 > r3"


def test_mark_func(r1, f1, e1):
    assert repr(r1 * +f1.func - e1) == "r1 < e1, r1:(+func=e1) > e1"


def test_refs():
    assert repr((x := ~E.x).y >> x) == \
        'e1 < e1.x.y, r1:(source=e1, target=e1) > e1'
    x = None

    assert repr((x := ~E.x) >> x.y) == \
        'e1 < e1.x.y, r1:(source=e1, target=e1) > e1'
    x = None

    assert repr((x := ~E.x) >> +x) == \
        'e1 < +e1.x, +r1:(+source=e1, +target=e1) > e1'
    x = None

    assert repr((x := +~E.x) >> -x) == \
        'e1 < e1.x, +r1:(+source=e1, +target=e1) > e1'
    x = None

    assert repr(+(x := ~E.x) >> x) == \
        'e1 < +e1.x, +r1:(+source=e1, +target=e1) > e1'
    x = None

    assert repr((x := ~E.x >> E.y) >> x) == (
        'e1 < '
        'e1.x, e2.y, e3.y, '
        'r1:(source=e1, target=e2), '
        'r2:(source=e2, target=e1), '
        'r3:(source=e1, target=e3) '
        '> e3'
    )
    x = None

    assert repr((x := ~(E.x >> E.y)) >> x) == (
        'e1 < '
        'e1.x, e2.y, '
        'r1:(source=e1, target=e2), '
        'r2:(source=e2, target=e1) '
        '> e2'
    )
    x = None

    assert repr((x := ~E.x(attr1=10)) >> E.y >> x(attr2=20)) == (
        'e1 < '
        'e1.x(attr1=10, attr2=20), '
        'e2.y, '
        'r1:(source=e1, target=e2), '
        'r2:(source=e2, target=e1) '
        '> e1'
    )
    x = None

    assert repr((x := ~E.x(attr1=10)) >> E.y >> x(attr1=20)) == (
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
        (a := ~E.ll_state.Advertising(
                comment='Device is an "advertiser"')) >>
        R.ll_state_transition >>
        E.ll_state.Standby(comment='No transmit/receive') >>
        R.ll_state_transition >> a
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
    gp = ~gp
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


def test_to_dg():
    assert repr((+(E(a=1) >> E(b=2))).to_dg()) == (
        "{"
        "+n1(a=1), +n2, +n3(b=2), "
        "+e1[n2->n1](_type='source'), "
        "+e2[n2->n3](_type='target')"
        "}"
    )


def test_graft():
    assert repr(DG().graft((+(E(a=1) >> E(b=2))).to_dg())) == (
        "{"
        "n1(a=1), n2, n3(b=2), "
        "e1[n2->n1](_type='source'), "
        "e2[n2->n3](_type='target')"
        "}"
    )
    assert repr(DG() ** +(E(a=1) >> E(b=2))) == (
        "{"
        "n1(a=1), n2, n3(b=2), "
        "e1[n2->n1](_type='source'), "
        "e2[n2->n3](_type='target')"
        "}"
    )
