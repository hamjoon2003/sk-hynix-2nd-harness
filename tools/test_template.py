#!/usr/bin/env python3
"""검증 하네스 템플릿 — 요구사항 <-> 테스트 1:1 매핑.

이 매핑 자체가 '기술 관리' 축의 증거가 된다. 요구사항이 문장으로만 있으면 검증되지 않는다.

**표준 unittest만 쓴다.** 시험 환경에 pytest가 없을 수 있기 때문이다.
(pytest가 있어도 `python3 -m unittest` 로 그대로 돈다)

실행:
    python3 tools/test_template.py           # 이 파일 자체 점검
    python3 -m unittest discover -s tests -v # 과제 테스트 전체

규칙:
- 테스트 이름은 업무 규칙을 문장으로 읽히게 짓는다.
  test_out_of_stock_product_is_excluded (o) / test_case_3 (x)
- 정상 경로만 쓰지 않는다. 결측 / 빈 입력 / 경계값 / 중복 / 순서 / 실패 를 포함한다.
- 새 규칙을 넣을 때 **먼저 빨간불을 확인**한다. 실패를 못 본 테스트는 통과를 신뢰하지 않는다.
"""
from __future__ import annotations

import unittest


class RequirementContractTests(unittest.TestCase):
    """요구사항 1:1 매핑. 아래 세 개를 과제 요구사항으로 교체한다."""

    def test_requirement_1_duplicate_request_is_processed_once(self) -> None:
        """README 요구사항 1에 대응 - 중복 요청은 한 번만 처리된다."""
        self.skipTest("과제 요구사항으로 교체")

    def test_requirement_2_state_is_recovered_after_failure(self) -> None:
        """README 요구사항 2에 대응 - 실패 후 상태가 복구된다."""
        self.skipTest("과제 요구사항으로 교체")

    def test_requirement_3_boundary_value_passes_when_inclusive(self) -> None:
        """경계값 규칙을 코드로 고정한다. '같으면 통과'를 회귀 방지로 못박는다."""
        # from verdict_engine import Rule
        # r = Rule("하한", "v", 95.0, "min", inclusive=True)
        # self.assertTrue(r.check(95.0))    # 같으면 통과
        # self.assertFalse(r.check(94.99))  # 그 아래는 실패
        self.skipTest("경계값 규칙으로 교체")


class EdgeCaseTests(unittest.TestCase):
    """실패 경로 - 채점에서 변별력이 가장 큰 구간."""

    def test_empty_input_does_not_crash(self) -> None:
        self.skipTest("빈 입력 처리로 교체")

    def test_missing_field_is_handled_or_fails_loudly(self) -> None:
        """조용히 틀리는 것보다 명시적으로 실패하는 편이 낫다."""
        self.skipTest("결측 필드 처리로 교체")

    def test_same_input_produces_same_output(self) -> None:
        """결정성 - 같은 입력에 같은 출력. tie-break를 명시했는지 확인."""
        self.skipTest("결정성 검증으로 교체")


class DatetimeBoundaryTests(unittest.TestCase):
    """가장 흔한 함정: naive/aware 혼용, 시간대 경계. 실행되는 실제 테스트."""

    def test_naive_and_aware_are_not_compared_directly(self) -> None:
        import datetime as dt

        naive = dt.datetime.fromisoformat("2026-10-31 10:00:00")
        aware = dt.datetime.fromisoformat("2026-10-31T10:00:00+00:00")
        self.assertIsNone(naive.tzinfo)
        self.assertIsNotNone(aware.tzinfo)
        with self.assertRaises(TypeError):
            _ = naive < aware  # 실제로 터진다는 사실을 테스트로 고정한다

    def test_z_suffix_vs_offset_gives_same_instant(self) -> None:
        import datetime as dt

        try:
            a = dt.datetime.fromisoformat("2026-10-31T10:00:00Z")
        except ValueError:
            self.skipTest("이 Python은 'Z' 접미사 미지원 -> '+00:00'으로 변환해 쓸 것")
        b = dt.datetime.fromisoformat("2026-10-31T10:00:00+00:00")
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main(verbosity=2)
