#!/usr/bin/env python3
"""제출 직전 환경·준비 상태 점검. 표준 라이브러리만.

핵심 원칙: **검사한 게 0건이면 통과가 아니다.**
  exit 0 = 전부 확인됨
  exit 1 = 확인했는데 문제 있음
  exit 2 = 아예 검사할 게 없음 (통과로 읽지 말 것)

사용:
  python3 scripts/preflight.py
  python3 scripts/preflight.py --task TASK.md --require outputs/
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"

# 흔한 비밀키 패턴. 높은 확신만 잡는다 — 애매한 건 잡지 않는다.
SECRET_PATTERNS = [
    ("anthropic", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openai", re.compile(r"sk-(?:proj-)?[A-Za-z0-9_\-]{32,}")),
    ("github", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("aws", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("slack", re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

SCAN_EXT = {".py", ".md", ".txt", ".json", ".sh", ".js", ".ts", ".yml", ".yaml", ".env", ".cfg", ".ini", ".html", ".css"}
SCAN_SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "data", "outputs"}
MAX_SCAN_BYTES = 2_000_000


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def add(self, check: str, state: str, detail: str) -> None:
        self.rows.append((check, state, detail))

    def counts(self) -> dict[str, int]:
        out = {PASS: 0, FAIL: 0, SKIP: 0}
        for _, state, _ in self.rows:
            out[state] = out.get(state, 0) + 1
        return out

    def render(self) -> str:
        lines = ["", "── preflight ──────────────────────────────────────────────"]
        width = max((len(c) for c, _, _ in self.rows), default=10)
        for check, state, detail in self.rows:
            mark = {PASS: "[PASS]", FAIL: "[FAIL]", SKIP: "[SKIP]"}[state]
            lines.append("  %s %-*s  %s" % (mark, width, check, detail))
        c = self.counts()
        lines.append("  " + "-" * 58)
        lines.append("  통과 %d · 실패 %d · 건너뜀 %d" % (c[PASS], c[FAIL], c[SKIP]))
        return "\n".join(lines)


def run(cmd: list[str], cwd: Path, timeout: int = 25) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except FileNotFoundError:
        return 127, "명령 없음"
    except subprocess.TimeoutExpired:
        return 124, "시간 초과"


def check_python(rep: Report, root: Path) -> None:
    rc, out = run([sys.executable, "-V"], root)
    if rc == 0:
        rep.add("python", PASS, out.splitlines()[0] if out else "?")
    else:
        rep.add("python", FAIL, out)


def check_env_tools(rep: Report, root: Path) -> None:
    found, missing = [], []
    for tool in ("git", "node", "npm", "jq", "curl"):
        if shutil.which(tool):
            found.append(tool)
        else:
            missing.append(tool)
    if found:
        rep.add("tools", PASS, "있음: " + ", ".join(found) + ((" / 없음: " + ", ".join(missing)) if missing else ""))
    else:
        rep.add("tools", FAIL, "쓸 수 있는 CLI 도구가 없음")


def check_datetime_trap(rep: Report, root: Path) -> None:
    """가장 흔한 함정: naive vs aware 비교."""
    code = (
        "import datetime as d, json\n"
        "r={}\n"
        "for s in ['2026-10-31T10:00:00Z','2026-10-31T10:00:00+09:00','2026-10-31 10:00:00']:\n"
        "    try:\n"
        "        v=d.datetime.fromisoformat(s)\n"
        "        r[s]='aware' if v.tzinfo else 'naive'\n"
        "    except Exception as e:\n"
        "        r[s]='FAIL:'+type(e).__name__\n"
        "print(json.dumps(r))\n"
    )
    rc, out = run([sys.executable, "-c", code], root)
    if rc != 0:
        rep.add("datetime", FAIL, "확인 실패: " + out[:120])
        return
    try:
        data = json.loads(out)
    except Exception:
        rep.add("datetime", FAIL, "출력 해석 실패")
        return
    naive = [k for k, v in data.items() if v == "naive"]
    broken = [k for k, v in data.items() if str(v).startswith("FAIL")]
    detail = ", ".join("%s=%s" % (k.split("T")[1] if "T" in k else k, v) for k, v in data.items())
    if broken:
        rep.add("datetime", FAIL, "파싱 실패 있음 → " + detail)
    elif naive:
        # tz 없는 문자열이 naive로 파싱되는 것은 정상 동작이다.
        # 위험한 건 그것을 aware 시각과 섞는 순간이므로 FAIL이 아니라 경고로 남긴다.
        rep.add("datetime", PASS, "주의: tz 없는 문자열은 naive로 파싱됨 → aware와 섞지 말 것 | " + detail)
    else:
        rep.add("datetime", PASS, detail)


def check_stdlib_modules(rep: Report, root: Path) -> None:
    names = ["json", "csv", "sqlite3", "statistics", "decimal", "dataclasses", "unittest", "pathlib", "zoneinfo"]
    ok, ng = [], []
    for n in names:
        try:
            __import__(n)
            ok.append(n)
        except Exception:
            ng.append(n)
    rep.add("stdlib", PASS if not ng else FAIL,
            "가능: %d/%d%s" % (len(ok), len(names), (" (없음: " + ", ".join(ng) + ")") if ng else ""))

    third = []
    for n in ("numpy", "pandas", "pytest", "requests"):
        try:
            __import__(n)
            third.append(n)
        except Exception:
            pass
    if third:
        rep.add("외부패키지", PASS, "설치됨: " + ", ".join(third))
    else:
        rep.add("외부패키지", PASS, "numpy/pandas/pytest/requests 없음 → 표준 라이브러리로 풀 것")


def check_disk_and_write(rep: Report, root: Path) -> None:
    try:
        st = os.statvfs(str(root))
        free_gb = st.f_bavail * st.f_frsize / (1024 ** 3)
    except Exception:
        free_gb = -1
    probe = root / ".preflight_write_test"
    writable = False
    try:
        probe.write_text("ok", encoding="utf-8")
        writable = probe.read_text(encoding="utf-8") == "ok"
    except Exception:
        writable = False
    finally:
        try:
            probe.unlink()
        except Exception:
            pass
    if not writable:
        rep.add("쓰기권한", FAIL, "현재 디렉터리에 쓸 수 없음")
        return
    rep.add("쓰기권한", PASS, "여유 %.1fGB" % free_gb if free_gb > 0 else "가능")


def check_task(rep: Report, root: Path, task_path: Path) -> None:
    if not task_path.exists():
        rep.add("TASK.md", FAIL, "%s 없음 — 계약을 먼저 쓴다" % task_path)
        return
    text = task_path.read_text(encoding="utf-8", errors="replace")
    required = ["사실", "가정", "안 할 일"]
    missing = [k for k in required if k not in text]
    todo_left = len(re.findall(r"\bTODO\b|미정|작성 필요|<채우기>", text))
    if missing:
        rep.add("TASK.md", FAIL, "필수 절 없음: " + ", ".join(missing))
    elif todo_left > 0:
        rep.add("TASK.md", FAIL, "미완성 표시 %d개 남음" % todo_left)
    else:
        rep.add("TASK.md", PASS, "사실/가정/안 할 일 확인 · %d자" % len(text))


def check_readme_template_leftovers(rep: Report, root: Path) -> None:
    p = root / "README.md"
    if not p.exists():
        rep.add("README", FAIL, "README.md 없음")
        return
    text = p.read_text(encoding="utf-8", errors="replace")
    bad = [w for w in ("TODO", "<채우기>", "여기에 작성", "작성 필요") if w in text]
    if bad:
        rep.add("README", FAIL, "템플릿 문구 남음: " + ", ".join(bad))
    elif len(text) < 120:
        rep.add("README", FAIL, "너무 짧음(%d자) — 심사자가 가장 먼저 보는 파일" % len(text))
    else:
        rep.add("README", PASS, "%d자" % len(text))


def check_secrets(rep: Report, root: Path) -> None:
    hits: list[str] = []
    scanned = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SCAN_SKIP_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() not in SCAN_EXT:
                continue
            try:
                if p.stat().st_size > MAX_SCAN_BYTES:
                    continue
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            scanned += 1
            for name, pat in SECRET_PATTERNS:
                if pat.search(text):
                    hits.append("%s(%s)" % (p.relative_to(root), name))
    if scanned == 0:
        # 스캔할 파일이 0개인 것은 "안전"이 아니다.
        rep.add("비밀키", SKIP, "스캔한 파일 0개 — 이 결과를 '안전'으로 읽지 말 것")
    elif hits:
        rep.add("비밀키", FAIL, "의심: " + ", ".join(hits[:5]))
    else:
        rep.add("비밀키", PASS, "%d개 파일 스캔 · 높은 확신 패턴 없음" % scanned)


def check_outputs(rep: Report, root: Path, required_dir: Path | None) -> None:
    if required_dir is None:
        rep.add("산출물", SKIP, "--require 로 경로를 주면 확인함")
        return
    d = root / required_dir
    if not d.exists():
        rep.add("산출물", FAIL, "%s 없음" % required_dir)
        return
    files = [p for p in d.rglob("*") if p.is_file()]
    if not files:
        rep.add("산출물", FAIL, "%s 는 있는데 파일이 0개 — 빈 결과를 통과로 읽지 말 것" % required_dir)
    else:
        rep.add("산출물", PASS, "%d개 파일" % len(files))


def check_tests(rep: Report, root: Path) -> None:
    """테스트가 실제로 돌았는지 확인. skip만 있고 실행된 게 없으면 통과가 아니다."""
    tests_dir = root / "tests"
    has_dir = tests_dir.is_dir() and any(tests_dir.glob("test_*.py"))

    if has_dir:
        rc, out = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], root, timeout=60)
        label = "tests/"
    else:
        tpl = root / "tools" / "test_template.py"
        if not tpl.exists():
            rep.add("테스트", SKIP, "tests/ 도 tools/test_template.py 도 없음 - 요구사항을 테스트로 옮기지 않았다")
            return
        rc, out = run([sys.executable, str(tpl)], root, timeout=60)
        label = "tools/test_template.py (템플릿만 있음 - 과제 테스트는 tests/ 에 쓸 것)"

    ran = re.search(r"Ran (\d+) tests?", out)
    n = int(ran.group(1)) if ran else 0
    skipped = re.search(r"skipped=(\d+)", out)
    nskip = int(skipped.group(1)) if skipped else 0

    if n == 0:
        rep.add("테스트", FAIL, "실행된 테스트 0개 (%s) - 이 결과를 '통과'로 읽지 말 것" % label)
    elif n == nskip:
        rep.add("테스트", FAIL, "%d개 전부 skip (%s) - 실제로 검증된 게 없다" % (n, label))
    elif rc != 0:
        rep.add("테스트", FAIL, "실패 있음 · Ran %d skip %d (%s)" % (n, nskip, label))
    else:
        rep.add("테스트", PASS, "Ran %d · skip %d · %s" % (n, nskip, label))


def check_git_state(rep: Report, root: Path) -> None:
    rc, out = run(["git", "rev-parse", "--is-inside-work-tree"], root)
    if rc != 0:
        rep.add("git", SKIP, "저장소 아님 — 커밋 기록은 채점 표면이므로 init 권장")
        return
    rc2, out2 = run(["git", "status", "--porcelain"], root)
    changed = len([l for l in out2.splitlines() if l.strip()]) if rc2 == 0 else 0
    rc3, out3 = run(["git", "rev-list", "--count", "HEAD"], root)
    commits = out3.strip() if rc3 == 0 else "0"
    if commits in ("0", ""):
        rep.add("git", FAIL, "커밋 0개 — 커밋 로그가 작업 과정 증거다")
    elif changed:
        rep.add("git", FAIL, "커밋 안 된 변경 %d개" % changed)
    else:
        rep.add("git", PASS, "커밋 %d개 · 작업 트리 깨끗" % int(commits))


def main() -> int:
    ap = argparse.ArgumentParser(description="제출 직전 점검 (exit 2 = 검사한 게 없음)")
    ap.add_argument("--task", default="TASK.md", help="계약 문서 경로")
    ap.add_argument("--require", default=None, help="반드시 존재해야 하는 산출물 디렉터리")
    ap.add_argument("--root", default=".", help="점검 기준 디렉터리")
    ap.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    rep = Report()

    check_python(rep, root)
    check_env_tools(rep, root)
    check_datetime_trap(rep, root)
    check_stdlib_modules(rep, root)
    check_disk_and_write(rep, root)
    check_task(rep, root, (root / args.task) if not Path(args.task).is_absolute() else Path(args.task))
    check_readme_template_leftovers(rep, root)
    check_secrets(rep, root)
    check_outputs(rep, root, args.require)
    check_tests(rep, root)
    check_git_state(rep, root)

    if args.json:
        print(json.dumps({"rows": [{"check": c, "state": s, "detail": d} for c, s, d in rep.rows],
                          "counts": rep.counts()}, ensure_ascii=False, indent=1))
    else:
        print(rep.render())

    counts = rep.counts()
    if counts[FAIL]:
        return 1
    if counts[PASS] == 0:
        print("검사한 항목이 없습니다. 이 결과를 '통과'로 읽지 마세요.")
        return 2
    print("\n전부 확인됨. 단, 이건 정답 증명이 아니다 — 업무 규칙이 맞는지는 테스트가 답한다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
