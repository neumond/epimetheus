from datetime import timedelta

from epimetheus.metrics import Counter, Gauge, Group, Histogram, Summary
from epimetheus.sample import SampleKey


def test_counter(frozen_sample_time):
    g = Group(
        key=SampleKey('name'),
        mcls=Counter,
    )
    c = g.with_labels()

    assert list(g.expose()) == [
        '# TYPE name counter',
        f'name 0 {frozen_sample_time}',
    ]

    c.inc()
    assert list(g.expose()) == [
        '# TYPE name counter',
        f'name 1 {frozen_sample_time}',
    ]

    c.inc()
    c.inc()
    assert list(g.expose()) == [
        '# TYPE name counter',
        f'name 3 {frozen_sample_time}',
    ]

    c.inc(10)
    assert list(g.expose()) == [
        '# TYPE name counter',
        f'name 13 {frozen_sample_time}',
    ]


def test_counters_with_labels(frozen_sample_time):
    g = Group(
        key=SampleKey('name'),
        mcls=Counter,
    )
    c = g.with_labels(key='value', x=300)

    c.inc(45)
    assert list(g.expose()) == [
        '# TYPE name counter',
        'name{key="value",x="300"} 45 ' f'{frozen_sample_time}',
    ]

    c2 = g.with_labels(key='another', j=18)
    c2.inc(2)

    assert list(g.expose()) == [
        '# TYPE name counter',
        'name{key="value",x="300"} 45 ' f'{frozen_sample_time}',
        'name{key="another",j="18"} 2 ' f'{frozen_sample_time}',
    ]


def test_gauge(frozen_sample_time):
    g = Group(
        key=SampleKey('name'),
        mcls=Gauge,
    )
    m = g.with_labels()

    assert list(g.expose()) == [
        '# TYPE name gauge',
        f'name 0 {frozen_sample_time}',
    ]

    m.inc(2)
    assert list(g.expose()) == [
        '# TYPE name gauge',
        f'name 2 {frozen_sample_time}',
    ]

    m.set(7)
    assert list(g.expose()) == [
        '# TYPE name gauge',
        f'name 7 {frozen_sample_time}',
    ]

    m.inc(2)
    assert list(g.expose()) == [
        '# TYPE name gauge',
        f'name 9 {frozen_sample_time}',
    ]

    m.dec(6)
    assert list(g.expose()) == [
        '# TYPE name gauge',
        f'name 3 {frozen_sample_time}',
    ]


def test_histogram():
    g = Group(
        key=SampleKey('name'),
        mcls=Histogram,
        kwargs={'buckets': [0.3, 0.6]},
    )
    h = g.with_labels()

    assert list(g.expose()) == [
        '# TYPE name histogram',
        'name_bucket{le="0.3"} 0',
        'name_bucket{le="0.6"} 0',
        'name_bucket{le="+Inf"} 0',
        'name_sum 0',
        'name_count 0',
    ]

    h.observe(0.5)
    assert list(g.expose()) == [
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
    assert list(g.expose()) == [
        '# TYPE name histogram',
        'name_bucket{le="0.3"} 3',
        'name_bucket{le="0.6"} 1',
        'name_bucket{le="+Inf"} 0',
        'name_sum -4.19',
        'name_count 4',
    ]

    h.observe(26)
    h.observe(48)
    assert list(g.expose()) == [
        '# TYPE name histogram',
        'name_bucket{le="0.3"} 3',
        'name_bucket{le="0.6"} 1',
        'name_bucket{le="+Inf"} 2',
        'name_sum 69.81',
        'name_count 6',
    ]


def test_summary(freezer):
    g = Group(
        key=SampleKey('name'),
        mcls=Summary,
        kwargs={'buckets': [0.25, 0.5, 0.75], 'time_window': 60},
    )
    s = g.with_labels()

    # no samples
    assert list(g.expose()) == []

    s.observe(20)  # t = 0
    freezer.tick(delta=timedelta(seconds=20))
    s.observe(30)  # t = 20
    freezer.tick(delta=timedelta(seconds=20))
    s.observe(50)  # t = 40
    # exposing at t = 40
    assert list(g.expose()) == [
        '# TYPE name summary',
        'name{quantile="0.25"} 25.0',
        'name{quantile="0.5"} 30',
        'name{quantile="0.75"} 40.0',
        'name_sum 100',
        'name_count 3',
    ]

    freezer.tick(delta=timedelta(seconds=30))
    # exposing at t = 70 (first sample popped)
    assert list(g.expose()) == [
        '# TYPE name summary',
        'name{quantile="0.25"} 35.0',
        'name{quantile="0.5"} 40.0',
        'name{quantile="0.75"} 45.0',
        'name_sum 80',
        'name_count 2',
    ]

    freezer.tick(delta=timedelta(seconds=20))
    # exposing at t = 90 (second sample popped)
    assert list(g.expose()) == [
        '# TYPE name summary',
        'name{quantile="0.25"} 50',
        'name{quantile="0.5"} 50',
        'name{quantile="0.75"} 50',
        'name_sum 50',
        'name_count 1',
    ]

    freezer.tick(delta=timedelta(seconds=20))
    # exposing at t = 110 (all samples popped)
    assert list(g.expose()) == []


def test_group_caching():
    g = Group(
        key=SampleKey('name'),
        mcls=Counter,
    )
    assert g.with_labels() is g.with_labels()
    assert g.with_labels(lol=3) is g.with_labels(lol=3)
    assert g.with_labels() is not g.with_labels(lol=3)


def test_counter_without_clock():
    g = Group(
        key=SampleKey('name'),
        mcls=Counter,
        kwargs={'use_clock': False},
    )
    c = g.with_labels()

    assert list(g.expose()) == [
        '# TYPE name counter',
        'name 0',
    ]

    c.inc()
    assert list(g.expose()) == [
        '# TYPE name counter',
        'name 1',
    ]


def test_gauge_without_clock():
    g = Group(
        key=SampleKey('name'),
        mcls=Gauge,
        kwargs={'use_clock': False},
    )
    m = g.with_labels()

    assert list(g.expose()) == [
        '# TYPE name gauge',
        'name 0',
    ]

    m.set(7)
    assert list(g.expose()) == [
        '# TYPE name gauge',
        'name 7',
    ]


def test_gauge_only_if_changed(ts_freezer):
    g = Group(
        key=SampleKey('name'),
        mcls=Gauge,
        kwargs={'reclock_if_changed': True},
    )
    m = g.with_labels()

    assert list(g.expose()) == [
        '# TYPE name gauge',
        f'name 0 {ts_freezer.get_ts()}',
    ]

    ts_freezer.tick(delta=timedelta(seconds=30))
    time7 = ts_freezer.get_ts()
    m.set(7)

    assert list(g.expose()) == [
        '# TYPE name gauge',
        f'name 7 {time7}',
    ]

    ts_freezer.tick(delta=timedelta(seconds=30))
    m.set(7)

    assert list(g.expose()) == [
        '# TYPE name gauge',
        f'name 7 {time7}',
    ]

    m.set(3)

    assert list(g.expose()) == [
        '# TYPE name gauge',
        f'name 3 {ts_freezer.get_ts()}',
    ]


def test_gauge_set_with_timestamp():
    g = Group(
        key=SampleKey('name'),
        mcls=Gauge,
    )
    m = g.with_labels()

    m.set_with_timestamp(3, 5000)

    assert list(g.expose()) == [
        '# TYPE name gauge',
        'name 3 5000',
    ]
