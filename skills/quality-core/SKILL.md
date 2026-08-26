---
name: quality-core
description: |
  신동형 공통 품질 코어 v0.1 — 어떤 문서·초안·보고서든 신동형 인사이트의 5대 품질 장치(Claims Ledger 사실 검증, So-What 통찰 강제, 문형·표기 규율, 16점 judge 채점, 재시도≤3회 루프)를 적용해 검증·개선한다. 산출물 형식 무관(MD·텍스트·Word 초안·이메일·타인이 쓴 보고서). 4종 정본 문서 생성은 본 스킬이 아니라 generate-full-report가 담당하며, 본 스킬은 '코어만 떼어낸' 범용 검증기다.
  Triggers (한국어): 품질 코어, 품질 코어 적용, 품질 검증, 퀄리티 체크, 이 초안 검증해줘, 팩트체크 게이트, claims 검증, 수치 검증해줘, So-What 점검, 인사이트 점검, 16점 채점, 루브릭 채점, 반론 점검, 딥체크만.
  Triggers (English): quality core, verify this draft, factcheck gate, claims ledger check, so-what review, rubric scoring, deep verification only.
---

# 공통 품질 코어 v0.1 — 범용 품질 검증·개선 스킬

> 신동형 인사이트 공정의 심장부(품질 코어)만 떼어내 **어떤 문서에든** 적용한다.
> 핵심 사상: **품질은 모델의 성실함에 부탁하는 것이 아니라, 원장과 게이트로 강제하는 것이다.**

## 🚨 GATE 0 — 즉시 중단 체크

다음 중 하나라도 해당하면 **STOP** 후 본 SKILL.md를 처음부터 다시 읽기:

1. **기억(사전지식)의 수치·날짜·사건을 검증 없이 본문에 쓰려 했다** → STOP. WebSearch/WebFetch/소스 재독으로 확인 후 claims.json 등록.
2. 소스에 없는 수치를 그럴듯하게 만들어 채우려 했다 → STOP. 수치 없이 서술하거나 estimate 등록 + `추정` 표기.
3. claims.json 없이 검증 판정("확인됨")을 내리려 했다 → STOP. 원장이 없으면 검증도 없다.
4. 자기가 쓴 초안을 자기 기준으로 후하게 채점하려 했다 → STOP. "비평가 모자"를 쓰거나 별도 컨텍스트(서브에이전트)로 채점.
5. 4종 정본 문서(Word KR/EN + PPTX KR/EN) 생성 요청이다 → STOP. 본 스킬이 아니라 `generate-full-report`로 핸드오프.
6. 필수 reference를 한 개도 읽지 않고 작업을 시작했다 → STOP. 아래 GATE 1 수행.

## 🛑 GATE 1 — 필수 읽기 (MANDATORY READS)

트리거 시 **첫 행동은 반드시** 아래 4개 파일을 Read로 모두 읽는 것:

```
1. references/claims-ledger.md   ← 원장 스키마 · 3-status · 5대 검증 규칙
2. references/so-what.md         ← So-What 사다리 · 반론 내성 · 3렌즈 · 전망 규칙
3. references/quality-rubric.md  ← 8기준 16점 채점표 · judge 출력 형식
4. references/style-rules.md     ← 문형·표기 규율 (사실↔해석, 추정 표기, 출처)
```

보조 도구: `references/verify_claims_lite.py` — MD/텍스트 대상 경량 기계 대조 스크립트.

## 🚫 ANTI-DRIFT — 절대 금지

| ❌ 금지 | ✅ 대신 |
|---|---|
| 기억의 수치를 그대로 사용 | 웹/소스 확인 후 verified 등록 |
| 소스에 없는 수치 생성 | 수치 없이 서술 또는 estimate + `추정` 표기 + 산출 근거 |
| removed claim을 본문에 잔존 | 해당 문장 수정·삭제 (잔존 = FAIL) |
| 비교축 없는 절대값 수치 | YoY/경쟁사/시장평균 중 1개 동반 |
| 사실과 해석을 같은 문형으로 단정 | 사실 "~임" / 해석 "~로 해석됨 · ~할 가능성이 큼" |
| KEY MESSAGE를 사실 나열(L1)로 | So-What L2 이상, 챕터당 1개는 L3 |
| 핵심 주장을 반론 없이 일방 서술 | 가장 강한 반론 1개를 본문에서 처리 |
| 자기 초안 자기 채점(관대화) | 비평가 모자 또는 별도 critic 컨텍스트 |
| 채점 없이 "품질 좋음" 총평 | 16점 루브릭 채점표 + 근거 1문장씩 |
| 무한 수정 루프 | 재시도 상한 3회 → NEEDS_REVIEW로 사람에게 |

