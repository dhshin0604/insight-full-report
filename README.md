# insight-full-report

### One prompt → four polished, fact-checked documents.
### 한 번의 프롬프트로, 검증까지 끝난 4종 문서를 동시에.

**Korean Word · English Word · Korean PowerPoint · English PowerPoint**
한국어 Word · 영어 Word · 한국어 PowerPoint · 영어 PowerPoint

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![version](https://img.shields.io/badge/version-0.9.3-blue.svg)
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

## What's new in v0.9.3 / 주요 변경점

**Compatible with the October 2026 Anthropic `pptx` skill.** That skill dropped
`scripts/office/unpack.py` and `pack.py`, and its `add_slide.py` now registers `<p:sldIdLst>` itself,
so the previous orchestrator stopped at the unpack step. `build_pptx.sh` now ships its own
unpack/pack (zipfile, `[Content_Types].xml` first), reconciles `sldIdLst` against the slide
relationships (duplicates and orphans removed, missing slides added; identical result with the old or
the new `add_slide.py`), finds the pptx skill under `/mnt/skills/public/pptx`,
`~/.claude/skills/synced/*/pptx` or `/sessions/*`, and runs `validate.py --original` after packing.
Older pptx skills that still have `unpack.py`/`pack.py` keep working unchanged.

2026년 10월판 Anthropic `pptx` 스킬에서 `unpack.py`·`pack.py` 가 사라지고 `add_slide.py` 가 `sldIdLst`
등록까지 맡게 되면서 기존 오케스트레이터가 unpack 단계에서 멈추던 문제를 고쳤습니다. `build_pptx.sh`
가 unpack/pack 을 내장하고, `sldIdLst` 를 rels 기준으로 정합하며, pack 뒤 `validate.py` 검증을 붙였습니다.
구판 pptx 스킬에서도 그대로 동작합니다.

---

## What's new in v0.9.2 / 주요 변경점

**Author profile extracted from the templates.** Name, phone, email, and output path moved out of
`SKILL.md`, the four build templates, `pptx-style-guide.md`, and `TEMPLATE.pptx` into
`references/profile.json`, applied at build time by `apply_profile.py` with a hard stop if anything
is left unfilled. Anyone can now clone the repo and produce documents under their own name without
editing the templates. See **Setup: author profile** above.

작성자 정보를 템플릿에서 분리했습니다. 이름·전화·이메일·저장 경로가 `profile.json` 한 곳으로 모였고,
빌드 시 자동 치환되며 값이 비면 빌드가 중단됩니다.

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

## Setup: author profile / 작성자 프로필 (v0.9.2)

The templates carry **no hard-coded name, phone, email, or output path**. Your details live in one
file, `skills/generate-full-report/references/profile.json`, and are substituted into the Word cover
line, the PPTX cover and closing slide, and the credit line at the bottom of every layout.

정본 템플릿에는 이름·전화·이메일·저장 경로가 하드코딩되어 있지 않습니다. 아래 한 파일의 값이 Word 표지,
PPTX 표지·맺음말, 모든 슬라이드 하단 크레딧 줄로 들어갑니다.

```jsonc
{
  "AUTHOR_KR": "홍길동",                 // Word/PPTX cover, closing slide (KR)
  "AUTHOR_EN": "Gildong Hong",           // EN documents + every slide credit line
  "PHONE_KR":  "010-0000-0000",
  "PHONE_EN":  "+82-10-0000-0000",
  "EMAIL":     "name@example.com",
  "WORKSPACE_ROOT":    "C:\\Users\\<you>\\OneDrive\\Reports",  // permanent output folder
  "WORKSPACE_DIRNAME": "Reports"
}
```

Fill it once, or leave it empty and answer when the skill asks — it then writes `./profile.json`
into your working folder. Resolution order is `PROFILE` env var → `./profile.json` → the bundled
`references/profile.json`; the file that has all five required keys wins.

```bash
python3 references/apply_profile.py --which        # which profile file will be used
python3 references/apply_profile.py build_kr.js    # Word: substitute before running the build
#          PPTX: build_pptx.sh applies the profile automatically
```

If any value is still empty the build **stops** and prints what is missing, so a placeholder such as
`{AUTHOR_KR}` can never reach a finished document. Drop a `references/logo.png` (315×60px,
transparent) to put your own logo on the cover; without one the logo area stays blank.

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
├── .claude-plugin/                       # plugin manifest (v0.9.3)
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
│       ├── apply_profile.py / profile.json  # author & contact profile (see Setup)
│       ├── build_pptx.sh / build_pptx_checked.sh
│       └── build_*.template.{js,py} + TEMPLATE.pptx
├── skills/quality-core/                  # standalone quality core (v0.1)
│   ├── SKILL.md                          # gates + 6-phase verify workflow
│   └── references/                       # claims-ledger · so-what · 16-pt rubric
│                                         #   · style rules · verify_claims_lite.py
├── LICENSE                               # MIT
└── README.md
```

---

## Bundled skill: quality-core / 번들 스킬 — 품질 코어 (v0.1)

`skills/quality-core/` is the **standalone quality core** extracted from this pipeline. It applies the same discipline — Claims-Ledger fact gate (`verified / estimate / removed`), So-What insight ladder, fact-vs-opinion sentence rules, the 16-point LLM-judge rubric, and the retry-with-limit loop (≤3, then `NEEDS_REVIEW` back to a human) — to **any document**: your own drafts, memos, or reports written by others. No 4-doc build required.

`skills/quality-core/`는 본 파이프라인에서 **품질 코어만 떼어낸 범용 검증·개선 스킬**입니다. 어떤 초안·보고서에든 Claims Ledger 사실 게이트, So-What 사다리, 사실↔해석 문형 규율, 16점 judge 루브릭, 재시도≤3회 루프를 그대로 적용합니다. 트리거 예: **"품질 코어 적용해줘"**, **"이 초안 검증해줘"**, **"팩트체크 게이트 돌려줘"**.

| | `generate-full-report` | `quality-core` |
|---|---|---|
| Purpose / 목적 | build the 4-doc set / 4종 정본 문서 생성 | verify & improve any draft / 임의 문서 검증·개선 |
| Output / 산출 | KR·EN Word + PPTX | revised draft + `claims.json` + rubric scorecard |
| Machine gate / 기계 게이트 | full OOXML gate chain | `verify_claims_lite.py` (MD/text) |

---

## Roadmap / 향후 계획

- [ ] Additional slide templates and report layouts
- [ ] More language pairs beyond KR/EN
- [ ] Configurable branding (footer, color, fonts)
- [ ] Example gallery of generated outputs
- [x] Dynamic-workflow harness (v0.9)
- [x] Deep verification / claims ledger (v0.9)
- [x] Auto-numbered Word chapters (v0.9.1)
- [x] Author profile extraction — no personal data in templates (v0.9.2)
- [x] Compatibility with the 2026-10 Anthropic pptx skill — built-in unpack/pack, rels-based sldIdLst, validate gate (v0.9.3)
- [x] Standalone `quality-core` skill — extracted quality core (v0.1)

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
