# logging_hj3415/_setup.py
from __future__ import annotations

import os
import sys
from pathlib import Path

from loguru import logger as _logger

_CONFIGURED = False
_CURRENT_LEVEL: str | None = None

def setup_logging(
    level: str | None = None,
    log_file: str | os.PathLike[str] | None = None,
) -> None:
    """
    Configure loguru sinks once.
    - Console sink always enabled
    - Optional file sink (log_file)
    - Idempotent: safe to call multiple times, will only configure once.
    """
    global _CONFIGURED, _CURRENT_LEVEL
    if _CONFIGURED:
        return

    # Allow ENV override, then param, then default
    level = (os.getenv("LOG_LEVEL") or level or "INFO").upper()
    _CURRENT_LEVEL = level

    # 1) remove default sink to avoid duplicate logs
    _logger.remove()

    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "{name}:{function}:{line} - "
        "{message} | {extra}"
    )

    # 2) console sink
    _logger.add(
        sys.stderr,
        level=level,
        colorize=True,
        backtrace=False,
        diagnose=False,
        enqueue=False,  # keep simple (async safe features are extra)
        format=fmt,
    )

    # 3) optional file sink
    if log_file is None:
        env_file = os.getenv("LOG_FILE")
        log_file = env_file if env_file else None

    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        _logger.add(
            str(path),
            level=level,
            rotation=None,   # keep minimal; add later if needed
            retention=None,
            compression=None,
            enqueue=False,
            format=fmt,          # ✅ 파일에도 extra 보이게
        )

    _CONFIGURED = True


def current_log_level() -> str | None:
    return _CURRENT_LEVEL

def reset_logging(
    level: str,
    log_file: str | os.PathLike[str] | None = None,
) -> None:
    global _CONFIGURED, _CURRENT_LEVEL

    _logger.remove()          # 모든 sink 제거
    _CONFIGURED = False       # 다시 설정 가능하게
    _CURRENT_LEVEL = None

    setup_logging(level=level, log_file=log_file)