## 사전 확인 (AskUserQuestion)

1. **대상**: 검증할 초안/문서 (파일·붙여넣기·URL)
2. **모드**: A=사후 검증(기존 초안 검증·수정, 기본) / B=작성 동행(초안 작성부터 코어 규율 적용)
3. **소스**: 대상의 근거 자료 제공 여부 (없으면 웹 검증 의존을 명시)
4. **강도**: 기본=전수 검증 / 사용자가 "빠르게·경량" 명시 시에만 핵심 claim 위주

## 워크플로 (6 Phase)

### Phase 1 — 원장 개설
대상 문서에서 사실 주장(claim)을 **전수 추출**해 `claims.json` 등록. 등록 대상: 수치(금액·비율·성장률·순위), 사건(출시일·인수합병·규제), 인용, 고유명사 간 관계. 스키마는 claims-ledger.md §1.

### Phase 2 — Deep Verification
verified가 아닌 claim을 하나씩 WebSearch/WebFetch/소스 재독으로 확인:
- 확인 성공 → `verified` (+source/url)
- 합리적 계산·외삽 → `estimate` (+method/note, 본문 `추정`/`est.` 표기)
- 확인 실패·모순 → `removed` (**본문 해당 문장 수정/삭제**)

이후 **회의 패스**: 비평가 모자를 쓰고 verified 표본을 재확인. 대형 작업은 claim 묶음(5~10개)당 검증 서브에이전트 fan-out + skeptic 재감사(claims-ledger.md §3).

### Phase 3 — So-What 패스
핵심 문장(제목·헤드라인·단락 첫 문장)을 사다리에 올려 판정: L1(사실 나열)이면 L2+ 로 재작성. 챕터/섹션당 1개 이상 L3 도달, 핵심 주장마다 반론 1개 처리, 핵심 사건은 3렌즈 검토, 전망은 조건문+estimate. 상세는 so-what.md.

### Phase 4 — 문형·표기 패스
사실↔해석 문형 분리, estimate `추정` 표기, 수치 밀집부 출처 표기, 비교축 동반 여부를 전수 점검. style-rules.md 적용. (선택) 산문체 요청 시 개조식 → analyst 산문 전환.

### Phase 5 — judge 채점
`quality-rubric.md`의 8기준(각 0·1·2점, 16점 만점)으로 채점하고 기준별 근거 1문장 기록. **합격 = 총점 ≥12 그리고 0점 없음.** 가능하면 작성자와 다른 컨텍스트(critic 서브에이전트)가 채점, 단일 컨텍스트면 비평가 모자 — 특히 #8(인사이트 깊이)을 후하게 주지 않는다. MD/텍스트 대상이면 `verify_claims_lite.py`로 기계 대조 병행.

### Phase 6 — 재시도 루프와 출구
불합격이면 0~1점 기준의 fixes만 패치 후 Phase 5 재채점. **상한 3회** — 초과 시 남은 문제를 `NEEDS_REVIEW`로 사용자에게 보고하고 멈춘다.

## 산출물 (검증 보고)

1. **수정본** (모드 A: 수정 반영본 / 모드 B: 완성 초안)
2. **claims.json** + claims 통계 (총/verified/estimate/removed)
3. **채점표** (8기준 점수 + 근거) 및 재시도 이력
4. removed·수정 내역 목록 (무엇을 왜 고쳤는지)

## ✅ 최종 자기 점검

- [ ] references 4개를 모두 읽고 시작했다
- [ ] 본문의 모든 수치·사건·인용이 claims.json에 등록되어 있다
- [ ] removed claim이 본문에 남아 있지 않다
- [ ] estimate에 `추정`/`est.` 표기가 있고 산출 근거가 note에 있다
- [ ] 기억의 수치를 웹 확인 없이 쓰지 않았다
- [ ] 사실과 해석이 문형으로 구분된다
- [ ] 핵심 문장이 So-What L2 이상, 섹션당 1개는 L3
- [ ] 핵심 주장마다 반론 1개 이상 처리
- [ ] 16점 채점표가 있고 합격선(≥12, 0점 없음)을 확인했다
- [ ] 재시도 3회 초과분은 NEEDS_REVIEW로 보고했다

체크박스 중 하나라도 비어 있으면 결과물은 품질 코어를 통과한 것이 아니다.
