# sk-hynix-2nd-harness

SK하이닉스 AI 해커톤 2026 **2차 예선**(2026-10-31, Cofa-Probe, 온라인) 대비용 **Codex 하네스**.
개인 응시 준비물이며, 대회 문제나 정답은 포함하지 않는다.

> 코파톤(2026-07-30) 공개 하네스들의 구조를 참고하되, **Codex 전용 / 180분 / 서술형 6문항**이라는
> 2차 예선 조건에 맞게 다시 짠 것이다.

---

## 왜 이게 필요한가

두 가지 실패가 조용히 일어난다.

1. **환경이 날 배신한다.** Python 3.9의 `fromisoformat`은 `Z` 접미사를 거부한다. 내 노트북에선 통과하는데 시험 입력은 UTC다. 이걸 40분째에 알면 37분을 잃는다.
2. **초록불이 거짓말한다.** 아무것도 구현 안 한 `solve()`에 "위반 0건"이 찍힌다. 기술적으로는 참이고, 실질적으로는 거짓이다. **"맞음"과 "아무것도 안 돌았음"을 구분하지 못하는 검증기는 신뢰받기 때문에 없느니만 못하다.**

그래서 이 하네스는 **정답을 만들지 않는다.** 대신 세 가지를 한다.

- 내가 서 있는 기계가 뭔지 **3분 안에** 알려준다
- 아무것도 검증 못 한 상태를 **exit 2로** 막는다
- 작업 과정을 **나중에 내 말로 설명할 수 있는 형태**로 남긴다 (서술형 30분이 평가에 들어간다)

## 구성

```
AGENTS.md              Codex가 읽는 최우선 지침 (역할·절대규칙·순서·증거규칙)
TASK.md                과제 계약 — 사실/가정/열린질문/안 할 일/완료조건
DECISIONS.md           결정 기록 — 사후 서술형의 재료
RUN.md                 당일 운영표 (경과시간 기준, 180분 + 서술형 30분)
docs/
  담당자_인터뷰.md      숨은 조건을 캐내는 질문 순서
  서술형_대비.md        후속 서술형 6문항 질문뱅크 22개 + 답변 골격
scripts/
  preflight.py         제출 직전 점검 (exit 0 정상 / 1 문제 / 2 검사한 게 없음)
tools/
  eda_bootstrap.py     데이터 첫 파악 — 스키마·결측·이상치 (손으로 열어보지 말 것)
  verdict_engine.py    판정 엔진 — Rule/limit/direction/inclusive 경계값 + 예외 우선
  test_template.py     요구사항 ↔ 테스트 1:1 매핑 템플릿 (표준 unittest, pytest 불필요)
```

## 쓰는 법

### 대회 전 (지금)

```bash
git clone https://github.com/hamjoon2003/sk-hynix-2nd-harness.git
cd sk-hynix-2nd-harness
python3 scripts/preflight.py            # 이 기계가 어떤 상태인지 먼저 본다
```

`preflight.py`가 알려주는 것: Python 버전, 쓸 수 있는 CLI, **시간대 파싱 함정(naive/aware)**,
표준 라이브러리 가용성, 외부 패키지 유무, 디스크·쓰기 권한, 비밀키 스캔, git 상태.
→ `numpy`/`pandas`가 없다는 걸 3분 만에 알면 `pip install`로 30분 날리지 않는다.

### 대회 당일 (사전 체험 15분)

```bash
git clone https://github.com/hamjoon2003/sk-hynix-2nd-harness.git
cd sk-hynix-2nd-harness
python3 scripts/preflight.py
codex            # /status 로 모델·권한, /model 로 Sol 6.1 선택
```

Codex 안에서 첫 프롬프트:

```
AGENTS.md를 읽고 이 세션 지침으로 써. TASK.md와 DECISIONS.md를 채우는 것부터 시작해.
아직 코드는 쓰지 마. README를 읽고 사실/가정/열린질문/안 할 일로 나눠서 보여줘.
```

### 과제 중

