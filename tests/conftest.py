from datetime import timezone

import pytest


@pytest.fixture
def frozen_sample_time(freezer):
    ts = freezer.time_to_freeze.replace(tzinfo=timezone.utc).timestamp()
    return int(ts * 1000)
