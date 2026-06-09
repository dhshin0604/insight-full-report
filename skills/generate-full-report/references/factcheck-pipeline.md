# factcheck-pipeline.md — Deep Verification (할루시네이션 제거 파이프라인) v0.9

> 목적: 본문에 들어가는 **모든 사실 주장(claim)** 을 출처와 1:1로 묶어, 검증되지 않은
> 수치·고유명사·인용이 최종 산출물에 남지 못하게 한다. Anthropic 블로그의
> **deep verification 패턴**(주장 추출 → 주장별 검증 에이전트 → 합산 게이트)을 따른다.

---

## 1. Claims Ledger (claims.json) — 단일 진실원

Phase 2(구조화) 진행 중 본문 초안에 **사실 주장**이 등장할 때마다 ledger에 등록한다.
빌드 디렉터리 루트에 `claims.json` 으로 저장:

```json
{
  "topic": "AI에이전트",
  "claims": [
    {
      "id": "C001",
      "text": "2025년 글로벌 AI 에이전트 시장 규모는 52억 달러",
      "kind": "numeric",
      "value": "52",
      "source": "MarketsandMarkets, 2025-10",
      "url": "https://...",
      "status": "verified",
      "method": "web",
      "note": "원문 USD 5.2B → 52억 달러 환산"
    },
    {
      "id": "C002",
      "text": "OpenAI Operator는 2026년 1월 출시",
      "kind": "event",
      "value": "2026",
      "source": "OpenAI 공식 블로그",
      "url": "https://openai.com/...",
      "status": "verified",
      "method": "source-doc"
    },
    {
      "id": "C003",
      "text": "2030년 시장 규모 500억 달러 전망",
      "kind": "numeric",
      "value": "500",
      "source": "보고서 자체 추정 (CAGR 45% 외삽)",
      "status": "estimate",
      "method": "calc"
    }
  ]
}
```

### claim 등록 대상 (하나라도 해당하면 등록)
- 수치: 금액, 비율, 성장률, 사용자 수, 연도별 실적, 순위
- 사건: 출시일, 인수합병, 발표, 규제 시행
- 인용: 인물 발언, 보고서 문구
- 고유명사 간 관계: "A사가 B를 인수", "C 모델이 D 벤치마크 1위"

### status 값 (3종만 허용)
| status | 의미 | 본문 처리 |
|---|---|---|
| `verified` | 소스 원문 또는 웹에서 직접 확인 | 그대로 사용 + Source 표기 |
| `estimate` | 직접 확인 불가, 계산/외삽/추정 | 본문에 반드시 `추정`(KR) / `est.`(EN) 표기 |
| `removed` | 검증 실패 | **본문에서 삭제** — 최종 문서에 남으면 게이트 FAIL |

---

## 2. 검증 규칙 (작성 시점에 적용)

1. **소스에 없는 수치를 만들어내지 않는다.** 소스에 수치가 없으면 수치 없이 서술하거나
   `estimate` 로 등록하고 산출 근거(method=calc, note)를 남긴다.
2. **단위·기간·환율 정합**: 원문 USD/CNY/JPY → KRW 환산 시 환산 기준을 note에 기록.
   YoY/QoQ, 회계연도(FY) 차이를 본문에 명시.
3. **두 소스가 충돌**하면 본문에 두 값을 병기하거나 보수적인 값 채택 + note 기록.
4. **사실과 해석의 분리**: 분석·전망 문장은 claim이 아니라 의견이다.
   "~로 해석됨", "~할 가능성이 큼" 처럼 의견임이 드러나는 서술로 쓴다.
   의견을 사실처럼 단정("~이다")하지 않는다.
5. **기억으로 쓰지 않는다**: 모델 사전지식에서 온 수치·날짜는 반드시 WebSearch/WebFetch로
   재확인 후 verified 처리. 확인 실패 시 estimate 또는 removed.

---

## 3. 검증 실행 — 두 가지 모드

### 3-A. 단일 컨텍스트 모드 (기본 Phase 2.7)
초안 완성 후 **비평가 패스**를 별도로 1회 수행한다:
1. 본문에서 claim 후보를 전수 추출해 claims.json과 대조 (누락분 등록)
2. `verified` 가 아닌 claim을 하나씩 WebSearch/WebFetch/소스 재독으로 확인
3. 확인 실패 → status=removed + 본문에서 해당 문장 수정/삭제
4. `python3 references/verify_claims.py --claims claims.json --docx {파일}` 로 기계 검증

### 3-B. 동적 워크플로 모드 (Phase D — deep verification fan-out)
`build_4set.workflow.js` 의 FACTCHECK 단계:
- **추출 에이전트** 1개가 챕터 초안 전체에서 claim 목록 추출
- claim **묶음(5~10개)당 검증 에이전트** 1개를 fan-out — 각자 깨끗한 컨텍스트에서
  소스 대조·웹 검색으로 verified/estimate/removed 판정 (self-preferential bias 차단)
- **회의(skeptic) 에이전트** 1개가 verified 판정 중 표본을 재검증 (false-verified 차단)
- 결과를 claims.json 으로 합산 → removed claim 반영해 챕터 수정

---

## 4. verify_claims.py — 기계 게이트

```bash
# DOCX
python3 references/verify_claims.py --claims claims.json --docx {주제}_KR_Report.docx --lang kr
# PPTX (unpacked)
python3 references/verify_claims.py --claims claims.json --unpacked unpacked_kr --lang kr
```

검사 항목:
- [E] `NUM_UNREG` — 본문 유의미 수치가 ledger에 미등록 (연도 단독·전화번호·슬라이드 좌표 제외)
- [E] `REMOVED_LEAK` — status=removed claim 텍스트가 본문에 잔존
- [E] `EST_UNMARKED` — estimate claim 수치가 본문에 `추정`/`est.` 표기 없이 등장
- [W] `NO_URL` — verified claim에 url/source 부재

`gate_report.py` 가 `--claims claims.json` 옵션으로 이 게이트를 toc/content/judge와 합산한다.

---

## 5. Source 표기 의무

- PPTX: 본문 슬라이드 Zone5에 해당 슬라이드 수치의 출처 표기
- DOCX: 수치가 밀집된 절 끝 또는 문서 말미 출처 섹션에 claim source 나열
- Executive Summary의 수치도 예외 없음 (본문 어딘가의 Source와 연결되어야 함)
