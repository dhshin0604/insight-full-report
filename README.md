# insight-full-report

### One prompt → four polished, fact-checked documents.
### 한 번의 프롬프트로, 검증까지 끝난 4종 문서를 동시에.

**Korean Word · English Word · Korean PowerPoint · English PowerPoint**
한국어 Word · 영어 Word · 한국어 PowerPoint · 영어 PowerPoint

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![version](https://img.shields.io/badge/version-0.9.1-blue.svg)
![Claude](https://img.shields.io/badge/Claude-Compatible-purple.svg)
![Dynamic Workflow](https://img.shields.io/badge/Dynamic%20Workflow-Harness-red.svg)
![WRODING](https://img.shields.io/badge/WRODING-Series-orange.svg)

---

## What it is / 한눈에 보기

`insight-full-report` is an open-source, MIT-licensed **Claude Code plugin (skill)** that converts a single natural-language request into **four publication-ready documents at once**. Ask Claude *"보고서 만들어줘"* (*"make me a report"*), and it produces a Korean Word report, an English Word report, a Korean PowerPoint deck, and an English PowerPoint deck — bilingual, fact-checked, and presentation-grade — in one pass.

`insight-full-report`는 Claude에게 **"보고서 만들어줘"** 한마디로 **한국어 Word · 영어 Word · 한국어 PowerPoint · 영어 PowerPoint 4종 문서를 동시에** 생성하는 오픈소스 플러그인입니다.

**v0.9.1 "Unified Deep-Verify Edition"** builds the documents with a **dynamic multi-agent workflow harness** (Claude Code [dynamic workflows](https://code.claude.com/docs/en/workflows)) and blocks hallucinated facts with a **Claims-Ledger deep-verification gate** — every number in the output is traced to a source or explicitly marked as an estimate.

v0.9.1은 **동적 워크플로 하니스**로 챕터를 병렬 생성·교차 검증하고, **Claims Ledger 기반 딥 베리피케이션**으로 출처 없는 수치가 최종 문서에 남지 못하게 차단합니다.

---

## What's new in v0.9.1 / 주요 변경점

| | v0.5 | v0.9.1 |
|---|---|---|
| 생성 방식 | 단일 컨텍스트 | **동적 워크플로 하니스** — 챕터별 fan-out, adversarial critic, loop-until-done |
| 사실 검증 | 없음 | **Deep Verification** — claims.json ledger + 검증 에이전트 fan-out + `verify_claims.py` 기계 게이트 |
| 품질 게이트 | verify_toc | **4중 게이트** (`gate_report.py`): 구조(toc) + 규칙(content) + 수치-출처(claims) + LLM-judge(16점 루브릭) |
| 인사이트 | 산문체 규칙 | **So-What 사다리**(사실→의미→함의→행동) + 반론 내성 + 비교축 의무 (`insight-frameworks.md`) |
| 시각화 | 표지 차트 1개 | **시각화 카탈로그** — 내용 유형→플로우차트/표/막대/타임라인/2×2 매핑 (`visual-catalog.md`) |
| Word 목차 | 수동 번호 (드리프트 위험) | **H1C/H2C 자동 번호** (`1.` / `1.1`) + HEADNUM 게이트 |
| 챕터 수 | 고정 7챕터 | 소스 깊이 따라 **5~9챕터 가변** (TOC↔본문 1:1 정합은 그대로 강제) |
| 다국어 소스 | — | 中文/日文 소스 자동 정규화 + `verify_lang_purity.py` |

---

## The harness / 동적 워크플로 하니스

Trigger with **`ultracode`** or *"워크플로로 만들어"*. The skill ships a workflow template (`references/build_4set.workflow.js`) that Claude adapts per task:

```
A. CLASSIFY    소스 분석 → 가변 챕터(5~9) + 모델 라우팅 + 시각화 계획   (classify-and-act)
B. NORMALIZE   비 한/영 소스 → KR/EN 정규화 노트 + Glossary             (conditional)
C. DRAFT       챕터당 에이전트 1개 병렬 초안 + claim 등록                (fan-out-and-synthesize)
C2. FACTCHECK  claim 묶음별 검증 에이전트 + skeptic 재감사               (deep verification)
D. VERIFY      작성자가 아닌 critic 이 16점 루브릭 채점, 불합격만 재작성  (adversarial verification)
E. BUILD       KR/EN × docx/pptx 4종 병렬 빌드                          (fan-out)
F. GATE+RETRY  gate_report.py 4중 게이트, 실패분만 패치-재빌드 (≤3회)     (loop-until-done)
G. FINALIZE    manifest + claims 통계 기록                              (observability)
```

This structurally prevents the four failure modes of long single-context runs: **agentic laziness, self-preferential bias, goal drift, and hallucination**.

단일 컨텍스트의 4대 실패 모드(중도 포기·자기편애 채점·목표 표류·할루시네이션)를 구조적으로 차단합니다. 작은 작업은 워크플로 없이 단일 컨텍스트 모드(Phase 0~7)로도 동일한 게이트를 통과해야 합니다.

---

## Anti-hallucination / 할루시네이션 차단

Every factual claim (number, date, event, quote) is registered in a **Claims Ledger** (`claims.json`) with one of three statuses:

| status | meaning | in the document |
|---|---|---|
| `verified` | confirmed against source/web | used as-is + Source line |
| `estimate` | calculated/extrapolated | must carry `추정` / `est.` marker |
| `removed` | failed verification | **must not appear** — build fails if it does |

`verify_claims.py` mechanically cross-checks the built .docx/.pptx against the ledger: unregistered numbers, leaked removed claims, and unmarked estimates all fail the build.

본문 수치를 ledger 와 기계 대조해, 미등록 수치·삭제된 주장 잔존·추정 무표기를 빌드 실패로 처리합니다.

---

## Features / 주요 기능

| | |
|---|---|
| 🇰🇷 **KR Word** (.docx) | Korean formal report (입니다/합니다체), auto-numbered chapters `1. / 1.1` |
| 🇬🇧 **EN Word** (.docx) | English analyst-style report |
| 🇰🇷 **KR PowerPoint** (.pptx) | 5-Zone Korean slide deck |
| 🇬🇧 **EN PowerPoint** (.pptx) | 5-Zone English slide deck |

- **WRODING analyst prose** — Key Questions → Executive Summary → numbered TOC → narrative sections → data tables.
- **5-Zone slide layout** — consistent, McKinsey-style structure across every deck.
- **So-What insight ladder** — key messages must reach implication level (L2+), with counter-argument handling.
- **Visual catalog** — process→flowchart, comparison→table, trend→bars, chronology→timeline, positioning→2×2.
- **Single canonical template** — uniform branding, typography, and color across all four outputs.
- **Deterministic OOXML pipeline** — `build_pptx.sh` orchestrator; same result on Opus or Sonnet.

---

## Quick start / 빠른 시작

> Requires Claude Code / Claude Cowork with plugin & skill support.

```bash
# 1. Clone the repository
git clone https://github.com/dhshin0604/insight-full-report.git

# 2. Install the skill into your Claude environment
cp -r insight-full-report/skills/generate-full-report <your-claude-skills-path>/
#    (or install the repo as a plugin — it ships a .claude-plugin manifest)
```

Then, in Claude, simply ask:

```
보고서 만들어줘 — 주제: [your topic]            # standard mode
ultracode 워크플로로 4종 세트 만들어 — [topic]   # dynamic-workflow harness mode
```

---

## How it works / 작동 원리

```
User prompt
   │
   ▼
Dynamic workflow harness ──► classify → draft (fan-out) → factcheck → critic
   │                                                (claims.json ledger)
   ▼
WRODING methodology  ──►  structure & analyst prose (So-What ladder)
   │
   ▼
OOXML build pipeline ──►  ┌── KR .docx ─┐
                          ├── EN .docx  │──► gate_report.py
                          ├── KR .pptx  │    (toc·content·claims·judge)
                          └── EN .pptx ─┘    pass ➜ deliver / fail ➜ retry
```

Content generation, fact verification, and document assembly are **separate, independently gated stages** — which is why the four outputs stay consistent and source-faithful every run.

---

## Repository structure / 저장소 구성

```
insight-full-report/
├── .claude-plugin/                       # plugin manifest (v0.9.1)
├── assets/                               # WRODING branding, banner, diagrams
├── skills/generate-full-report/
│   ├── SKILL.md                          # the canonical procedure (gates, phases)
│   └── references/
│       ├── build_4set.workflow.js        # dynamic-workflow harness template
│       ├── factcheck-pipeline.md         # Claims Ledger & deep verification rules
│       ├── insight-frameworks.md         # So-What ladder, counter-arguments
│       ├── visual-catalog.md             # content-type → visual mapping
│       ├── quality_rubric.md             # 8-criteria LLM-judge rubric
│       ├── verify_claims.py / verify_content.py / verify_toc.py / verify_lang_purity.py
│       ├── gate_report.py                # unified 4-gate verdict
│       ├── build_pptx.sh / build_pptx_checked.sh
│       └── build_*.template.{js,py} + TEMPLATE.pptx
├── LICENSE                               # MIT
└── README.md
```

---

## Roadmap / 향후 계획

- [ ] Additional slide templates and report layouts
- [ ] More language pairs beyond KR/EN
- [ ] Configurable branding (footer, color, fonts)
- [ ] Example gallery of generated outputs
- [x] Dynamic-workflow harness (v0.9)
- [x] Deep verification / claims ledger (v0.9)
- [x] Auto-numbered Word chapters (v0.9.1)

---

## Contributing / 기여

Contributions, issues, and template adaptations are welcome. Open an issue describing your use case, or fork and submit a pull request.

이슈·PR·템플릿 확장 기여를 환영합니다.

---

## License / 라이선스

[MIT](LICENSE) © DONG HYUNG SHIN

---

*Researched, Written, and Created by DONG HYUNG SHIN*
**[신동형 인사이트] · WRODING Series**
