# 보고서 하네스 v1.0

**큰 보고서를 여러 에이전트로 만들 때의 구조 : 정본, 고삐, 원장, 게이트, 분업, 루프, 사람 확인**

> 쓰는 때 : ① 보고서 한 편을 돌릴 때(3절) ② 새 보고서 스킬·플러그인을 만들 때(4절, 6절, 7절) ③ 기존 스킬을 고칠 때(10절)
> 쓰는 법 : 작업을 시작할 때 이 파일을 먼저 읽고, 해당 절의 순서를 그대로 따름
> 표기 : 「(권장)」은 이 문서가 정리한 운영 규칙으로, 저장소의 스크립트가 아직 강제하지 않는 것임
> 예시 : 이 문서의 대상, 기관, 수치 예시는 모두 가상임(「가상의 A사」, 「예시 도시 B시」)

---

## 0. 하네스란

- 하네스 = 모델(두뇌)에 채우는 마구임. 지킬 것을 프롬프트의 당부로 두지 않고 파일, 스크립트, 원장, 확인 지점으로 바깥에 꺼내 둔 장치임
- quality-core 스킬의 문장 그대로 「품질은 모델의 성실함에 부탁하는 것이 아니라, 원장과 게이트로 강제하는 것이다」임. 어느 모델이 돌려도 같은 양식과 같은 검증을 거친 산출물이 나와야 함
- 이 저장소의 이동 : 「한 컨텍스트의 성실함」 → 「빌드 외부화」 → 「원장과 게이트」 → 「작성자와 검증자의 분리」 → 「사람 확인 지점」. 품질을 지키는 힘을 「잘 쓴 프롬프트」에서 「빠져나갈 수 없는 구조」로 옮겨 온 과정임

## 1. 이 저장소의 버전 이력

| 버전 | 형태 | 산출물 | 새로 들어간 하네스 요소 |
|---|---|---|---|
| v0.5 | 단일 컨텍스트 스킬 (generate-full-report) | Word KR/EN + PPTX KR/EN 4종 | 정본 템플릿 하나를 복사·치환, `verify_toc.py`(목차와 본문 대조), 산문체 규칙, 고정 7챕터 |
| v0.9 | 원장, 게이트, 동적 워크플로 | 4종 + `claims.json` + `gate_report.json` | Claims Ledger(verified, estimate, removed), 4중 게이트(`gate_report.py` : toc, content, claims, judge), 재시도 3회, 동적 워크플로(classify 로 챕터 5~9 가변, fan-out, deep verification, critic, loop-until-done), So-What 사다리 |
| v0.9.1 | 헤딩 자동 번호 | 위와 같음 | Word 헤딩 `H1C`/`H2C` 자동 번호 + HEADNUM 게이트 |
| v0.9.2 | 작성자 정보 분리 | 위와 같음 | `profile.json` + `apply_profile.py`, 자리표시가 남으면 빌드 중단 |
| v1.0 | 이미지 덱, 보고서 하네스 | MD 토의본 → Word(JSON 원고) + 이미지 덱(PDF, PPTX, PNG zip) | image-deck 스킬(HTML 5-Zone 렌더, 자동 QA, 팔레트 검사), report-harness 스킬(이 문서, 브리프 뼈대, `selfcheck.py`, `assemble.py`, `build_docx.js`), 공용 금지어 사전 `lexicon.json`, 사용자 확인 지점, 독립 검토 |

- 덱 만드는 방식도 「OOXML 템플릿 편집(.pptx)」에서 「HTML 5-Zone 렌더 → PNG → PDF, PPTX(쪽마다 이미지 한 장)」으로 옮겨 왔음. 편집 가능한 PPTX 가 필요하면 generate-full-report 의 OOXML 경로를 씀
- 고삐(GATE 0, GATE 1 필수 읽기와 셀프 체크, ANTI-DRIFT 표)는 generate-full-report SKILL.md 에 들어 있음
- quality-core 스킬(v0.1)은 v0.9.x 파이프라인의 품질 장치 다섯 가지(원장, So-What, 문형·표기, 16점 judge, 재시도 3회)만 떼어낸 범용 코어임. report-harness 는 그 위에 분업, 사람 확인, 원고 → Word 빌드를 더한 것임

## 2. 하네스 7요소

