import pytest

from epimetheus import Counter, Gauge, Histogram, Summary


def test_counter():
    c = Counter(name='name')

    assert c.get_output() == {
        'count': 0,
    }
    assert list(c.expose()) == ['name 0']

    c.inc()
    assert c.get_output() == {
        'count': 1,
    }
    assert list(c.expose()) == ['name 1']

    c.inc()
    c.inc()
    assert c.get_output() == {
        'count': 3,
    }
    assert list(c.expose()) == ['name 3']

    c.inc(10)
    assert c.get_output() == {
        'count': 13,
    }
    assert list(c.expose()) == ['name 13']


def test_counter_with_labels():
    c = Counter(name='name').with_labels(key='value', x='300')
    c.inc(45)
    assert list(c.expose()) == ['name{key="value",x="300"} 45']


@pytest.mark.skip
def test_many_labels():
    base = Counter(name='name')
    base.inc(2)
    a = base.with_labels(a='1')
    a.inc(3)
    b = base.with_labels(b='2')
    b.inc(4)
    bsub = b.with_labels(s='_')
    bsub.inc(5)
    c = base.with_labels(c='3')
    c.inc(6)

    assert list(base.expose()) == ['name 2']
    assert list(a.expose()) == ['name{a="1"} 3']
    assert list(b.expose()) == ['name{b="2"} 4']
    assert list(bsub.expose()) == ['name{b="2",s="_"} 5']
    assert list(c.expose()) == ['name{c="3"} 6']


@pytest.mark.skip
def test_with_timestamp():
    c = Counter(name='name')
    c.supply_timestamp(True)


def test_gauge():
    g = Gauge(name='name')
    assert g.get_output() == {
        'value': 0,
    }
    g.inc(2)
    assert g.get_output() == {
        'value': 2,
    }
    g.set(7)
    assert g.get_output() == {
        'value': 7,
    }
    g.inc(2)
    assert g.get_output() == {
        'value': 9,
    }
    g.dec(6)
    assert g.get_output() == {
        'value': 3,
    }


def test_histogram():
    h = Histogram(buckets=[0.3, 0.6], name='name')
    assert h.get_output() == {
        'buckets': [0.3, 0.6],
        'counts': [0, 0, 0],
    }
    h.observe(0.5)
    assert h.get_output() == {
        'buckets': [0.3, 0.6],
        'counts': [0, 1, 0],
    }
    h.observe(0.2)
    h.observe(0.11)
    h.observe(-5)
    assert h.get_output() == {
        'buckets': [0.3, 0.6],
        'counts': [3, 1, 0],
    }
    h.observe(26)
    h.observe(48)
    assert h.get_output() == {
        'buckets': [0.3, 0.6],
        'counts': [3, 1, 2],
    }


def test_summary():
    s = Summary(buckets=[0.3, 0.6], name='name')
    assert s.get_output() == {
        'buckets': [0.3, 0.6],
        'samples': [],
    }
    s.observe(26)
    s.observe(5)
    s.observe(84)
    assert s.get_output() == {
        'buckets': [0.3, 0.6],
        'samples': [26, 5, 84],
    }
