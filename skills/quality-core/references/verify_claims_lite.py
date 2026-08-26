# -*- coding: utf-8 -*-
"""verify_claims_lite.py — MD/텍스트용 경량 claims 대조 게이트 (quality-core v0.1)

원본 파이프라인의 verify_claims.py(DOCX/PPTX용)를 일반 텍스트·마크다운에 맞게
경량화한 것. 휴리스틱 기반이므로 최종 판단은 리포트를 읽고 사람이 내린다.

사용:
    python3 verify_claims_lite.py --claims claims.json --text draft.md
종료 코드: 오류([E]) 있으면 1, 없으면 0.

검사 항목:
    [E] NUM_UNREG     본문의 유의미 수치가 원장에 미등록
    [E] REMOVED_LEAK  status=removed claim의 핵심 수치/문구가 본문에 잔존
    [E] EST_UNMARKED  estimate claim 수치가 '추정'/'est.' 표기 없이 등장
    [W] NO_URL        verified claim에 url/source 부재
"""
import argparse, json, re, sys, unicodedata

YEAR_RE = re.compile(r"^(19|20)\d{2}$")
NUM_RE = re.compile(r"\d[\d,\.]*")
EST_MARKS = ("추정", "est.", "Est.", "EST.", "전망치")


def norm(s):
    return unicodedata.normalize("NFKC", s)


def significant_numbers(text):
    """유의미 수치 추출: 연도 단독·1~2자리 목록번호 등은 제외하는 휴리스틱."""
    found = []
    for m in NUM_RE.finditer(text):
        tok = m.group().rstrip(".,")
        bare = tok.replace(",", "")
        if YEAR_RE.match(bare):
            continue  # 연도 단독
        try:
            val = float(bare)
        except ValueError:
            continue
        # 아주 작은 정수(목록 번호·챕터 번호 등)는 문맥상 단위가 붙을 때만 유의미로 본다
        ctx = text[m.end(): m.end() + 6]
        has_unit = bool(re.match(r"\s*(%|억|조|만|천|배|년|개월|달러|원|위|건|명|p|pt|%p)", ctx))
        if val < 100 and not has_unit and "." not in bare:
            continue
        found.append((tok, m.start()))
    return found


def num_variants(value):
    """claim value의 표기 변형(콤마 유무 등) 집합."""
    v = str(value).strip()
    out = {v, v.replace(",", "")}
    try:
        f = float(v.replace(",", ""))
        if f.is_integer():
            i = int(f)
            out.add(str(i))
            out.add(f"{i:,}")
    except ValueError:
        pass
    return {x for x in out if x}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", required=True)
    ap.add_argument("--text", required=True)
    args = ap.parse_args()

    ledger = json.load(open(args.claims, encoding="utf-8"))
    claims = ledger.get("claims", [])
    body = norm(open(args.text, encoding="utf-8").read())

    errors, warns = [], []

    # 원장 수치 인덱스
    registered = set()
    for c in claims:
        if c.get("value"):
            registered |= num_variants(c["value"])
        for tok, _ in significant_numbers(norm(c.get("text", ""))):
            registered.add(tok.replace(",", ""))
            registered.add(tok)

    # 1) NUM_UNREG — 본문 유의미 수치가 원장에 없음
    for tok, pos in significant_numbers(body):
        if tok not in registered and tok.replace(",", "") not in registered:
            snippet = body[max(0, pos - 22): pos + 26].replace("\n", " ")
            errors.append(f"[E] NUM_UNREG  '{tok}' 원장 미등록  …{snippet}…")

    for c in claims:
        st, cid = c.get("status"), c.get("id", "?")
        variants = num_variants(c.get("value", "")) if c.get("value") else set()

        # 2) REMOVED_LEAK
        if st == "removed":
            leaked = any(v and v in body for v in variants)
            key = norm(c.get("text", ""))[:18]
            if leaked or (key and key in body):
                errors.append(f"[E] REMOVED_LEAK  {cid} removed claim이 본문에 잔존: {c.get('text','')[:40]}")

        # 3) EST_UNMARKED — estimate 수치 주변 60자 내 추정 표기 확인
        if st == "estimate" and variants:
            for v in variants:
                for m in re.finditer(re.escape(v), body):
                    ctx = body[max(0, m.start() - 60): m.end() + 60]
                    if not any(mk in ctx for mk in EST_MARKS):
                        errors.append(f"[E] EST_UNMARKED  {cid} '{v}' 주변에 추정 표기 없음")
                    break  # 첫 등장만 검사

        # 4) NO_URL
        if st == "verified" and not (c.get("url") or c.get("source")):
            warns.append(f"[W] NO_URL  {cid} verified인데 출처(url/source) 없음")

    # 중복 제거·리포트
    errors = sorted(set(errors))
    warns = sorted(set(warns))
    stats = {s: sum(1 for c in claims if c.get("status") == s) for s in ("verified", "estimate", "removed")}
    print(f"claims 통계: 총 {len(claims)} · verified {stats['verified']} · estimate {stats['estimate']} · removed {stats['removed']}")
    for line in errors + warns:
        print(line)
    print(f"결과: 오류 {len(errors)} · 경고 {len(warns)} → {'FAIL' if errors else 'PASS'}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