| 시점 | 명령 / 행동 |
|---|---|
| 데이터 받으면 | `python3 tools/eda_bootstrap.py <csv>` — 눈으로 열지 않는다 |
| 판정 규칙 나오면 | `tools/verdict_engine.py`의 `RULES`를 채운다. **경계값은 "같으면 통과?"를 주석으로 확정** |
| 완료 조건마다 | `tools/test_template.py`로 테스트 이름 1:1 매핑 |
| 130분쯤 | `python3 scripts/preflight.py` → FAIL 0 만들기 |
| 144분 | **동결. 기능 추가 금지.** |
| 162분 | `python3 scripts/preflight.py` 재실행 |

## preflight의 exit 코드

```
exit 0  전부 확인됨 (단, 정답 증명은 아니다 — 업무 규칙은 테스트가 답한다)
exit 1  확인했는데 문제 있음
exit 2  검사한 항목이 0개 — 이 결과를 '통과'로 읽지 말 것
```

`exit 2`가 이 저장소의 핵심이다. 스캔한 파일이 0개면 "안전"이 아니라 `SKIP`으로 표시하고,
통과 항목이 하나도 없으면 명시적으로 실패한다.

## 2차 예선 제약 (공식 안내 2026-10-26 기준)

| 항목 | 내용 |
|---|---|
| 일시 | 2026-10-31(토) 10:00–14:00, 09:40까지 접속 (**시간대 미표기 — KST면 홍콩 09:00 시작**) |
| 과제 | 최대 **180분** |
| 후속 서술형 | **6문항 × 5분(총 30분)**, AI·복사·붙여넣기 금지 |
| AI | **제공된 Codex만.** Claude Code·별도 모델 연결·개인 API 키 금지 |
| 모델 | 권장 Sol 6.1 / Terra 5.6 / Luna 6 / Sol 6.0 · **Astra 제한** |
| 반입 | **개인 파일 업로드 불가.** 공개 GitHub `git clone`은 허용 |
| 금지 | 외부 전송·공유, `git push`, Computer Use, 감독 설정 우회 |
| 기록 | 대화·터미널·git log·테스트 결과 + **토큰 사용량(간접 평가)** |

토큰이 평가에 걸리므로 **큰 파일을 통째로 읽지 않고, 같은 실행을 이유 없이 반복하지 않는다.**
이 규칙은 `AGENTS.md` 1번에 명시돼 있다.

## 이 저장소가 하지 않는 것

- **문제를 풀지 않는다.** `TASK.md`는 빈 계약서이고, 채우는 것이 일이다.
- **정답·예상문제가 없다.** 대회 문제는 비공개이며, 여기엔 어떤 추측도 넣지 않았다.
- **실제 데이터가 없다.** 도구는 합성 입력으로만 검증했다.
- **`preflight`는 정답 증명이 아니다.** 환경이 성한지 볼 뿐, 알고리즘이 맞는지는 테스트가 답한다.

## 검증한 것

| 주장 | 확인 방법 |
|---|---|
| `preflight`가 미구현/무검사를 통과로 착각하지 않는다 | 빈 디렉터리에서 실행 → 검사 항목 0이면 `exit 2` |
| 시간대 함정을 실행 전에 잡는다 | `preflight`의 datetime 체크가 `2026-10-31 10:00:00`을 `naive`로 표시 |
| 표준 라이브러리만 쓴다 | `tools/*.py`, `scripts/*.py` import 전부 stdlib |
| 비밀키 스캔이 조용히 통과하지 않는다 | 스캔 파일 0개면 PASS가 아니라 `SKIP` + 경고 문구 |
| 도구 3종이 실행된다 (pytest 없이) | `eda_bootstrap.py`, `verdict_engine.py`, `test_template.py` 실행 확인 → `Ran 8 tests` |
| 테스트 전부 skip이면 통과가 아니다 | `preflight`가 `n == nskip` 이면 FAIL 처리 |

## 라이선스

MIT. 개인 준비용이며 SK하이닉스·크래프톤과 무관하다.
하네스 사상 일부는 공개 저장소 `hongkevin/cofathon-prep`(MIT)의 "exit 2" 검증 원칙에서 착안했다.