| # | 요소 | 하는 일 | 실물(이 저장소) | 막는 실패 |
|---|---|---|---|---|
| ① | 정본 | 모델이 새로 짓지 않고 복사해 채우는 틀 | `build_*.template.*`, `TEMPLATE.pptx`, `build_docx.js`, `deck_core.py`, `content-schema.md`, 브리프 뼈대, 작성자 문체 정리본 | 양식 표류, 편마다 다른 결과 |
| ② | 고삐(SOFT) | 할 것과 하지 말 것을 문장으로 고정 | SKILL.md 원칙, GATE 0, ANTI-DRIFT 표, 셀프 체크 문답, 브리프 | 규칙 망각(goal drift) |
| ③ | 원장 | 모든 사실을 출처와 1:1 로 묶음 | `claims.json`, 연결 원장, `research/D<n>_*.md`, 용어 사전 | 환각, 기억 수치 |
| ④ | 게이트(HARD) | 규칙 위반을 스크립트가 잡아 멈춤 | `selfcheck.py`, `verify_toc/content/claims/lang_purity.py`, `render_all` QA, `gate_report.py` | 알고도 어김 |
| ⑤ | 분업 | 작성자와 검증자를 떼고 깨끗한 컨텍스트로 나눔 | 브리프 파일, 워크플로 템플릿 | 중도 포기(laziness), 자기 편애(self-bias) |
| ⑥ | 루프 | 통과할 때까지 고치되 상한을 둠 | 재시도 3회 이하, critic 재작성 2회 이하, NEEDS_REVIEW | 무한 수정 |
| ⑦ | 사람 확인·학습 | 되돌리기 비싼 지점에서 멈추고, 교정을 다음 편 규칙으로 올림 | 착수 질문, MD 토의본과 토의 안건, 「겪은 문제와 대응」, 버전 이력 | 잘못된 방향을 끝까지 끌고 감 |

## 3. 생산 하네스 : 보고서 한 편이 도는 순서 (P0~P8)

```
P0 착수 → P1 정본 로드 → P2 조사(갈래 병렬) → P3 2차 검증 → P4 MD 토의본
                                                          ↓
                                                [사용자 확인 : 멈춤]
                                                          ↓
P8 전달 ← P7 독립 검토 ← P6 게이트·재시도 ← P5 빌드(그림 → Word ∥ 덱)
```

| 단계 | 하는 일 | 산출 | 넘어가는 조건 |
|---|---|---|---|
| P0 착수 | 착수 질문을 한 번에 물음(부록 A) : 범위, 진행 순서, 산출 형식, 양식 원본. 기존 원고 개정이면 파일보다 토의부터 | 작업 폴더, 결정 메모 | 범위, 순서, 형식 확정 |
| P1 정본 로드 | SKILL.md 와 필수 references 읽기, 작성자 문체 정리본·선호 규칙(있으면) 읽기, 직전 편 파일을 `ref/` 에 둠 | | 셀프 체크 문답 통과 |
| P2 조사 | 공통 `BRIEF.md` → 갈래마다 에이전트 하나. WebSearch, WebFetch 만, 갈래당 검색 30회 안팎, 아는 URL 은 바로 열람 | `research/D<n>_*.md` | 행마다 출처, 날짜, URL, 태그 |
| P3 2차 검증 | 조사하지 않은 에이전트가 핵심 수치, 날짜, 소재(안/밖), 단계, 금액 층위를 원문으로 다시 확인 | 판정 5종(확인, 수정, 상충 유지, 부재 유지, 미확인) | 바뀐 값은 MD 부록에 기록 |
| P4 MD 토의본 | `INTEG_BRIEF.md`(고정 용어, 채택값, 문체, 블록 배정) → 블록 작성 → 통합 → 검토 에이전트 → 수정 → 전달. 끝에 번호 붙은 토의 안건과 잠정안 | `{대상}_{시리즈}_{단계}_v0.1.md` | **사용자 확인 전에는 다음으로 가지 않음** |
| P5 빌드 | 더미 원고로 파이프라인 먼저 시험 → 그림 담당이 먼저 렌더(`figs/_DONE`) → Word 원고(`BRIEF_WORD.md`)와 덱 파트(`BRIEF_DECK.md`) 병렬 | `content_*.py`, 그림·쪽 PNG | 파트별 자체 QA OK |
| P6 게이트 | selfcheck PASS → assemble → build → `gate_report.py` pass → PDF 로 바꿔 쪽 그림 확인. 실패분만 패치, 상한 3회 | `gate.json` | pass: true, 넘침 0 |
| P7 독립 검토 | 만들지 않은 검토 에이전트가 MD, 원문과 대조(`REVIEW.md`). 확인한 오류만 최소 수정, 수치는 원값으로 독립 재계산 | 수정 목록 | 미해결 0, 남으면 NEEDS_REVIEW |
| P8 전달 | 파일 전달(docx, PDF, PPTX, PNG zip, MD), 연결 폴더가 있으면 거기도 저장 | | 끝 메시지는 짧게(부록 C) |

