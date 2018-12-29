from typing import Dict


def label_value(v: str) -> str:
    return v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"')


def label_set(labels: Dict[str, str]) -> str:
    x = ','.join(f'{k}="{label_value(v)}"' for k, v in labels.items())
    return '{' + x + '}'
