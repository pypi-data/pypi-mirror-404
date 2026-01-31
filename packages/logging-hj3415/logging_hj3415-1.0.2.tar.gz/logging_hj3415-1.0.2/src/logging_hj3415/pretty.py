# logging_hj3415/pretty.py
from __future__ import annotations

import json
from typing import Any


def to_pretty_json(
    obj: Any,
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
) -> str:
    """
    다양한 객체(dto / pydantic / dict / 기타)를
    사람이 보기 좋은 JSON 문자열로 변환한다.

    우선순위:
    1) pydantic v2: model_dump_json
    2) pydantic v2: model_dump + json.dumps
    3) dict / list: json.dumps
    4) fallback: str(obj)

    ⚠️ 이 함수는 "표시/디버그/CLI 출력" 용도다.
    """
    # ✅ pydantic v2 (권장)
    if hasattr(obj, "model_dump_json"):
        try:
            return obj.model_dump_json(
                indent=indent,
                by_alias=False,
                exclude_none=False,
            )
        except Exception:
            pass

    # ✅ pydantic v2 fallback
    if hasattr(obj, "model_dump"):
        try:
            return json.dumps(
                obj.model_dump(),
                ensure_ascii=ensure_ascii,
                indent=indent,
                default=str,
            )
        except Exception:
            pass

    # ✅ dict / list
    if isinstance(obj, (dict, list)):
        try:
            return json.dumps(
                obj,
                ensure_ascii=ensure_ascii,
                indent=indent,
                default=str,
            )
        except Exception:
            pass

    # ✅ 최후의 수단
    return str(obj)