- 분석 → 진단 → 제언은 현황 확인 뒤 단계마다 P2~P8 을 다시 돎. 단계마다 MD 토의본과 확인을 둠. 사용자가 한 번에 요청하면 단계 확인을 생략함
- 토의 안건은 번호와 잠정안을 붙여 냄. 사용자는 「잠정안대로 확정」 한 줄로 넘길 수 있음
- 수정 요청이 오면 문구만 바꾸지 않고 제목, 논지, 구조에 미치는 영향을 먼저 보고 반영함. 국소 수정이 쌓여 제목과 논지가 어긋나는 것을 막는 규칙임
- 원고 교정은 내용이 확정될 때까지 MD 로 주고받고, Word 는 확정 뒤에 만듦
- 작업 공간은 초기화될 수 있으므로 단계마다 산출물을 전달해 둠. 긴 작업은 인계 브리프(handoff brief)와 원장을 함께 남김

## 4. 제작 하네스 : 새 보고서 스킬·플러그인을 만드는 순서 (M1~M10)

| 단계 | 하는 일 | 예 (가상) |
|---|---|---|
| M1 선례 | 사용자가 만족한 산출물 2편 이상, 구조가 되풀이된 것을 정본 후보로 삼음 | 「예시 도시 A시 현황편」과 「예시 도시 B시 현황편」의 장 구성이 같음 |
| M2 결정 수집 | 그 편들에서 사용자가 확정한 교정과 토의 안건 결정을 모음 | 「점수는 모두 뺀다」, 「지자체는 연결자로만 쓴다」 |
| M3 정본 추출 | 장·절·쪽 구성, 측정값(좌표, 색, 글자 크기), 헬퍼 코드, 브리프 뼈대를 떼어냄 | `content-schema.md`, 5-Zone 측정값, `briefs/` |
| M4 규칙화 | 결정을 원칙(어기면 다시 씀), 금지어, ANTI-DRIFT 표로 씀 | SKILL.md 1절, `lexicon.json` |
| M5 게이트화 | 기계로 잡히는 규칙은 스크립트로 내림 | `selfcheck.py`, `verify_*` |
| M6 SKILL.md | 6절 골격으로 씀 | |
| M7 시범 실행 | 더미 원고로 빌드·게이트를 먼저 통과시키고 작은 대상 1편을 돌림 | `references/examples/` 로 PASS 확인 |
| M8 사용자 검토 | 스킬을 보이고 확인을 받은 뒤 본 작업 | 「스킬로 만들어 검토한 뒤 진행」 |
| M9 패키징 | 플러그인 구조, plugin.json, README, 버전, 배포본 | 7절 |
| M10 운영 학습 | 편마다 「겪은 문제와 대응」과 사례 파일을 쌓고 버전을 올림 | 10절 |

- 시리즈 작업은 프롬프트를 둘로 나눔 : 시리즈 공통 「표준 프롬프트」 + 대상별 「착수 프롬프트」

## 5. 분업 하네스 : 에이전트 역할과 브리프

### 5-1. 역할

| 역할 | 맡는 일 | 지킬 것 | 브리프 |
|---|---|---|---|
| 오케스트레이터 | 브리프 작성, 배정, 통합, 게이트 실행, 사용자 소통 | 직접 쓰기보다 배정과 대조, 확인 지점 관리 | (SKILL.md) |
| 조사 D1~Dn | 주제 축별 1차 조사 | 검색 예산, 출처 태그, 못 찾으면 「미발견」 | `BRIEF.md` |
| 2차 검증 S1~Sn | 다른 갈래의 핵심 값 재확인 | 조사한 에이전트와 다른 에이전트 | `BRIEF.md` 5절 |
| 블록 작성 B1~Bn | MD 토의본 블록 | 채택값만 씀, 블록별 수치 표 | `INTEG_BRIEF.md` |
| 원고 W1~Wn | Word 장 원고(`content_chN.py` + CLAIMS) | 자기 장의 claim 을 함께 등록, selfcheck PASS | `BRIEF_WORD.md` |
| 그림 FIG | Word·덱 공용 그림을 먼저 렌더 | 숫자는 MD 값 그대로, 끝나면 `_DONE` | `BRIEF_FIG.md` |
| 덱 P1~Pn | 파트별 쪽 렌더 | `render_all` QA OK, PNG 한 장씩 육안 확인, 금지어 0 | `BRIEF_DECK.md` |
| critic | 16점 루브릭 채점 | 작성자와 다른 컨텍스트, 인사이트 깊이를 후하게 주지 않음 | quality-core `quality-rubric.md` |
| skeptic | verified 표본 재감사 | 잘못된 verified 차단 | factcheck-pipeline.md |
| 검토 R | 산출물을 MD, 원문과 대조 | 확인한 오류만 최소 수정 | `REVIEW.md` |
| 독립 재계산 N | 수치 쪽을 처음부터 다시 셈 | 원값을 브리프에 넣고 산출물을 믿지 않음, 자기 스크립트로 계산 | `REVIEW.md` 3절 |

