from __future__ import annotations

import re

_WS_RE = re.compile(r"\s+")

def clean_text(s: str | None) -> str:
    """
    문자열을 사람이 읽기 좋은 형태로 정규화한다.
    - None → ""
    - NBSP 제거
    - 연속 공백 → 단일 공백
    - 좌우 공백 제거
    """
    if s is None:
        return ""
    s = s.replace("\xa0", " ")
    return _WS_RE.sub(" ", s).strip()