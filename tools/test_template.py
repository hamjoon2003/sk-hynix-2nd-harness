"""검증 하네스 템플릿. 요구사항 1,2,3을 테스트에 1:1 매핑한다.
이 매핑 자체가 '기술 관리' 축의 증거가 된다.
실행: pytest -q
"""
import pytest

# from verdict_engine import Rule, judge, summarize


def test_요구사항1_중복요청은_한번만_처리된다():
    """README 요구사항 1에 대응."""
    pytest.skip("과제 요구사항으로 교체")


def test_요구사항2_실패시_상태가_복구된다():
    """README 요구사항 2에 대응."""
    pytest.skip("과제 요구사항으로 교체")


def test_요구사항3_경계값_같으면_통과():
    """경계값 규칙을 명시적으로 고정한다. 회귀 방지."""
    # r = Rule("하한", "v", 95.0, "min", inclusive=True)
    # assert r.check(95.0) is True
    # assert r.check(94.99) is False
    pytest.skip("경계값 규칙으로 교체")