- 검토를 나눠 맡기면 작성자 혼자 볼 때 지나친 오류가 걸러짐. 큰 보고서일수록 검토 에이전트를 장 묶음, 파트 묶음별로 둠

### 5-2. 브리프 규칙

- 규칙을 프롬프트에 길게 쓰지 않음. 브리프 파일 경로를 주고 「처음부터 끝까지 읽고 그대로 따를 것」으로 지시함
- 브리프 종류 : `BRIEF.md`(조사 공통), `INTEG_BRIEF.md`(통합), `BRIEF_WORD.md`, `BRIEF_DECK.md`, `BRIEF_FIG.md`(빌드), `REVIEW.md`(검토). 뼈대는 `references/briefs/`
- 출력 계약 : 파일 경로, 한 줄 요약, 핵심 셈 5개, 원문과 2차 출처 구분, 상충, 접근하지 못한 원문, 검색·열람 로그
- 출처 제한 : 1차 출처(공식 사이트, 공시, 정부·기관 문서, 표준기관)를 먼저 보도록 지정함. 못 찾으면 추정하지 말고 「미발견」으로 보고함

### 5-3. 동적 워크플로 패턴 (generate-full-report Phase D)

| 패턴 | 단계 | 막는 실패 |
|---|---|---|
| classify-and-act | 소스 깊이로 챕터 수(5~9), 모델, 시각화 계획 결정 | 고정 구조에 억지로 채우기 |
| fan-out-and-synthesize | 챕터당 에이전트 하나로 초안 → Executive Summary 합성 | 중도 포기, 규칙 망각 |
| deep verification | claim 5~10개 묶음마다 검증 에이전트 + skeptic | 환각 |
| adversarial verification | 다른 critic 이 루브릭 채점, 불합격 챕터만 재작성(2회 이하) | 자기 편애 |
| loop-until-done | 게이트 실패분만 패치·재빌드(3회 이하) → NEEDS_REVIEW | 무한 루프 |

- 소스 3개 이상이거나 챕터 8개 이상이 예상되면 워크플로 모드를 먼저 제안함. 동시 에이전트는 16개 이하

### 5-4. 운영 메모

- rate limit(429)이 나면 같은 지시로 모델만 바꿔 다시 실행함
- 세션 웹검색에는 한도가 있음(예 : 약 200회). 갈래 수로 나눠 갈래당 예산을 브리프에 적음. 예산을 적지 않으면 앞 갈래가 다 써서 뒤 갈래가 못 찾음
- 순서가 필요한 병렬 작업은 완료 표시 파일로 맞춤(그림 `figs/_DONE` → 덱)

## 6. SKILL.md 표준 골격

