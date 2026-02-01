from __future__ import annotations

import re
import math


def nan_to_none(v: float | None) -> float | None:
    return None if v is not None and math.isnan(v) else v


_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?\d+(\.\d+)?$")


def parse_number_token(t: str) -> int | float | None:
    """
    문자열 토큰이 숫자 형태인지 판별하여 변환한다.

    - 정수 형태이면 int로 변환
    - 소수 형태이면 float로 변환
    - 숫자가 아니면 None 반환

    주의:
    - 콤마(,)가 포함된 숫자는 처리하지 않는다
    - 지수 표기(1e3 등)는 지원하지 않는다
    - 공백은 사전에 제거되어 있어야 한다
    """
    if _INT_RE.fullmatch(t):
        return int(t)
    if _FLOAT_RE.fullmatch(t):
        return float(t)
    return None
