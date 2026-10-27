#!/usr/bin/env python3
"""판정 엔진 템플릿. 계산·판정은 코드, 해석만 AI.
핵심: 임계값/경계값 규칙을 데이터가 아니라 코드에 명시한다.
경계값은 반드시 '같으면 통과인가?'를 주석으로 확정할 것.
"""
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Rule:
    name: str
    field: str
    limit: float
    direction: str          # "max" (<=limit 통과) | "min" (>=limit 통과)
    inclusive: bool = True  # 경계값 포함 여부: True면 같으면 통과
    note: str = ""          # 근거 문서 위치 (파일명·조항·행)

    def check(self, v: float) -> bool:
        if self.direction == "max":
            return v <= self.limit if self.inclusive else v < self.limit
        return v >= self.limit if self.inclusive else v > self.limit

@dataclass
class Verdict:
    passed: bool
    failures: list = field(default_factory=list)
    exceptions: list = field(default_factory=list)

def judge(row: dict, rules: list, exceptions: list = None) -> Verdict:
    """row를 규칙에 대조. 예외 조항이 규칙보다 우선한다."""
    exceptions = exceptions or []
    # 1) 예외 먼저 (요구사항에 예외가 있으면 규칙보다 우선)
    for ex in exceptions:
        if ex(row):
            return Verdict(passed=True, exceptions=[getattr(ex, "__name__", "exception")])
    # 2) 규칙 대조
    fails = []
    for r in rules:
        try:
            v = float(row.get(r.field))
        except (TypeError, ValueError):
            fails.append(f"{r.name}: 값 없음/비숫자 ({r.field})")
            continue
        if not r.check(v):
            fails.append(f"{r.name}: {v} (기준 {r.limit}, {r.direction}, 경계포함={r.inclusive}) [{r.note}]")
    return Verdict(passed=not fails, failures=fails)

def summarize(rows, rules, exceptions=None):
    res = {"total": len(rows), "passed": 0, "failed": 0, "reasons": {}}
    for row in rows:
        v = judge(row, rules, exceptions)
        if v.passed: res["passed"] += 1
        else:
            res["failed"] += 1
            for f in v.failures:
                key = f.split(":")[0]
                res["reasons"][key] = res["reasons"].get(key, 0) + 1
    return res

if __name__ == "__main__":
    RULES = [
        # 예시: Rule("수율하한", "yield_pct", 95.0, "min", inclusive=True, note="출하기준 p.3"),
    ]
    EXCEPTIONS = [
        # 예시: lambda r: r.get("재검사") == "Y",
    ]
    print("RULES를 과제 기준표로 채운 뒤 summarize()를 호출하세요.")
    print("규칙 수:", len(RULES), "/ 예외 수:", len(EXCEPTIONS))