```markdown
---
name: "{영문-소문자-하이픈}"
description: "{무엇을, 어느 양식으로} 만들 때 사용. {진행 순서} → {산출물}. {쓰지 말 때 한 구절}."
---

# {스킬 이름}

> 선례 : {정본으로 삼은 편 2개 이상, 버전, 날짜, 분량}
> 결과물 : ① MD 토의본 ② {Word} ③ {이미지 덱 PDF, PPTX, PNG zip}
> 순서 : 착수 질문 → 조사 → MD 전달 → 사용자 확인 → 빌드 → 게이트 → 검토 → 전달

## 0. GATE 0 : 바로 멈출 것
- {하려 한 일} → STOP. {대신 할 일}

## 1. 원칙 (어기면 다시 씀)
- {사용자가 확정한 결정을 원칙 문장으로}
- 금지어 : {8-3 갈래 중 해당하는 것}

## 2. GATE 1 : 필수 읽기와 셀프 체크
- 필수 : references/{...}.md, 작성자 문체 정리본
- Q1. {틀리기 쉬운 것} / 정답 : {...}

## 3. 절차
3-1 착수 질문 / 3-2 조사 n갈래(BRIEF.md, 검색 예산) / 3-3 2차 검증 /
3-4 MD 토의본(토의 안건 + 잠정안) → 확인 대기 / 3-5 빌드(더미 시험 → 그림 → Word ∥ 덱) /
3-6 게이트·재시도 3회 이하 / 3-7 독립 검토 / 3-8 전달

## 4. MD 구조      ## 5. Word 구조·문체·게이트 함정
## 6. 덱 구조·측정값·헤드라인 규칙      ## 7. 그림 규격
## 8. ANTI-DRIFT 표 (금지 | 대신)
## 9. 겪은 문제와 대응
## 10. 최종 자기 점검 (체크박스)
## 부록 : 헬퍼 코드, selfcheck, 조립, 렌더러, 묶기, 브리프 뼈대
```

- description 은 「언제 쓰는지 + 무엇을 만드는지 + 순서」를 한두 문장으로 씀. 트리거 단어를 길게 늘어놓거나 「EXCLUSIVE, 무조건 우선」 문구를 넣으면 다른 스킬과 부딪힘 (권장)
- 필수 읽기는 적게 둠(4~7개). 나머지는 「필요할 때 읽기」로 내림

## 7. 플러그인 패키징

### 7-1. 폴더

```
{plugin-name}/
├─ .claude-plugin/plugin.json
├─ README.md                    무엇을 하나, 사용 예, 구성, 산출물, 버전 이력
├─ skills/{skill-name}/
│  ├─ SKILL.md
│  └─ references/               정본 템플릿, 루브릭, 프레임워크, 게이트 스크립트, 사례 파일
├─ agents/                      (선택) 역할 정의 .md : 조사, 검증, 검토 (권장)
└─ hooks/hooks.json             (선택) 게이트 강제용 (권장)
```

- 플러그인 안의 경로는 스크립트 위치 기준이나 `${CLAUDE_PLUGIN_ROOT}` 로 씀. 절대 경로를 박지 않음

### 7-2. plugin.json

```json
{
  "name": "{plugin-name}",
  "version": "1.0.0",
  "description": "{한 문장 : 무엇을 만들고 어떤 장치가 들어 있는지}",
  "author": { "name": "{저자}" },
  "keywords": ["{도메인}", "report", "harness"],
  "license": "MIT"
}
```

### 7-3. 버전 (권장)

- `plugin.json` 의 version, SKILL.md 제목의 버전, README 이력 첫 줄을 같게 둠
- 구조·산출물이 바뀌면 minor, 규칙·게이트 보완이면 patch. README 이력은 한 줄에 무엇을 왜 바꿨는지 씀

### 7-4. 배포본

- 원본과 배포본을 나눌 때 개인정보(연락처, 저자명, 저장 경로, 로고)는 `references/profile.json` 으로 빼고 템플릿에는 자리표시만 남김
- 빌드는 자리표시가 남으면 멈춤(`apply_profile.py`, `build_docx.js` 종료코드 2). 그래서 배포본에 개인 연락처가 남지 않음
- profile.json 찾는 순서 : 환경변수 `PROFILE` → 작업 폴더 `./profile.json` → 스킬 자신의 `references/profile.json` → 형제 스킬의 `references/profile.json`

### 7-5. 의존과 경로

- 다른 스킬의 스크립트를 쓸 때(report-harness → generate-full-report 의 `gate_report.py`) 경로를 박지 않고 형제 경로를 먼저 찾은 뒤, 없으면 「게이트 없음」으로 분명히 보고하고 설치를 안내함
- 저장·전달은 환경을 보고 고름 : ① 연결된 사용자 폴더 ② 작업 공간 + 파일 전달 ③ 마운트 폴더. 특정 환경 전용 경로와 도구는 그 환경용으로 표시함 (권장)
- 플러그인 폴더가 읽기 전용이면 템플릿을 쓰기 가능한 작업 폴더에 복사한 뒤 빌드함

## 8. 공통 고삐 사전

### 8-1. 사실

