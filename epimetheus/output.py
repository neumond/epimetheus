import math
from typing import Dict, Optional


def label_value(v: str) -> str:
    return v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"')


def label_set(labels: Optional[Dict[str, str]]) -> str:
    if not labels:
        return ''
    x = ','.join(f'{k}="{label_value(v)}"' for k, v in labels.items())
    return '{' + x + '}'


def sample_value(v: float):
    if v == math.inf:
        return 'Inf'
    elif v == -math.inf:
        return '-Inf'
    elif math.isnan(v):
        return 'Nan'
    return str(v)


def sample_timestamp(v: int):
    return str(v)
