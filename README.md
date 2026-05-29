<div align="center">

# insight-full-report

### One prompt → four polished documents.
### 한 번의 프롬프트로 4종 문서를 동시에.

**Korean Word · English Word · Korean PowerPoint · English PowerPoint**
한국어 Word · 영어 Word · 한국어 PowerPoint · 영어 PowerPoint

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![version](https://img.shields.io/badge/version-0.5-blue.svg)](#)
[![Claude](https://img.shields.io/badge/Claude-Compatible-purple.svg)](#)
[![WRODING](https://img.shields.io/badge/WRODING-Series-orange.svg)](#)

</div>

---

## What it is / 한눈에 보기

`insight-full-report` is an open-source, MIT-licensed **Claude Code plugin (skill)** that converts a single natural-language request into **four publication-ready documents at once**. Ask Claude *"보고서 만들어줘"* (*"make me a report"*), and it produces a Korean Word report, an English Word report, a Korean PowerPoint deck, and an English PowerPoint deck — bilingual and presentation-grade — in one pass.

`insight-full-report`는 Claude에게 **"보고서 만들어줘"** 한마디로 **한국어 Word · 영어 Word · 한국어 PowerPoint · 영어 PowerPoint 4종 문서를 동시에** 생성하는 오픈소스 플러그인입니다.

It encodes a structured analyst-report methodology — the **WRODING framework** — into a reproducible OOXML pipeline, so that **non-developers** can generate consistent, professionally formatted deliverables without touching a template by hand.

분석가 산문체와 5-Zone 슬라이드 구조를 정본 템플릿으로 고정해, 매번 동일한 품질의 문서를 자동으로 만들어 줍니다.

---

## Why it matters / 이 도구가 채우는 공백

Most AI document tooling is English-first and assumes a developer audience. `insight-full-report` is built for a corner of the ecosystem that those tools don't reach: **Korean-speaking strategists, educators, and corporate planners** who need structured bilingual output but don't write code.

- **Bilingual by default** — Korean and English deliverables generated together, not as an afterthought.
- **Non-developer friendly** — one sentence in, four finished files out.
- **Reproducible** — the same WRODING structure every time, via a fixed OOXML build pipeline.
- **Open & adaptable** — MIT-licensed; fork the templates and methodology for your own domain.

영어 우선·개발자 중심의 기존 도구가 놓치는 **비영어권·비개발자 지식 노동자**를 위한 도구입니다.

---

## Features / 주요 기능

| | |
|---|---|
| 🇰🇷 **KR Word** (.docx) | Korean formal report (입니다/합니다체) |
| 🇬🇧 **EN Word** (.docx) | English analyst-style report |
| 🇰🇷 **KR PowerPoint** (.pptx) | 5-Zone Korean slide deck |
| 🇬🇧 **EN PowerPoint** (.pptx) | 5-Zone English slide deck |

- **WRODING analyst prose** — Key Questions → Executive Summary → numbered TOC → narrative sections → data tables.
- **5-Zone slide layout** — consistent, McKinsey-style structure across every deck.
- **Single canonical template** — uniform branding, typography, and color across all four outputs.

---

## Quick start / 빠른 시작

> Requires Claude Code with plugin/skill support.
> Claude Code(스킬 지원 버전)가 필요합니다.

```bash
# 1. Clone the repository
git clone https://github.com/dhshin0604/insight-full-report.git

# 2. Install the skill into your Claude environment
#    (place the skill directory where Claude Code loads skills from)
cp -r insight-full-report/skills/generate-full-report <your-claude-skills-path>/
```

Then, in Claude, simply ask:

```
보고서 만들어줘 — 주제: [your topic]
make me a full report on: [your topic]
```

Claude will generate all four documents using the canonical template.

---

## How it works / 작동 원리

```
User prompt
   │
   ▼
WRODING methodology  ──►  structure & analyst prose
   │
   ▼
OOXML build pipeline ──►  ┌── KR .docx
                          ├── EN .docx
                          ├── KR .pptx
                          └── EN .pptx
```

The plugin separates **content generation** (WRODING-structured prose) from **document assembly** (a deterministic OOXML pipeline), which is why the four outputs stay visually and structurally consistent every run.

---

## Repository structure / 저장소 구성

```
insight-full-report/
├── .claude-plugin/              # plugin manifest
├── assets/                      # WRODING branding, banner, diagrams
├── skills/generate-full-report/ # the core skill: templates + build logic
├── LICENSE                      # MIT
└── README.md
```

---

## Roadmap / 향후 계획

- [ ] Additional slide templates and report layouts
- [ ] More language pairs beyond KR/EN
- [ ] Configurable branding (footer, color, fonts)
- [ ] Example gallery of generated outputs

---

## Contributing / 기여

Contributions, issues, and template adaptations are welcome. Open an issue describing your use case, or fork and submit a pull request.

이슈·PR·템플릿 확장 기여를 환영합니다.

---

## License / 라이선스

[MIT](./LICENSE) © DONG HYUNG SHIN

---

<div align="center">

*Researched, Written, and Created by DONG HYUNG SHIN*
**[신동형 인사이트] · WRODING Series**

</div>
