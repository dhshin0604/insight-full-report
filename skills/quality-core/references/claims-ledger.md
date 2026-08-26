# claims-ledger.md — Claims Ledger 원장 규율 v0.1

> 목적: 본문의 **모든 사실 주장(claim)** 을 출처와 1:1로 묶어, 검증되지 않은
> 수치·고유명사·인용이 최종 산출물에 남지 못하게 한다.

## 1. 스키마 (claims.json)

작업 디렉터리 루트에 `claims.json`으로 저장:

```json
{
  "topic": "주제 슬러그",
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

`kind`: `numeric`(수치) / `event`(사건) / `quote`(인용) / `relation`(고유명사 간 관계).
`method`: `web`(웹 확인) / `source-doc`(소스 원문) / `calc`(계산·외삽).

## 2. 등록 대상 (하나라도 해당하면 등록)

- 수치: 금액, 비율, 성장률, 사용자 수, 연도별 실적, 순위
- 사건: 출시일, 인수합병, 발표, 규제 시행
- 인용: 인물 발언, 보고서 문구
- 고유명사 간 관계: "A사가 B를 인수", "C 모델이 D 벤치마크 1위"

## 3. status — 3종만 허용

| status | 의미 | 본문 처리 |
|---|---|---|
| `verified` | 소스 원문 또는 웹에서 직접 확인 | 그대로 사용 + Source 표기 |
| `estimate` | 직접 확인 불가 — 계산/외삽/추정 | 본문에 반드시 `추정`(KR)/`est.`(EN) 표기 + 산출 근거 |
| `removed` | 검증 실패·모순 | **본문에서 삭제** — 잔존 시 게이트 FAIL |

## 4. 5대 검증 규칙 (작성 시점에 적용)

1. **소스에 없는 수치를 만들어내지 않는다.** 수치가 없으면 수치 없이 서술하거나
   estimate로 등록하고 산출 근거(method=calc, note)를 남긴다.
2. **기억으로 쓰지 않는다.** 모델 사전지식의 수치·날짜는 반드시 WebSearch/WebFetch로
   재확인 후 verified 처리. 확인 실패 시 estimate 또는 removed.
3. **단위·기간·환율 정합.** 환산 기준을 note에 기록. YoY/QoQ, 회계연도(FY) 차이를 본문에 명시.
   환율은 임의 가정 금지 — 실제 조회값 또는 명시적 estimate.
4. **두 소스가 충돌**하면 본문에 병기하거나 보수적 값 채택 + note 기록.
5. **사실과 해석의 분리.** 분석·전망은 claim이 아니라 의견 — "~로 해석됨",
   "~할 가능성이 큼"으로 쓴다. 의견을 사실 문형("~이다/~임")으로 단정하지 않는다.

## 5. 검증 실행 — 두 가지 모드

### 5-A. 단일 컨텍스트 모드 (기본)
1. 본문에서 claim 후보를 전수 추출해 claims.json과 대조 (누락분 등록)
2. verified가 아닌 claim을 하나씩 WebSearch/WebFetch/소스 재독으로 확인
3. 확인 실패 → status=removed + 본문 해당 문장 수정/삭제
4. **회의 패스**: "비평가 모자"를 쓰고 verified 판정 표본을 재확인 (false-verified 차단)

### 5-B. 서브에이전트 fan-out 모드 (claim 15개 이상 권장)
- 추출 에이전트 1개가 claim 목록 추출
- claim **묶음(5~10개)당 검증 에이전트** 1개 fan-out — 각자 깨끗한 컨텍스트에서 판정
  (self-preferential bias 차단)
- **skeptic 에이전트** 1개가 verified 표본을 재감사
- 결과를 claims.json으로 합산 → removed 반영해 본문 수정

## 6. 기계 대조 (lite)

MD/텍스트 대상은 `verify_claims_lite.py`로 본문 ↔ 원장 정합을 대조:

```bash
python3 references/verify_claims_lite.py --claims claims.json --text 대상문서.md
```

검사 항목: NUM_UNREG(원장 미등록 유의미 수치), REMOVED_LEAK(removed 잔존),
EST_UNMARKED(추정 표기 누락 estimate), NO_URL(verified의 출처 부재 — 경고).
연도 단독(1900~2099)과 4자리 미만 사소한 수는 휴리스틱으로 제외되는 **경량판**이므로,
최종 판단은 사람이 리포트를 읽고 내린다.

## 7. Source 표기 의무

수치가 밀집한 절 끝 또는 문서 말미에 출처 섹션을 두고, claims.json의 source와
정합시킨다. 슬라이드형 산출물이면 해당 슬라이드에 Source 줄을 단다.
