from __future__ import annotations

import os


def is_read_only_runtime() -> bool:
    return os.environ.get('VERCEL') == '1' or os.path.exists('/var/task')


def get_runtime_base_dir() -> str:
    if is_read_only_runtime():
        base = os.path.join('/tmp', 'fortunapick')
    else:
        base = os.path.dirname(__file__)
    os.makedirs(base, exist_ok=True)
    return base


def ensure_runtime_subdir(name: str) -> str:
    path = os.path.join(get_runtime_base_dir(), name)
    os.makedirs(path, exist_ok=True)
    return path


def get_cache_dir() -> str:
    if is_read_only_runtime():
        return ensure_runtime_subdir('cache')
    path = os.path.join(os.path.dirname(__file__), '.cache')
    os.makedirs(path, exist_ok=True)
    return path


def get_report_path(filename: str) -> str:
    if is_read_only_runtime():
        return os.path.join(get_runtime_base_dir(), filename)
    return os.path.join(os.path.dirname(__file__), filename)


def get_checkpoint_dir() -> str:
    if is_read_only_runtime():
        return ensure_runtime_subdir('checkpoints')
    path = os.path.join(os.path.dirname(__file__), '.backtest-checkpoints')
    os.makedirs(path, exist_ok=True)
    return path
