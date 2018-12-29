import re

METRIC_NAME_RE = re.compile(r'^[a-zA-Z_:][a-zA-Z0-9_:]*$')
LABEL_NAME_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


def metric_name(v: str) -> bool:
    return METRIC_NAME_RE.fullmatch(v) is not None


def label_name(v: str) -> bool:
    return LABEL_NAME_RE.fullmatch(v) is not None
