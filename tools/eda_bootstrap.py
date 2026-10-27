#!/usr/bin/env python3
"""파일 받은 뒤 5분 안에 구조 파악. 손으로 열어보지 말고 이걸 돌려라.
사용: python eda_bootstrap.py <파일 또는 디렉터리> [...] > eda_report.md
pandas 없으면 csv만 표준 라이브러리로 처리한다.
"""
import sys, os, csv, json, io
from collections import Counter

def summarize_csv(path):
    with open(path, newline='', encoding='utf-8-sig', errors='replace') as f:
        rdr = csv.reader(f)
        rows = list(rdr)
    if not rows: return {"file": path, "rows": 0}
    head, body = rows[0], rows[1:]
    ncol = len(head)
    out = {"file": path, "rows": len(body), "cols": ncol, "columns": []}
    for i, name in enumerate(head):
        vals = [r[i] for r in body if i < len(r)]
        nonempty = [v for v in vals if v.strip() != ""]
        blank = len(vals) - len(nonempty)
        num = 0
        for v in nonempty[:500]:
            try: float(v.replace(",", "")); num += 1
            except: pass
        uniq = Counter(nonempty).most_common(5)
        out["columns"].append({
            "name": name,
            "blank": blank,
            "blank_pct": round(100*blank/max(len(vals),1), 1),
            "numeric_pct": round(100*num/max(len(nonempty),1), 1),
            "top_values": [f"{k}({c})" for k, c in uniq],
        })
    return out

def summarize_json(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        d = json.load(f)
    def shape(x, depth=0):
        if depth > 2: return "..."
        if isinstance(x, list):
            return {"type": "list", "len": len(x), "sample": shape(x[0], depth+1) if x else None}
        if isinstance(x, dict):
            return {"type": "dict", "keys": list(x.keys())[:20]}
        return {"type": type(x).__name__, "sample": str(x)[:60]}
    return {"file": path, "shape": shape(d)}

def walk(target):
    if os.path.isdir(target):
        for root, _, files in os.walk(target):
            for fn in sorted(files):
                yield os.path.join(root, fn)
    else:
        yield target

def main():
    targets = sys.argv[1:] or ["."]
    print("# EDA 자동 요약\n")
    for t in targets:
        for p in walk(t):
            ext = os.path.splitext(p)[1].lower()
            try:
                if ext in (".csv", ".tsv", ".txt"):
                    print(f"\n## {p}")
                    r = summarize_csv(p)
                    print(f"- 행 {r['rows']} / 열 {r['cols']}")
                    print("\n| 열 | 결측 | 결측% | 숫자% | 상위값 |")
                    print("|---|---|---|---|---|")
                    for c in r["columns"]:
                        print(f"| {c['name']} | {c['blank']} | {c['blank_pct']} | {c['numeric_pct']} | {', '.join(c['top_values'])} |")
                elif ext == ".json":
                    print(f"\n## {p}")
                    print("```json\n" + json.dumps(summarize_json(p), ensure_ascii=False, indent=1)[:2000] + "\n```")
                elif ext in (".xlsx", ".xls"):
                    print(f"\n## {p}\n- 엑셀: pandas 필요 → `python -c \"import pandas as pd; x=pd.ExcelFile('{p}'); print(x.sheet_names); [print(s, pd.read_excel(x,s).shape) for s in x.sheet_names]\"`")
                elif ext == ".pdf":
                    print(f"\n## {p}\n- PDF: `pdftotext -layout '{p}' - | head -100`")
                else:
                    print(f"\n## {p}  (미지원 확장자 {ext}, 크기 {os.path.getsize(p)}B)")
            except Exception as e:
                print(f"\n## {p}\n- 실패: {e}")

if __name__ == "__main__":
    main()
