from datetime import timedelta

from epimetheus.metrics import Counter, Exposer, Gauge, Histogram, Summary
from epimetheus.sample import SampleKey


def test_counter(frozen_sample_time):
    c = Counter()
    exp = Exposer(c, SampleKey('name'))

    assert list(exp.expose()) == [
        '# TYPE name counter',
        f'name 0 {frozen_sample_time}',
    ]

    c.inc()
    assert list(exp.expose()) == [
        '# TYPE name counter',
        f'name 1 {frozen_sample_time}',
    ]

    c.inc()
    c.inc()
    assert list(exp.expose()) == [
        '# TYPE name counter',
        f'name 3 {frozen_sample_time}',
    ]

    c.inc(10)
    assert list(exp.expose()) == [
        '# TYPE name counter',
        f'name 13 {frozen_sample_time}',
    ]


def test_counter_with_labels(frozen_sample_time):
    c = Counter()
    exp = Exposer(c, SampleKey('name').with_labels(key='value', x=300))

    c.inc(45)
    assert list(exp.expose()) == [
        '# TYPE name counter',
        f'name{{key="value",x="300"}} 45 {frozen_sample_time}',
    ]


def test_gauge(frozen_sample_time):
    g = Gauge()
    exp = Exposer(g, SampleKey('name'))

    assert list(exp.expose()) == [
        '# TYPE name gauge',
        f'name 0 {frozen_sample_time}',
    ]

    g.inc(2)
    assert list(exp.expose()) == [
        '# TYPE name gauge',
        f'name 2 {frozen_sample_time}',
    ]

    g.set(7)
    assert list(exp.expose()) == [
        '# TYPE name gauge',
        f'name 7 {frozen_sample_time}',
    ]

    g.inc(2)
    assert list(exp.expose()) == [
        '# TYPE name gauge',
        f'name 9 {frozen_sample_time}',
    ]

    g.dec(6)
    assert list(exp.expose()) == [
        '# TYPE name gauge',
        f'name 3 {frozen_sample_time}',
    ]


def test_histogram():
    h = Histogram(buckets=[0.3, 0.6])
    exp = Exposer(h, SampleKey('name'))

    assert list(exp.expose()) == [
        '# TYPE name histogram',
        'name_bucket{le="0.3"} 0',
        'name_bucket{le="0.6"} 0',
        'name_bucket{le="+Inf"} 0',
        'name_sum 0',
        'name_count 0',
    ]

    h.observe(0.5)
    assert list(exp.expose()) == [
        '# TYPE name histogram',
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
        '# TYPE name histogram',
        'name_bucket{le="0.3"} 3',
        'name_bucket{le="0.6"} 1',
        'name_bucket{le="+Inf"} 0',
        'name_sum -4.19',
        'name_count 4',
    ]

    h.observe(26)
    h.observe(48)
    assert list(exp.expose()) == [
        '# TYPE name histogram',
        'name_bucket{le="0.3"} 3',
        'name_bucket{le="0.6"} 1',
        'name_bucket{le="+Inf"} 2',
        'name_sum 69.81',
        'name_count 6',
    ]


def test_summary(freezer):
    s = Summary(buckets=[0.25, 0.5, 0.75], time_window=60)
    exp = Exposer(s, SampleKey('name'))

    # no samples
    assert list(exp.expose()) == []

    s.observe(20)  # t = 0
    freezer.tick(delta=timedelta(seconds=20))
    s.observe(30)  # t = 20
    freezer.tick(delta=timedelta(seconds=20))
    s.observe(50)  # t = 40
    # exposing at t = 40
    assert list(exp.expose()) == [
        '# TYPE name summary',
        'name{quantile="0.25"} 25.0',
        'name{quantile="0.5"} 30',
        'name{quantile="0.75"} 40.0',
        'name_sum 100',
        'name_count 3',
    ]

    freezer.tick(delta=timedelta(seconds=30))
    # exposing at t = 70 (first sample popped)
    assert list(exp.expose()) == [
        '# TYPE name summary',
        'name{quantile="0.25"} 35.0',
        'name{quantile="0.5"} 40.0',
        'name{quantile="0.75"} 45.0',
        'name_sum 80',
        'name_count 2',
    ]

    freezer.tick(delta=timedelta(seconds=20))
    # exposing at t = 90 (second sample popped)
    assert list(exp.expose()) == [
        '# TYPE name summary',
        'name{quantile="0.25"} 50',
        'name{quantile="0.5"} 50',
        'name{quantile="0.75"} 50',
        'name_sum 50',
        'name_count 1',
    ]

    freezer.tick(delta=timedelta(seconds=20))
    # exposing at t = 110 (all samples popped)
    assert list(exp.expose()) == []