| 규칙 | 어디서 강제 |
|---|---|
| 기억(사전지식)의 수치·날짜는 웹·원문 확인 전에 쓰지 않음 | GATE 0, quality-core |
| claim 상태는 verified, estimate, removed 셋만. estimate 는 본문에 「추정」, removed 가 남으면 FAIL | `verify_claims.py`, `selfcheck.py` |
| 태그 : 「단독」 「상충」(둘 다 적음) 「미확인」 「2차」 「(계산)」 「문서 미발견」 「문서 미기재」. 「」 안에는 원문 문장만 | `BRIEF.md` |
| 「없음」에는 조사 범위를 붙임 : 「이번 조사 범위에서 문서 미발견」 | `BRIEF.md` |
| 금액 층위(계획, 예산안, 선정, 집행, 총사업비, 재원별)를 문장에 적고, 기준이 다른 숫자는 한 문장에서 비교하지 않음 | `BRIEF.md`, 검토 |
| 가정값(환율 등)을 쓰지 않음. 사용자 확인을 받거나 그 열을 뺌 | GATE 0 |
| 「표준」 「원칙」은 누구의 것인지 밝힘(어느 기관의 어느 문서) | `BRIEF.md`, 검토 |
| 정부·기관 문서는 적힌 이름, 금액, 단계만 씀. 언론·정치권 표현과 구분하고 발행 기관 관점에 기울지 않음 | `BRIEF.md`, `INTEG_BRIEF.md` |
| 수치에는 비교축 하나(전년, 다른 대상, 평균) | quality-core so-what |
| 사실은 「~임」, 기관 발표는 「~밝힘」, 해석은 「~로 해석됨, ~보임」, 전망은 조건문 | quality-core style-rules |
| 개인 이름과 연락처는 적지 않음(기관, 회사, 국가만) | `BRIEF.md` |
| 점수·등급 대신 셀 수 있는 사실(건수, 비율, 시간, 대수, 금액)로 좌표를 잡음 (권장) | 원칙 |

### 8-2. 문체 (산출물별)

| 산출물 | 문체 | 날짜 표기 |
|---|---|---|
| MD 토의본 | 명사형 종결(~임, ~음), 표 위주 | 2026-10-12 |
| 덱 헤드라인 | 명사형 1~2문장, 90~130자, 2줄 이내. 첫 문장 = 사실·구조, 둘째 문장 = 판정·재정의(현황 단계는 보완 사실) | 2026.10.12 |
| 덱 본문 | 컴포넌트(표, 카드, 흐름, 수치 타일)만 쓰고 산문 없음, ☞ 정리 줄 | 2026.10.12 |
| Word 보고서 | analyst 합니다체 산문, 절마다 KEY MESSAGE, bullet 없음 | 2026년 10월 12일 |
| 기고·칼럼 | 필자 문체 정리본을 따름 | |
| 영문 | 줄표 없음(콜론, 세미콜론은 씀) | October 12, 2026 |

- 대필 문장은 필자의 문체 정리본(헤드라인 구조, 자주 쓰는 수사, 종결 어미)을 먼저 읽고 씀
- 발주처 명의 보고서는 발주처가 부담스러워하는 주어와 표현을 피함. 착수 질문에서 확인함

### 8-3. 금지어·금지 문형 (정본 : `lexicon.json`)

| 갈래 | lexicon 키 | 수준 |
|---|---|---|
| 과장 | `hype_hard` / `hype_soft` | 오류 / 경고 |
| 평가어(현황 단계) | `eval_terms` | status 모드에서 오류 |
| AI 티 문형 | `ai_tone` | 경고 |
| 가리킴 | `pointer` | 오류 |
| 자기 해설 | `self_commentary` | 오류 |
| 팀 고유 금지 표현 | `user_banned` | 오류 |
| 기호 | `bullets`, `dash` | bullet 오류, 줄표는 `dash.level`(en 오류, kr 경고. `selfcheck --strict` 면 오류) |

- 금지어는 `lexicon.json` 하나를 정본으로 두고 generate-full-report 와 report-harness 에 같은 사본을 둠. `selfcheck.py` 와 image-deck 의 `render_all` 이 이 파일을 읽음. 목록을 바꿀 때는 두 사본과, 같은 목록을 코드에 들고 있는 게이트 스크립트가 있으면 그것까지 함께 맞춤
- 사용자가 「맞지 않는다」고 한 표현은 `user_banned` 에 올림

### 8-4. 구조

