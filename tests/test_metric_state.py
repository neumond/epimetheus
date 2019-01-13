from epimetheus.metrics import Counter, Exposer, Gauge, Histogram, Summary
from epimetheus.sample import SampleKey


def test_counter(frozen_sample_time):
    c = Counter()
    exp = Exposer(c, SampleKey('name'))

    assert list(exp.expose()) == [
        '# TYPE counter',
        f'name 0 {frozen_sample_time}',
    ]

    c.inc()
    assert list(exp.expose()) == [
        '# TYPE counter',
        f'name 1 {frozen_sample_time}',
    ]

    c.inc()
    c.inc()
    assert list(exp.expose()) == [
        '# TYPE counter',
        f'name 3 {frozen_sample_time}',
    ]

    c.inc(10)
    assert list(exp.expose()) == [
        '# TYPE counter',
        f'name 13 {frozen_sample_time}',
    ]


def test_counter_with_labels(frozen_sample_time):
    c = Counter()
    exp = Exposer(c, SampleKey('name').with_labels(key='value', x=300))

    c.inc(45)
    assert list(exp.expose()) == [
        '# TYPE counter',
        f'name{{key="value",x="300"}} 45 {frozen_sample_time}',
    ]


def test_gauge(frozen_sample_time):
    g = Gauge()
    exp = Exposer(g, SampleKey('name'))

    assert list(exp.expose()) == [
        '# TYPE gauge',
        f'name 0 {frozen_sample_time}',
    ]

    g.inc(2)
    assert list(exp.expose()) == [
        '# TYPE gauge',
        f'name 2 {frozen_sample_time}',
    ]

    g.set(7)
    assert list(exp.expose()) == [
        '# TYPE gauge',
        f'name 7 {frozen_sample_time}',
    ]

    g.inc(2)
    assert list(exp.expose()) == [
        '# TYPE gauge',
        f'name 9 {frozen_sample_time}',
    ]

    g.dec(6)
    assert list(exp.expose()) == [
        '# TYPE gauge',
        f'name 3 {frozen_sample_time}',
    ]


def test_histogram():
    h = Histogram(buckets=[0.3, 0.6])
    exp = Exposer(h, SampleKey('name'))

    assert list(exp.expose()) == [
        '# TYPE histogram',
        'name_bucket{le="0.3"} 0',
        'name_bucket{le="0.6"} 0',
        'name_bucket{le="+Inf"} 0',
        'name_sum 0',
        'name_count 0',
    ]

    h.observe(0.5)
    assert list(exp.expose()) == [
        '# TYPE histogram',
        'name_bucket{le="0.3"} 0',
        'name_bucket{le="0.6"} 1',
        'name_bucket{le="+Inf"} 0',
        'name_sum 0.5',
        'name_count 1',
    ]

    h.observe(0.2)
    h.observe(0.11)
    h.observe(-5)
    assert list(exp.expose()) == [
        '# TYPE histogram',
        'name_bucket{le="0.3"} 3',
        'name_bucket{le="0.6"} 1',
        'name_bucket{le="+Inf"} 0',
        'name_sum -4.19',
        'name_count 4',
    ]

    h.observe(26)
    h.observe(48)
    assert list(exp.expose()) == [
        '# TYPE histogram',
        'name_bucket{le="0.3"} 3',
        'name_bucket{le="0.6"} 1',
        'name_bucket{le="+Inf"} 2',
        'name_sum 69.81',
        'name_count 6',
    ]


def test_summary(frozen_sample_time):
    s = Summary(buckets=[0.25, 0.5, 0.75])
    exp = Exposer(s, SampleKey('name'))

    # no samples
    assert list(exp.expose()) == []

    s.observe(20)
    s.observe(30)
    s.observe(50)
    assert list(exp.expose()) == [
        '# TYPE summary',
        'name{quantile="0.25"} 25.0',
        'name{quantile="0.5"} 30',
        'name{quantile="0.75"} 40.0',
        'name_sum 100',
        'name_count 3',
    ]
