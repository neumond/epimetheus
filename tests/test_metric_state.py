from epimetheus import Counter, Gauge, Histogram, Summary


def test_counter():
    c = Counter(name='name')
    assert c.get_output() == {
        'count': 0,
    }
    assert list(c.expose()) == [
        'name 0',
    ]
    c.inc()
    assert c.get_output() == {
        'count': 1,
    }
    c.inc()
    c.inc()
    assert c.get_output() == {
        'count': 3,
    }
    c.inc(10)
    assert c.get_output() == {
        'count': 13,
    }


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