- Word 헤딩 : 번호 장 「1. 」, 절 「1.1 」. 번호 없는 헤딩은 HEAD_EXEMPT 목록의 이름만(Executive Summary, 핵심 질문과 답변, 맺음말, 참고 자료, 핵심 키워드, 관점별). `build_docx.js` 가 번호를 붙이고 HEADNUM 게이트가 검사함
- Word 표 : 열 5개 이하, 폭 합 9026, 행 14개 이하, 셀 60자 이하. 그림 폭 630, 높이는 원본 비율
- 표지와 표지 그림은 같은 쪽, 표지에 출처 줄·해시태그 없음
- 덱 : 본문 넘침 0, 표 8행 이하, 파트 안 컴포넌트 3종 이상, 표만 연속 3장 금지, 출처 줄 2줄 이내, 글자 19px 이상
- 각 장은 자기 결론으로 끝내고 다른 장을 가리키지 않음

## 9. 게이트 체인

```
원고 selfcheck.py (PASS)
 → assemble.py (content.json + claims.json, 메타 claim Z001~Z004 자동)
 → build_docx.js (.docx)
 → gate_report.py : verify_content(규칙, 헤딩 번호) → verify_claims(수치-출처) → judge(있으면)
 → gate.json { pass, fixes[] }
 → 실패분만 패치·재빌드(상한 3회) → 넘으면 NEEDS_REVIEW 로 사람에게
덱   : render_all QA → PNG 한 장씩 육안 확인 → 금지어 0
Word : soffice 로 PDF 변환 → 쪽 그림 확인
```

| 스크립트 | 위치 | 잡는 것 |
|---|---|---|
| `selfcheck.py` | report-harness | 스키마, 원고 속 번호, bullet, 괄호 밖 한자·가나, 날짜 형식, 과장, 평가어, AI 티, 가리킴, 자기 해설, 줄표, 따옴표, 자리표시, 표 규격, 미등록 수치, 「추정」 없는 estimate, removed 잔존, claim id·status |
| `verify_toc.py` | generate-full-report | PPTX 목차 로마숫자와 본문 라벨 불일치 |
| `verify_content.py` | generate-full-report | 과장(HARD, SOFT), bullet, 한자 혼입, 출처 섹션, 헤딩 번호(HEADNUM) |
| `verify_claims.py` | generate-full-report | 미등록 수치, removed 잔존, 「추정」 없는 estimate, 잘못된 status, 출처 없음(경고) |
| `verify_lang_purity.py` | generate-full-report | KR 가나 0·한자 10 이하, EN 한자·가나 0 |
| `gate_report.py` | generate-full-report | 위 게이트와 judge 를 합쳐 pass, fixes[] |
| `render_all` (`deck_core.py`) | image-deck | 본문 넘침, 헤드라인 줄 수, 출처 줄 길이, 이미지 로드 실패, 작은 글자, 팔레트 대비 |
| `quality-rubric.md` | quality-core | 8기준 16점, 합격 = 12점 이상이고 0점 없음 |

