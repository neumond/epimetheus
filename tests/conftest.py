from datetime import timezone

import pytest


@pytest.fixture
def ts_freezer(freezer):
    def get_ts():
        ts = freezer.time_to_freeze.replace(tzinfo=timezone.utc).timestamp()
        return int(ts * 1000)

    freezer.get_ts = get_ts
    return freezer


@pytest.fixture
def frozen_sample_time(ts_freezer):
    return ts_freezer.get_ts()