- selfcheck 는 gate 와 같은 수치 규칙(연도 단독과 12 이하 정수 제외, 소수·%·큰 수는 등록)과 같은 금지어 사전을 씀. 그래서 selfcheck PASS 면 gate 의 content·claims 가 대개 통과함. 빌드가 만드는 번호는 assemble 이 메타 claim 으로 넣음
- 렌더 함정 : Word 미리보기에서 Malgun Gothic 이 없는 환경이면 fontconfig 에서 「Malgun Gothic」 「맑은 고딕」을 Noto Sans CJK KR 로 별칭 지정(문서 글꼴 선언은 그대로). Node 패키지는 `NODE_PATH="$(npm root -g)"`. PDF 묶기는 13.333×7.5in
- 게이트 함정 : 한자는 「(」 바로 뒤에서 시작할 때만 통과. 12를 넘는 수, 소수, %, 표준 번호는 claims 에 등록. 제목에 번호를 직접 쓰면 번호가 둘이 됨
- hook 은 게이트를 지시가 아니라 실행 단계에서 거는 방법임. `gate.json` 의 pass 가 없으면 전달을 막는 식 (권장)

## 10. 학습 루프 : 하네스가 자라는 방식

```
사용자 교정
 → 기록(작업 메모, 선호 규칙, 문체 정리본)
 → 다음 편 브리프에 반영
 → 두 편 이상 되풀이되면 SKILL.md 원칙·금지어로 올림
 → 기계로 잡히면 selfcheck·verify 로 내림
 → 버전 올림, README 이력, 「겪은 문제와 대응」
```

| 교정·사건 (가상 예) | 규칙으로 | 장치로 |
|---|---|---|
| 「점수는 모두 빼고 최대한 정량적으로」 | 좌표 근거는 셀 수 있는 사실만 | 원칙, 검토 |
| 「현황 보고서인데 제언이 섞였다」 | 현황 단계 분리, 판정·제언 없음 | `selfcheck --mode status`(평가어 오류) |
| 「문서에 없는 지정 표현이 전제로 쓰였다」 | 그 말은 문서에 있을 때만 | 토의 안건, 검토 |
| 조사 갈래가 검색 한도를 먼저 다 씀 | 갈래당 예산을 나눔 | `BRIEF.md` 2절 |
| 작업 공간 초기화로 파일 소실 | 단계마다 전달, 다음 편 시작 때 직전 편 파일을 다시 받음 | 착수 질문 4번 |
| 덱 날짜에 하이픈이 섞임 | 산출물별 날짜 형식 고정 | 렌더 전 정규식, selfcheck `dates` |
| 「AI가 쓴 티가 난다」 | AI 티 문형 금지, 필자 산문 패턴 유지 | `lexicon.json` `ai_tone` |
| 「이 표현은 맞지 않는다」 | 필자 언어로 다시 씀 | `lexicon.json` `user_banned` |
| 실험 옵션의 실측 결과가 기본값보다 나쁨 | 기본값 유지, 실험 옵션으로 내림 | README 이력 |

- 올리는 기준 (권장) : 같은 교정이 두 번 나오면 원칙(SOFT)으로, 같은 원칙이 두 번 어겨지면 게이트(HARD)로 올림

## 11. 다음 구조 (권장) : 공용 코어 + 도메인 팩

```
공용 코어
├─ gates/        selfcheck, verify_toc, verify_content, verify_claims, verify_lang_purity, gate_report
├─ lexicon.json  금지어·문형·표기 사전 하나
├─ rubric/       quality-rubric(16점), so-what, claims-ledger
├─ render/       deck_core.py(5-Zone HTML), 묶기(PDF, PPTX, PNG zip), build_docx.js(Word)
└─ briefs/       BRIEF, INTEG_BRIEF, BRIEF_WORD·DECK·FIG, REVIEW 뼈대

도메인 팩 (SKILL.md + 도메인 references 만)
├─ 현황 보고서 팩          지역·산업 현황편
├─ 진단 팩                기업·정책 분석, 진단, 제언
├─ 경쟁사 비교 팩          벤치마킹
└─ 일반 인사이트 팩        generate-full-report
```

- quality-core 가 「코어만 떼어낸」 첫 시도이고, v1.0 의 report-harness 와 image-deck 이 게이트 앞단(selfcheck, assemble), Word 빌더, 렌더러, 브리프 뼈대를 더했음. 도메인 팩은 프레임워크와 양식만 들고 다니면 됨
- 남은 일 : `gate_report.py` 와 `verify_*` 를 공용 위치로 옮기고, 모든 게이트가 금지어를 `lexicon.json` 한 곳에서 읽게 맞춤

---

## 부록 A. 착수 질문 표준 (한 번에)

1. 대상·범위 : 경계(지역, 사업부, 기간), 인접 대상을 안으로 둘지 밖으로 둘지
2. 진행 순서 : MD 토의본 먼저 → 확인 뒤 빌드(기본) / 한 번에
3. 산출물 : MD / Word / 이미지 덱(PDF, PNG zip, 쪽마다 이미지인 PPTX) / 편집 가능한 PPTX, 언어 KR·EN
4. 양식 원본 : 직전 편 덱 PDF, Word, MD 첨부(저자 소개 쪽, 로고, 레이아웃 대조용)

## 부록 B. BRIEF.md 뼈대

`references/briefs/BRIEF.md` 를 복사해 채움. 구성 : 0 제1 규칙 / 1 범위 / 2 도구·출처(검색 예산, 태그) / 3 산출 / 4 최종 메시지 / 5 갈래 배정

## 부록 C. 끝 메시지

- 무엇이 나왔는지 한 줄 → 파일 → 게이트 결과(pass 여부, claims 총·verified·estimate·removed) → 남은 확인 요청이나 토의 안건 1~3개
- 과정 요약과 긴 설명은 넣지 않음

## 부록 D. 파일 찾기

```bash
# 플러그인으로 함께 설치된 경우 : 이 스킬 폴더 기준 형제 경로
ls ../generate-full-report/references/gate_report.py ../image-deck/references/deck_core.py
# 어디 있는지 모를 때
find / -name "gate_report.py" -path "*generate-full-report*" -not -path "/proc/*" 2>/dev/null | head -3
```
