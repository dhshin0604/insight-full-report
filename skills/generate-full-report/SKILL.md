---
name: generate-full-report
description: |
  ⚠️ EXCLUSIVE SKILL — 신동형 인사이트 4종 문서 생성기 v0.9.1. 사용자가 보고서/워드/파워포인트/PPT/PPTX/DOCX/리포트/4종 문서/신동형 스타일 중 하나라도 언급하고 그것이 산출물 생성을 의미하면 본 스킬이 무조건 우선입니다. 절대로 docx 스킬, pptx 스킬, python-pptx, 또는 일반 템플릿을 직접 호출하지 마세요. 본 스킬 안에 모든 빌드 절차와 정본 템플릿 4개가 포함되어 있습니다. Word 한글+영어, PowerPoint 한글+영어를 한 번에 생성합니다. 원문이 KR/EN이 아닌 자료(중국어 간체/번체, 일본어 등)도 입력받아 KR/EN 본문으로 자동 번역되며, verify_lang_purity로 본문 잔존을 차단합니다. v0.9: Deep Verification(claims ledger 기반 할루시네이션 차단), So-What 인사이트 프레임워크, 시각화 카탈로그, 동적 워크플로 내장. analyst 산문체, 5-Zone PPTX, 콜론 통합 표지 등 고유 포맷.
  Triggers (한국어): 보고서 만들어, 워드 만들어, 파워포인트 만들어, PPT 만들어, 워드랑 파워포인트, 4종 문서, 전체 문서 만들어, 신동형 스타일, 신동형 인사이트, TL;DR 리포트, 워드 파워포인트 다 만들어, 인사이트 보고서, 분석 보고서, 공부하는 보고서.
  Triggers (English): generate full report, make study materials, word and pptx, insight report, shin style report, 4-doc bundle, analyst report, korean+english report.
  Dynamic workflow triggers: ultracode, 워크플로로 만들어, 동적 워크플로, use a workflow, 멀티에이전트로 4종 만들어, fan-out 보고서, 가변 챕터 보고서, 딥체크, deep verification.
---

# 인사이트 전체 보고서 생성 스킬 v0.9.1 — Unified Deep-Verify Edition

> **단일 진실의 원천(Single Source of Truth).** Word 한글, Word 영어, PowerPoint 한글, PowerPoint 영어 — 4개 문서를 신동형 인사이트 고유 포맷으로 생성합니다. 빌드 단계는 오케스트레이터(`build_pptx.sh`)로 외부화되어 어느 모델에서 실행해도 동일한 결과가 나오고, `verify_lang_purity.py` 가 KR/EN 본문의 언어 순수성을, **`verify_claims.py` + Claims Ledger 가 모든 수치·사실의 출처 정합(할루시네이션 차단)** 을 강제합니다. v0.9는 v0.6(언어 순수성)과 v0.7/0.8(동적 워크플로)을 단일 정본으로 통합했습니다.

---

## 🚨 GATE 0 — 즉시 중단 체크

이 스킬이 로드되었다면 다음 중 하나라도 해당하면 **STOP** 후 본 SKILL.md를 처음부터 다시 읽기:

1. `docx` 스킬 또는 `pptx` 스킬을 호출하려고 했다 → STOP. 본 스킬이 모든 것을 처리한다.
2. `python-pptx` 라이브러리를 import하려고 했다 → STOP. 반드시 unpack→XML편집→pack 패턴 사용.
3. `build_kr.js` / `build_pptx_kr.py` 를 scratch에서 작성하려고 했다 → STOP. `references/build_*.template.*` 4개를 cp로 복사 후 내용만 치환.
4. 필수 reference `.md` 파일을 한 개도 안 읽었다 → STOP. 아래 GATE 1을 먼저 수행.
5. PPTX를 만들면서 `build_pptx.sh` 오케스트레이터를 우회했다 → STOP. 오케스트레이터가 unpack/sldIdLst/strip/pack/verify 를 모두 처리한다.
6. 표지에 PB() 페이지브레이크 또는 Source 라인을 넣으려고 했다 → STOP. 표지+차트는 동일 페이지.
7. Phase 0 를 건너뛰고 `/sessions/*/mnt/outputs` 같은 임시 경로에 최종 산출물을 저장하려 했다 → STOP. 반드시 Phase 0 의 사용자 영구 폴더(`$WORKSPACE`)로 저장.
8. `present_files` 를 `$WORKSPACE` 바깥 경로(cwd, tmp, outputs 등)로 호출하려 했다 → STOP. mount 바깥 경로는 자동으로 세션 outputs 로 복사되어 카드 링크가 **세션 종료 후 깨짐**. 반드시 Phase 7-B 의 안전 검증 통과 후 $WORKSPACE 하위 경로만 전달.
9. 소스 언어가 **한국어/영어가 아닌 경우**(중국어·일본어·기타) 원문 표기를 그대로 본문에 넣으려 했다 → STOP. **Phase 1.5 (다국어 소스 언어 정규화)** 를 먼저 수행한 뒤 Phase 2 로 진입.
10. **소스에서 확인하지 않은 수치·날짜·사건·인용을 본문에 쓰려고 했다** → STOP. 모든 사실 주장은 Phase 2.7 의 Claims Ledger(`claims.json`)에 등록·검증되어야 한다 (`references/factcheck-pipeline.md`). 기억(사전지식)에서 꺼낸 수치는 웹으로 재확인 전까지 사용 금지.

---

## 🛑 GATE 1 — 작업 시작 전 필수 (MANDATORY READS)

이 스킬이 트리거되면 **첫 번째 행동은 반드시** 아래 7개 reference 파일을 `Read` 툴로 모두 읽는 것입니다.

```
1. references/docx-build-pipeline.md     ← Word 빌드 헬퍼 함수와 패턴
2. references/pptx-build-pipeline.md     ← PPTX OOXML 빌드 패턴 (placeholder 버그 회피 포함)
3. references/pptx-style-guide.md        ← 5-Zone 레이아웃 좌표·색상
4. references/pptx-chart-helpers.md      ← make_table / make_hbars 등 시각화 함수
5. references/docx-chart-design.md       ← 표지 플로우차트 SVG 설계
6. references/factcheck-pipeline.md      ← Deep Verification — Claims Ledger·검증 규칙 (v0.9)
7. references/insight-frameworks.md      ← So-What 사다리·반론 내성·수치 비교축 (v0.9)
```

권장 추가 읽기: `references/visual-catalog.md` (본문 시각화 카탈로그 — 권장 가이드),
`references/verify_lang_purity.py` (비 한/영 소스일 때 통독 권장).

그리고 build 단계 진입 직전 아래 **canonical template** 4개도 읽어 그대로 적응(adapt)해야 합니다.

```
references/build_kr.template.js          ← Word 한글 정본
references/build_en.template.js          ← Word 영어 정본
references/build_pptx_kr.template.py     ← PPTX 한글 정본 (slide5 closing 포함)
references/build_pptx_en.template.py     ← PPTX 영어 정본 (slide5 closing 포함)
```

### GATE 1 셀프 체크 — 6문 6답 통과 필수

```
Q1. PPTX의 모든 Zone helper 함수에서 <p:nvPr> 태그는?
   정답: 빈 태그 <p:nvPr/>. <p:ph type="..."/> 절대 금지.
Q2. rr() 함수의 underline 파라미터 기본값은?
   정답: u='none'. slideLayout5의 defRPr u="sng" 상속을 막는다.
Q3. Word 문서의 textBox에서 사용하는 ShadingType은?
   정답: ShadingType.CLEAR. SOLID는 검은 배경 버그.
Q4. 한국어 인용부호 'word' 를 JS 문자열에 어떻게 넣는가?
   정답: 「word」 로 변환.
Q5. PPTX 빌드는 어떤 명령으로 끝까지 실행하는가?
   정답: bash references/build_pptx.sh kr build_pptx_kr.py 출력파일.pptx
        오케스트레이터 한 줄로 unpack/sldIdLst보정/슬라이드작성/strip/pack/검증을 모두 수행.
Q6. 본문에 수치를 쓰기 위한 전제 조건은?
   정답: claims.json 에 등록되고 status=verified(출처 확인) 또는 estimate(본문 '추정' 표기).
        removed claim 이 본문에 남으면 verify_claims.py 가 빌드를 FAIL 시킨다.
```

---

## 🚫 ANTI-DRIFT — 절대 금지 사항

| ❌ 금지 | ✅ 대신 |
|---|---|
| `pptx` 스킬을 직접 invoke | 본 스킬의 `references/build_pptx.sh` 만 사용 |
| `docx` 스킬을 직접 invoke | `build_kr.template.js` / `build_en.template.js` 적응 |
| python-pptx 라이브러리로 생성 | unpacked TEMPLATE.pptx XML 직접 편집 |
| TEMPLATE.pptx 없이 처음부터 생성 | `references/TEMPLATE.pptx`(번들 포함) 사용 |
| 슬라이드 unpack/pack 단계를 모델이 직접 수행 | `build_pptx.sh` 오케스트레이터에 위임 |
| TOC(slide2)와 본문 z1 챕터 라벨을 따로 작성 | 두 번호가 1:1로 일치해야 하며 `verify_toc.py` 가 강제 |
| 맺음말 슬라이드를 본문 중간에 두기 | sldIdLst에서 마지막 위치로 이동 (오케스트레이터가 자동) |
| Word 본문에 bullet points (`•`, `-`) 사용 | analyst 산문체 3~4 단락 (`입니다/합니다` 체) |
| Executive Summary를 textBox 3개로 분리 | 단일 textBox + SL() 4개 서브섹션 |
| 표지에 PB() 페이지 브레이크 / Source 줄 | 표지+차트 동일 페이지, Source/해시태그 없음 |
| `ShadingType.SOLID` 사용 | `ShadingType.CLEAR` |
| `<p:ph>` placeholder를 여러 shape에 사용 | 모든 Zone helper의 `<p:nvPr>` 는 빈 `<p:nvPr/>` |
| 한국어 인용부호 `'단어'` 그대로 | `「단어」` 로 변환 |
| 영어본 전화번호 다른 형식 | `+82-10-2202-8761` |
| 한국어 차트에 NanumGothic 외 폰트 | NanumGothic 필수, 영어는 Arial/DejaVu Sans |
| 산출물을 `/sessions/$USER_SESSION/mnt/outputs` 로 저장 | Phase 0 의 `$WORKSPACE` (사용자 OneDrive 영구 폴더) 로 저장 |
| Phase 0 를 생략 | Phase 0 는 **필수**. 저장 경로를 먼저 확정한 뒤 빌드 시작 |
| 중국어/일본어 원문을 그대로 본문에 복사·붙여넣기 | 반드시 한글(한글문서) 또는 영어(영문문서)로 **전면 번역** 후 사용 |
| 한글 본문에 한자(漢字/中文) 혼입 | 한글 본문은 100% 한글. 고유명사·핵심기술용어는 **첫 등장시에만** `한글(中文)` 형식, 이후 한글 전용 |
| 영문 본문에 中文 혼입 | 영문 본문은 100% English. 고유명사는 **첫 등장시에만** `English (Pinyin, 中文)` 형식, 이후 English 전용 |
| pinyin 없이 中文만 괄호에 병기 | 영문 문서는 pinyin 동반 필수 (`Zhipu AI (Zhìpǔ, 智谱)`) |
| 일본어 가나(ひらがな/カタカナ) 또는 한자를 본문에 그대로 | 동일 정책: 한글/영어 전면 번역, 첫 등장에만 괄호 원문 |
| Phase 1.5 (언어 정규화) 를 생략 | 비(非) 한/영 소스가 하나라도 있으면 Phase 1.5 **필수** |
| **기억(사전지식)의 수치·날짜를 그대로 본문에 사용** | WebSearch/WebFetch/소스 재독으로 확인 후 claims.json 에 verified 등록 |
| **소스에 없는 수치를 그럴듯하게 생성** | 수치 없이 서술하거나 estimate 등록 + 본문 `추정` 표기 + 산출 근거 |
| **비교축 없는 절대값 수치 나열** | YoY/경쟁사/시장평균 중 1개 비교축 동반 (insight-frameworks.md §2) |
| **사실과 해석(의견)을 같은 문형으로 단정** | 해석·전망은 "~로 해석됨/~할 가능성이 큼" 으로 의견임을 명시 |
| KEY MESSAGE 를 사실 나열(L1)로 작성 | So-What 사다리 L2 이상 — 의미·함의가 담긴 통찰 명제 |
| 프로세스·구조 설명을 줄글로만 길게 서술 | visual-catalog.md 매핑에 따라 플로우차트/표/차트 활용 (권장) |
| **Word 챕터 헤딩에 번호 누락** (`제목`만) 또는 텍스트에 수동 번호 기입 | `H1C()`/`H2C()` 헬퍼 사용 — `1. 제목`/`1.1 소제목` 자동 번호. `verify_content.py` HEADNUM 게이트가 강제 (v0.9.1) |

---

## 사전 확인 (AskUserQuestion)

작업 시작 전 반드시 확인:
1. **소스**: URL / YouTube / PDF / DOCX / 텍스트 직접
2. **제목 + 부제목**: 보고서 제목과 부제목 (콜론 통합용)
3. **작성자**: 기본값 KR=`신동형`, EN=`DH Shin`
4. **주제 슬러그(폴더/파일명용)**: 한글/영문 혼용 가능, 공백은 언더스코어(`_`)로. 예: `AI에이전트`, `반도체_2026`

> 세션 임시 outputs는 사라지므로 반드시 **사용자의 영구 폴더**로 저장해야 합니다. 아래 Phase 0 를 건너뛰지 마세요.
> Deep Verification(Phase 2.7)은 v0.9의 **기본값**입니다 — 별도 질문 없이 항상 수행합니다.

---

## Phase 0: 출력 폴더 준비 (영구 저장 경로 확정) — **필수**

> **Why this phase exists**: 예전 버전은 `/sessions/$USER_SESSION/mnt/outputs` 로 저장했는데 이 경로는 세션 종료와 함께 삭제되고, Windows 탐색기에서 열면 "위치를 사용할 수 없습니다" 오류가 발생합니다. 이제부터는 **사용자의 OneDrive 영구 폴더**에 직접 저장합니다.

### 저장 경로 규칙 (고정)

```
루트    : C:\Users\dongh\OneDrive\신동형인사이트\
하위폴더 : {주제}_{YYYYMMDD}\
최종    : C:\Users\dongh\OneDrive\신동형인사이트\{주제}_{YYYYMMDD}\
          ├─ {주제}_KR_Report_{YYYYMMDD}.docx
          ├─ {주제}_EN_Report_{YYYYMMDD}.docx
          ├─ {주제}_KR_Presentation_{YYYYMMDD}.pptx
          └─ {주제}_EN_Presentation_{YYYYMMDD}.pptx
```

### STEP 0-A — 루트 폴더 mount (한 번)

`mcp__cowork__request_cowork_directory` 를 호출해 루트 폴더를 연결합니다:

```
path: C:\Users\dongh\OneDrive\신동형인사이트
```

> 폴더가 아직 없으면 사용자에게 먼저 생성을 안내하거나, OneDrive 루트만 mount 한 뒤 `mkdir -p` 로 `신동형인사이트` 하위를 만듭니다.

### STEP 0-B — 마운트 경로 감지 (동적 탐색, `$USER_SESSION` 미의존)

```bash
# 세션 mnt 루트 자동 감지
SESSION_MNT=$(ls -d /sessions/*/mnt 2>/dev/null | head -1)

# 1순위: 사용자가 직접 mount한 '신동형인사이트' 폴더
DEST_ROOT=$(find "$SESSION_MNT" -maxdepth 3 -type d -name '신동형인사이트' 2>/dev/null | head -1)

# 2순위: OneDrive 하위
[ -z "$DEST_ROOT" ] && DEST_ROOT=$(find "$SESSION_MNT" -maxdepth 4 -type d -path '*OneDrive*신동형인사이트*' 2>/dev/null | head -1)

# 3순위: fallback — 세션 outputs (경고 표시 후 사용, 영구 저장은 실패)
if [ -z "$DEST_ROOT" ]; then
  echo "⚠️  영구 폴더 mount 실패 — 세션 outputs 사용 (세션 종료 시 삭제됨!)"
  DEST_ROOT="$SESSION_MNT/outputs"
fi
echo "DEST_ROOT = $DEST_ROOT"
```

### STEP 0-C — 주제 하위폴더 생성

```bash
TOPIC_SLUG="<사용자 지정 주제 슬러그>"         # 예: AI에이전트
TODAY=$(date +%Y%m%d)                           # 예: 20260610
WORKSPACE="$DEST_ROOT/${TOPIC_SLUG}_${TODAY}"
mkdir -p "$WORKSPACE"
ls -la "$WORKSPACE"     # 존재 확인
echo "WORKSPACE = $WORKSPACE"
```

> 이후 Phase 4/5 에서 만든 `.docx`/`.pptx` 를 이 `$WORKSPACE` 로 `cp` 합니다.

### STEP 0-D — 자기 점검

- [ ] `$WORKSPACE` 가 `/sessions/*/mnt/` 아래에 존재 (`ls -la "$WORKSPACE"` OK)
- [ ] Windows 측 경로 `C:\Users\dongh\OneDrive\신동형인사이트\{주제}_{YYYYMMDD}\` 에 해당
- [ ] 세션 임시 경로(`/sessions/*/mnt/outputs`)는 최종 저장소로 사용하지 않음

---

## Phase 1: 소스 수집

- 웹/블로그/뉴스 URL → `WebFetch`
- YouTube → `WebFetch` + 자막 (`youtube.com/api/timedtext?v=ID&lang=ko|en`)
- PDF/DOCX → `Read`
- 텍스트 → 사용자 제공 그대로 분석

수집 완료 후 소스 제목·저자·날짜·핵심 주제 정리. 이때 **소스 원문의 언어**도 기록 (예: `KR / EN / ZH(简体) / ZH(繁體) / JA / 혼합`).

> 이 시점부터 Claims Ledger(`claims.json`) 작성을 시작합니다 — 소스에서 발견한 핵심 수치·사건을 바로 등록해 두면 Phase 2.7 검증이 빨라집니다 (`references/factcheck-pipeline.md` §1 스키마).

---

## Phase 1.5: 다국어 소스 언어 정규화 (Multilingual Source Normalization) — 조건부 **필수**

> **Why this phase exists**: 중국어·일본어·기타 비(非) 한/영 원문 소스를 그대로 분석에 쓰면 최종 Word/PPTX 본문에 한자(漢字)·中文·가나 문자가 섞여 들어가 신동형 인사이트의 한글/영문 정본 포맷을 훼손합니다. 본 Phase 에서 **정규화된 노트(normalized notes)** 를 먼저 만든 뒤 Phase 2 로 넘어가야 합니다.

### 트리거

다음 중 하나라도 해당하면 Phase 1.5 를 **반드시** 수행:

- 소스 언어에 `ZH(简/繁)`, `JA`, 기타 비(非) 한/영이 하나라도 포함
- 소스가 한/영이어도 **고유명사가 한자/中文으로만 표기**되어 있는 경우 (예: 中国电科, 比亚迪, 紫光)
- 영상/음성 자막이 중국어/일본어로 제공되는 경우

### STEP 1.5-A — 정규화 노트 생성

원문을 바로 Phase 2 구조에 넣지 말고, **중간 산출물**로 다음 두 세트를 만든다:

1. `notes_kr.md` — 한국어 정규화 노트 (한글 문서 빌드용)
2. `notes_en.md` — 영어 정규화 노트 (영문 문서 빌드용)

각 노트는 **원문 1 문단 → 번역 1 문단** 구조로 작성하되, 최종 본문에는 번역본만 사용한다.

### STEP 1.5-B — 한글 문서 언어 정책 (KR Docs)

본문 서술은 **100% 한글**. 한자·中文·가나 문자는 아래 한 가지 경우에만 허용:

| 상황 | 형식 | 예시 |
|---|---|---|
| 회사·제품·인물 고유명사 첫 등장 | `한글음차/번역(中文)` | `바이두(百度)`, `알리바바(阿里巴巴)`, `런정페이(任正非)` |
| 번역 모호한 핵심 기술용어 첫 등장 | `한글(中文)` | `전목시(全目視, end-to-end visual)` |
| 한시·고전 인용 (아주 드물게) | 인용 블록 내부에서만 원문+번역 | — |

**이후 모든 재등장은 한글 전용**. 본문 어디에도 `百度`, `人工智能`, `中国` 같은 독립 한자/中文 토큰이 나타나서는 안 된다.

> 주의: 괄호 병기는 **첫 등장 1회**에 한한다. TOC/챕터 라벨/KEY MESSAGE/z4 본문 어디에서도 규칙 동일.

### STEP 1.5-C — 영문 문서 언어 정책 (EN Docs)

본문 서술은 **100% English**. 고유명사 첫 등장시에만 pinyin + 中文 병기:

| 상황 | 형식 | 예시 |
|---|---|---|
| 회사·제품·인물 고유명사 첫 등장 | `English Name (Pinyin, 中文)` | `Baidu (Bǎidù, 百度)`, `BYD (Bǐyàdí, 比亚迪)`, `Ren Zhengfei (Rèn Zhèngfēi, 任正非)` |
| 번역 모호한 핵심 기술용어 첫 등장 | `English term (Pinyin, 中文)` | `full visual perception (quánmùshì, 全目視)` |

**이후 재등장은 English 전용**. 본문에 단독 中文 토큰 금지.

> 일본어 소스의 경우: 한글 문서는 `한글(日本語)`, 영문 문서는 `English (Romaji, 日本語)` 형식으로 동일 규칙 적용.

### STEP 1.5-D — 용어 사전(glossary) 고정

정규화 노트 상단에 **용어 사전**을 먼저 만든다 (이후 모든 챕터가 이 사전을 참조):

```markdown
## Glossary (Normalization Lookup)

| 원문 | KR (첫등장) | KR (재등장) | EN (첫등장) | EN (재등장) |
|---|---|---|---|---|
| 百度 | 바이두(百度) | 바이두 | Baidu (Bǎidù, 百度) | Baidu |
| 人工智能 | 인공지능 | 인공지능 | artificial intelligence (AI) | AI |
| 华为 | 화웨이(華為) | 화웨이 | Huawei (Huáwéi, 華為) | Huawei |
| 深度求索 | 딥시크(深度求索) | 딥시크 | DeepSeek (Shēndùqiúsuǒ, 深度求索) | DeepSeek |
```

Phase 2 이후의 모든 본문 작성은 이 사전의 **재등장 열(column)** 만 사용한다. 첫 등장 열은 각 문서에서 해당 용어가 처음 나오는 지점에만 한 번 쓰고, 같은 문서에서 재등장하면 재등장 열을 쓴다.

### STEP 1.5-E — 자기 점검

- [ ] `notes_kr.md` / `notes_en.md` 두 노트에 원문 1 문단당 번역 1 문단이 매핑되어 있다
- [ ] Glossary 가 정규화 노트 상단에 생성되어 있다
- [ ] Phase 2 이후의 모든 본문 초안이 번역본+Glossary 재등장열만 참조한다 (원문 복붙 0 건)
- [ ] 본문 작성 후 `grep -Pc '[\x{4E00}-\x{9FFF}\x{3040}-\x{309F}\x{30A0}-\x{30FF}]' notes_kr.md` 결과가 **Glossary + 첫등장 괄호 병기 부분의 예상치와 일치** (그 외 한자/가나 0건)

> 검증 팁: Phase 6 품질 검증에서 `verify_lang_purity.py` 가 4개 산출물에 대해 독립 한자/가나 토큰을 재확인한다.

---

## Phase 2: 내용 분석 및 구조화 (+ 인사이트 프레임워크)

### Executive Summary 4파트 (이 구조 외 금지)
```
■ Key Message   — 1~2문장 핵심 명제 (So-What 사다리 L3~L4)
■ 배경          — 거시 맥락 + 수치 (비교축 동반)
■ 핵심 구조 흐름 — ① ② ③ ④ Bold + 내러티브
■ 전망          — 단기/중기/장기 (조건문 + estimate 표기)
```

### 챕터 구성 (TOC와 본문 z1 라벨이 1:1로 일치해야 함)
```
I  : 개요/배경 (글로벌 맥락)
II : 핵심 기술/프레임워크
III: 제품·플레이어
IV : (선택) 응용/특수영역
V  : 산업/투자 생태계
VI : 미래 전망
VII: Devil's Advocate (비판적 관점)
```

> 기본은 7챕터 정본. **동적 워크플로(Phase D)에서는 소스 깊이에 따라 5~9개로 가변** — 단, TOC ↔ 본문 1:1 일치 규칙은 그대로 강제됩니다 (`verify_toc.py`).

### 각 챕터 내용 (insight-frameworks.md 적용 — v0.9 강화)
- 소주제 H2 2~3개/챕터
- 각 H2마다 KEY MESSAGE (완결 분석 문장 40~100자) — **So-What 사다리 L2 이상**에서 도출. 사실 나열(L1) 금지. 챕터당 최소 1개는 L3(2차 효과: 수혜/피해 주체) 도달
- 내러티브 3~4 단락 (비유·수치·맥락 필수). 수치는 **비교축 동반**(YoY/경쟁사/시장평균)
- 챕터 핵심 주장마다 **가장 강한 반론 1개**를 본문에서 처리 (반박 또는 조건부 인정)
- 핵심 사건은 **이해관계자 3렌즈**(당사자/경쟁자/수요자) 함의 검토
- 비교 데이터는 `makeTable()` / 프로세스·구조는 플로우차트 (visual-catalog.md 매핑)

### 시각화 계획표 (권장 — visual-catalog.md)

구조화를 마치면 챕터별 시각요소 계획을 표로 만든다 (의무 게이트는 아니지만 강력 권장):

```
| 챕터 | 내용 유형 | 시각요소 | 데이터 |
|---|---|---|---|
| II  | 기술 구조 흐름 | 플로우차트 (Pillow) | 아키텍처 4단계 |
| III | 플레이어 비교 | 표 (make_table) | 5사 × 4축 |
| V   | 투자 추이 | 가로 막대 (make_hbars) | 연도별 투자액 |
```

### Claims Ledger 동시 작성

본문 초안에 들어가는 모든 수치·사건·인용을 `claims.json` 에 등록하면서 쓴다. 스키마와 규칙은 `references/factcheck-pipeline.md` §1~2. **소스에 없는 수치는 만들지 않는다.**

---

## Phase 2.7: Deep Verification (할루시네이션 제거 게이트) — **필수, v0.9 신규**

> Anthropic 동적 워크플로 블로그의 **deep verification 패턴** 적용. 상세 절차는 `references/factcheck-pipeline.md`.

1. **추출**: 챕터 초안 전체에서 사실 주장(claim)을 전수 추출해 `claims.json` 과 대조, 누락분 등록.
2. **검증**: `verified` 가 아닌 claim 을 하나씩 WebSearch/WebFetch/소스 재독으로 확인.
   - 확인 성공 → `verified` (+source/url)
   - 합리적 계산/외삽 → `estimate` (+method/note, 본문에 `추정`/`est.` 표기)
   - 확인 실패·모순 → `removed` (**본문에서 해당 문장 수정/삭제**)
3. **회의 패스**: "비평가 모자"를 쓰고 verified 판정 표본을 재확인 (동적 워크플로 모드에서는 별도 skeptic 에이전트).
4. **기계 검증**: 빌드 후 Phase 6 에서 `verify_claims.py` 가 산출물 본문의 모든 유의미 수치가 ledger 와 정합하는지 검사. 실패 시 빌드 FAIL.

> 사실과 해석의 분리: 분석·전망은 claim 이 아니라 의견 — "~로 해석됨", "~할 가능성이 큼" 으로 쓴다. 의견을 사실처럼 단정하지 않는다.

---

## Phase 3: 시각화 생성 (표지 차트 + 본문 시각요소)

### NanumGothic 설치 (sandbox에서 GitHub raw 차단되므로 pip 패키지 사용)
```bash
pip install --break-system-packages cairosvg koreanize-matplotlib 2>&1 | tail -2
mkdir -p ~/.fonts
NANUM=$(python3 -c "import koreanize_matplotlib, os; print(os.path.dirname(koreanize_matplotlib.__file__))")/fonts/NanumGothic.ttf
cp "$NANUM" ~/.fonts/NanumGothic.ttf
fc-cache -f ~/.fonts/ 2>/dev/null
fc-list | grep -i nanum   # 확인
```

### 표지 차트 사양 (Pillow 권장)
- **권장**: Pillow(PIL) 직접 렌더링 (한글 폰트 문제 없음)
  - KR: NanumGothic + NanumGothicBold, 2000×~1025px, 배경 #FFFFFF
  - EN: DejaVu Sans, 2000×~1440px, 배경 #FFFFFF
- 대안: cairosvg + SVG (한글 missing glyph 이슈 주의)
  - SVG 텍스트의 `&` 문자는 반드시 `&amp;` 로 escape
- 설계 규격: `references/docx-chart-design.md`

### 본문 시각요소 (v0.9 확장 — 권장 가이드)

Phase 2 의 시각화 계획표에 따라 챕터별 시각요소를 생성한다. 유형별 매핑·Pillow 레시피(박스+화살표 helper)·팔레트(#1A3A6B 계열)·삽입 규격은 `references/visual-catalog.md`. 요약:
- 프로세스·인과 → 플로우차트 / 비교 → 표 / 수량·점유율 → 가로 막대 / 연대기 → 타임라인 / 포지셔닝 → 2×2
- PPTX 는 `make_table()`/`make_hbars()` XML 네이티브 우선, DOCX 는 Pillow PNG + 캡션
- 동일 차트는 KR/EN 두 벌 (KR=NanumGothic, EN=DejaVu Sans/Arial)

### DOCX 삽입 크기 계산 (필수)
```python
from PIL import Image
img = Image.open('cover_chart_kr.png')
h = int(630 * img.size[1] / img.size[0])
# → build_kr.js: transformation: { width: 630, height: h }
```

`width: 630` 고정 (A4 본문 폭 꽉 차게), height는 원본 비율로 계산.

---

## Phase 4: Word 문서 생성 (KR + EN)

```bash
NODE_PATH=/usr/local/lib/node_modules_global/lib/node_modules node -e "require('docx'); console.log('docx OK')"

# 1. 정본 템플릿 복사
cp references/build_kr.template.js build_kr.js
cp references/build_en.template.js build_en.js

# 2. 내용 치환 (제목, 본문, 챕터 등) — 헬퍼 시그니처는 변경 금지

# 3. 문법 체크 후 실행
node --check build_kr.js && NODE_PATH=/usr/local/lib/node_modules_global/lib/node_modules node build_kr.js
node --check build_en.js && NODE_PATH=/usr/local/lib/node_modules_global/lib/node_modules node build_en.js
```

### 파일명
- `{주제}_KR_Report_{YYYYMMDD}.docx`
- `{주제}_EN_Report_{YYYYMMDD}.docx`

### 절대 규칙
- `ShadingType.CLEAR` (SOLID 금지)
- 이미지: `width:630` 고정, height는 크롭 후 비율 계산 (A4 폭 꽉 차게), 그림 직후 캡션 1줄 `[그림 N] 제목 (출처)`
- 첫페이지 번호 미표시: `titlePage:true` + first footer 빈 것
- 폰트 KR: `Malgun Gothic`, EN: `Arial`
- JS 따옴표: 한국어 `'단어'` → `「단어」`
- 본문: bullets 금지, 산문 3~4 단락
- **챕터 헤딩 번호 체계 (v0.9.1)**: 본문 챕터는 `H1C()`(→`1. 제목`) / `H2C()`(→`1.1 소제목`) 헬퍼만 사용. 번호를 텍스트에 직접 쓰지 않는다(자동 카운터). Executive Summary·핵심 질문과 답변·맺음말·참고 자료만 번호 없는 `H1()`/`H2()`. 상세: `references/docx-build-pipeline.md` 말미
- 수치 밀집 절 끝 또는 문서 말미에 출처 섹션 (claims.json 의 source 와 정합)

---

## Phase 5: PowerPoint 생성 (KR + EN) — 오케스트레이터 사용

### STEP 1 — 정본 템플릿 복사 + 내용 치환

```bash
cp references/build_pptx_kr.template.py build_pptx_kr.py
cp references/build_pptx_en.template.py build_pptx_en.py
# 두 파일에서 toc_items, z1 챕터 라벨, z2 KEY MESSAGE, z4 본문 등을 주제에 맞게 치환
# ★ 주의: TOC(toc_items) 와 z1 좌측 라벨의 로마숫자 챕터가 1:1로 일치하도록!
```

### STEP 2 — 오케스트레이터 한 줄 실행 (KR/EN 각각)

```bash
bash references/build_pptx.sh kr build_pptx_kr.py {주제}_KR_Presentation_{YYYYMMDD}.pptx
bash references/build_pptx.sh en build_pptx_en.py {주제}_EN_Presentation_{YYYYMMDD}.pptx
```

> 게이트까지 한 번에 돌리려면 `build_pptx_checked.sh` 사용 (빌드 + gate_report.py 래퍼).

오케스트레이터 `build_pptx.sh` 가 결정론적으로 수행하는 단계:

| # | 단계 | 내용 |
|---|---|---|
| 1 | clean unpack | `unpacked_{lang}/` 디렉터리에 TEMPLATE.pptx 풀기 |
| 2 | add slides | `slideLayout5.xml` 기준으로 N_CONTENT 개 슬라이드 추가 |
| 3 | sldIdLst 보정 | 동적 rId 탐색 → 새 sldId 추가 + **closing slide를 마지막으로 이동** |
| 4 | layout 보정 | `slide3.xml.rels` 의 layout3 → layout5 (divider→contents) |
| 5 | run build_py | `TARGET_UNPACKED=unpacked_{lang} python3 build_pptx_{lang}.py` 로 슬라이드 XML 작성 |
| 6 | **verify_toc** | `verify_toc.py` 가 TOC ↔ 본문 챕터 정합성 검사 (실패시 빌드 중단) |
| 7 | clean | `clean.py` 로 미참조 파일 제거 |
| 8 | strip Google | `strip_google_extensions.py --unpacked` 로 GoogleSlides 잔존물 제거 |
| 9 | pack | `pack.py` 로 .pptx 패키징 |
| 10 | 최종 검증 | Google 잔존물 0개, metadata 0개, zip OK 확인 |

이 시퀀스는 모델이 임의로 우회하거나 단계를 건너뛸 수 없도록 외부화되어 있습니다. **오케스트레이터를 사용하지 않고 직접 unpack/pack을 시도하지 마세요.**

### STEP 3 — TEMPLATE.pptx / pptx 스킬 위치

오케스트레이터가 자동 탐색하지만, 환경변수로 명시할 수도 있습니다:
```bash
export TEMPLATE=$(find /sessions -maxdepth 6 -name "TEMPLATE*.pptx" 2>/dev/null | xargs ls -S | head -1)
export PPTX_SKILL=$(find /sessions -maxdepth 6 -name "pptx" -type d -path "*/skills/*" 2>/dev/null | head -1)
```

**가장 큰 TEMPLATE*.pptx** 가 우선 사용됩니다. 사용자가 업로드한 수정 템플릿이 있으면 자동으로 해당 파일을 선택합니다. `build_pptx.sh`의 동적 rId 탐색으로 OLD/NEW 템플릿 모두 자동 지원됩니다.

### 슬라이드 구성 (기본 13장 — 7챕터 정본 구조)
```
1   표지       (slideLayout1 / cover)
2   INDEX      (slideLayout4 — TOC 7개 챕터 I-VII)
3   I-① 개요   (slideLayout5 / contents)
4   I-② 현황
5   II-① 기술
6   II-② 데이터
7   II-③ 심화
8   III. 제품
9   IV. 응용
10  V. 산업 생태계
11  VI. 미래 전망
12  VII. Devil's Advocate
13  감사합니다 (slideLayout2 / closing — sldIdLst 마지막)
```

> 동적 워크플로로 챕터가 5~9개로 가변되면 전체 슬라이드 수도 달라집니다. `N_CONTENT = (전체 슬라이드 수) - 5` 로 맞춰 `build_pptx.sh` 에 전달하세요.

### 5-Zone 본문 좌표 (절대 변경 금지)
```
Zone 1 y=264100   섹션헤더 (좌:챕터명#1A3A6B bold / 우:번호)
Zone 2 y=641800   KEY MESSAGE 완결문장 (~임./~음.)
Zone 3 y=1455150  소주제 (algn=ctr, #1A3A6B bold, u=sng) + y=1773900 cy=25400 별도 밑줄 사각형
Zone 4 y=1850000  본문 (2단/표/막대차트/플로우차트 PNG)
Zone 5 y=4715475  Source — 해당 슬라이드 수치의 출처 (claims.json 정합)
```

### rr() 함수 — 드리프트 1순위 버그
```python
def rr(text, sz=None, bold=False, color=None, lang='ko', u='none'):
    sz_a = f' sz="{sz}"' if sz else ''
    b_a  = ' b="1"' if bold else ''
    u_a  = f' u="{u}"' if u else ''
    col  = f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>' if color else ''
    return f'<a:r><a:rPr lang="{lang}"{sz_a}{b_a}{u_a} dirty="0">{col}</a:rPr><a:t>{esc(text)}</a:t></a:r>'
```
- **`u='none'` 기본값 필수** — 빠뜨리면 slideLayout5 defRPr u="sng" 상속됨.
- **모든 Zone helper의 `<p:nvPr>`는 빈 `<p:nvPr/>`** — 다중 placeholder 충돌 → "읽을 수 없습니다" 에러.

### 맺음말 슬라이드 (고정 — 정본 템플릿에 이미 포함)
- 한국어: "감사합니다." + 3개 안내 + `신동형 | 010-2202-8761 | donghyung.shin@gmail.com`
- 영어: "Thank You." + 3개 안내 + `DH Shin | +82-10-2202-8761 | donghyung.shin@gmail.com`

---

## Phase 6: 품질 검증 (4중 게이트)

### 게이트 체인 (gate_report.py 가 합산)

```
build → ① verify_toc(구조) → ② verify_content(규칙+HEADNUM 헤딩번호) → ③ verify_claims(수치-출처)
      → ④ judge(quality_rubric.md 주관 채점) → gate_report.json
```

```bash
# PPTX (unpacked 기준)
python3 references/gate_report.py --unpacked unpacked_kr --lang kr \
    --skill-dir references --claims claims.json \
    --judge judge_verdict_kr.json --out gate_kr_pptx.json

# DOCX
python3 references/gate_report.py --docx {주제}_KR_Report_{YYYYMMDD}.docx --lang kr \
    --skill-dir references --claims claims.json --out gate_kr_docx.json
```

judge 채점: `verify_content.py --judge-extract judge_in_kr.json` 으로 텍스트를 덤프한 뒤, `references/quality_rubric.md` 의 8기준(16점 만점, 합격 ≥12 + 0점 없음)으로 채점해 `judge_verdict_kr.json` 작성. **단일 컨텍스트 모드에서는 "비평가 모자"를 쓰고 채점하되, #8(인사이트 깊이)을 후하게 주지 않도록 주의** (동적 워크플로에서는 별도 critic 에이전트가 수행).

### Word 추가 확인
- `node --check build_kr.js` 통과, `unzip -t {파일}.docx` 구조 OK
- 원문이 KR/EN이 아닐 때: `python3 references/verify_lang_purity.py --auto {파일}.docx` 통과
- ShadingType.CLEAR, 이미지 크롭 후 실제 높이, 첫페이지 번호 미표시

### PowerPoint 추가 확인 (오케스트레이터가 자동 수행, 수동 재확인)
- `unzip -t {파일}.pptx` 구조 OK
- `verify_lang_purity.py` 통과 (KR: 가나 0개·한자 ≤ 10 / EN: CJK·가나 0개)
- Google 잔존물 0개: `unzip -p file.pptx ppt/presentation.xml | grep -c 'customschemas\.google\|customooxmlschemas\.google'` → 0
- metadata 0개: `unzip -l file.pptx | grep -c 'ppt/metadata'` → 0
- 다중 `<p:ph>` 없음: `grep -c '<p:ph' unpacked_kr/ppt/slides/slide5.xml` ≤1
- 맺음말 슬라이드가 sldIdLst의 마지막에 있는지 확인

### Phase 6.5 — 재시도 루프 (loop-until-done)

`gate_report.json` 의 `pass=false` 이면 `fixes[]` 를 읽어 **실패한 슬라이드/섹션만** build 소스(build_*.js / build_pptx_*.py)와 claims.json 에 패치 후 재빌드. **상한 3회** — 초과 시 무한 루프 금지, 남은 fixes 를 사용자에게 NEEDS_REVIEW 로 보고.

---

## Phase 7: 결과물 전달

### 7-A — $WORKSPACE 적재 (영구 저장)

```bash
cp {주제}_KR_Report_{YYYYMMDD}.docx       "$WORKSPACE/"
cp {주제}_EN_Report_{YYYYMMDD}.docx       "$WORKSPACE/"
cp {주제}_KR_Presentation_{YYYYMMDD}.pptx "$WORKSPACE/"
cp {주제}_EN_Presentation_{YYYYMMDD}.pptx "$WORKSPACE/"
cp claims.json manifest.json              "$WORKSPACE/" 2>/dev/null || true
ls -la "$WORKSPACE"
```

> Phase 0 의 `$WORKSPACE` 가 이미 OneDrive `신동형인사이트\{주제}_{YYYYMMDD}` 이므로 별도 아카이브 복사가 필요 없습니다. (Phase 0 fallback 으로 세션 outputs 를 쓴 경우에만 `references/copy_to_insights.ps1` 또는 `copy_to_insights.sh {주제} {YYYYMMDD}` 로 OneDrive 보관을 시도합니다.)

### 7-B — present_files 안전 검증 (필수)

`present_files` 호출 **전에** 다음을 확인:

```bash
# 4개 파일 모두 $WORKSPACE 하위에 실재하는지
for f in "$WORKSPACE"/{주제}_*_{Report,Presentation}_*; do ls -la "$f" || echo "MISSING: $f"; done
# $WORKSPACE 가 /sessions/*/mnt/outputs 가 아닌지 (임시 경로 금지)
case "$WORKSPACE" in */mnt/outputs*) echo "⚠️ 임시 경로 — 카드 링크가 세션 후 깨짐";; esac
```

검증 통과 후에만 `present_files` 로 4개 파일을 동시 제시.

### 7-C — 사용자 보고

빌드 요약을 함께 보고: 파일 크기·페이지/슬라이드 수, gate_report 4게이트 결과, **claims 통계(총/verified/estimate/removed)**, judge 점수. 사용자가 .docx/.pptx 를 열어둔 상태로 복사가 IO Lock 에러를 내면 실패 파일명을 보고하고 앱을 닫게 한 뒤 재시도.

---

## Phase D: 동적 워크플로 오케스트레이션 (Dynamic Workflow)

> 트리거: `ultracode`, "워크플로로 만들어", "동적 워크플로", "use a workflow".
> 큰/고품질 4종 세트 작업에서, 단일 컨텍스트 대신 **다수 서브에이전트를 스크립트로 오케스트레이션**한다.
> 일상적 소형 작업은 기존 Phase 0~7 로 충분하다(워크플로는 토큰을 더 쓴다). 단, **소스가 3개 이상이거나 챕터가 8개 이상으로 예상되면 워크플로 모드를 사용자에게 먼저 제안**할 것.

### 왜 워크플로인가 (단일 컨텍스트의 4대 실패 모드 차단)
- **agentic laziness**: 7챕터를 한 컨텍스트에서 쓰다 중도 포기 → 챕터별 에이전트로 분리.
- **self-preferential bias**: 자기 초안을 자기가 검수하면 후해짐 → 작성자와 **다른** critic 에이전트가 채점.
- **goal drift**: 긴 대화·compaction 으로 제약(금지 형용사·산문체) 망각 → 각 에이전트가 깨끗한 컨텍스트.
- **hallucination**: 작성 컨텍스트가 자기 수치를 의심하지 않음 → **독립 검증 에이전트의 deep verification** (v0.9).

### 워크플로 파일
`references/build_4set.workflow.js` — **템플릿**이다(verbatim 스크립트 아님). 소스에 맞게 단계·프롬프트·모델을 조정해 작성한다. 입력은 전역 `args`(sources, titleKR, slug, langs, docTypes, maxRetries 등).

### 오케스트레이션 단계(패턴 매핑) — v0.9
```
A. CLASSIFY  (classify-and-act)        소스 분석 → 구조 결정.
   ★ 고정 7챕터/13장 제약을 푼다: 챕터 수를 소스 깊이에 따라 5~9개로 가변.
     VII(Devil's Advocate)는 비판 소재가 있을 때만. 모델 라우팅 결정.
   ★ v0.9: 챕터별 시각화 계획(visual-catalog.md 매핑)도 여기서 수립.
B. NORMALIZE (조건 분기)               비 한/영 소스만 Phase 1.5 정규화 노트+Glossary.
C. DRAFT     (fan-out-and-synthesize)  챕터당 에이전트 1개 병렬 초안(+claims 등록)
                                        → Exec Summary 합성.
C2. FACTCHECK(deep verification)       ★ v0.9 신규. claim 묶음(8개)당 검증 에이전트
                                        fan-out → verified/estimate/removed 판정.
                                        skeptic 에이전트가 verified 표본 재감사.
                                        removed 반영해 해당 챕터 수정.
D. VERIFY    (adversarial verification) 초안마다 '다른' critic 이 quality_rubric.md
                                        (8기준·16점, #8=인사이트 깊이)로 채점,
                                        불합격 챕터만 재작성(상한 2회).
E. BUILD     (fan-out)                  KR/EN × docx/pptx 병렬 빌드(정본 템플릿 적응,
                                        claims.json 동반).
F. GATE+RETRY(loop-until-done)          gate_report.py(toc+content+claims+judge)로 검증,
                                        실패분만 패치-재빌드(상한 maxRetries=3,
                                        초과 시 사람에게 NEEDS_REVIEW).
G. FINALIZE  (observability)            manifest.json(plan·claims 통계) 기록 + $WORKSPACE 저장.
```

### 가변 챕터 구조와 기존 정합성 규칙
워크플로가 챕터 수를 동적으로 정하더라도 **TOC(slide2) ↔ 본문 z1 로마숫자 1:1 일치**는 그대로 강제된다. `build_pptx.sh` 의 `verify_toc.py` 와 `gate_report.py` 가 가변 챕터 수에서도 검사하므로, classify 단계에서 정한 `chapters[]` 의 로마숫자를 TOC·본문 양쪽에 동일하게 흘려보낼 것. PPTX 슬라이드 수가 13장에서 벗어나면 `N_CONTENT` 를 (전체 - 5)로 맞춰 `build_pptx.sh` 에 전달한다.

### 품질 게이트(동봉)
`references/` 에 `verify_content.py`(규칙 게이트), `verify_claims.py`(수치-출처 게이트, v0.9), `gate_report.py`(toc+content+claims+judge 합산), `build_pptx_checked.sh`(빌드+게이트 래퍼), `quality_rubric.md`(critic 채점 기준)가 포함된다. 워크플로 없이 기존 Phase 5 를 쓸 때도 `build_pptx.sh` → `build_pptx_checked.sh` 로 바꾸면 게이트가 붙는다.

### 실행·비용 메모
- 시작: 프롬프트에 `ultracode` 포함 또는 "워크플로로 4종 세트 만들어".
- 토큰 예산: "10k 토큰으로" 처럼 상한 지시 가능. 동시 에이전트 ≤16, 총 ≤1000.
- FACTCHECK 비용 조절: claim 이 적으면(<15개) 묶음 검증 1~2개 에이전트로 축소, skeptic 생략 가능.
- 먼저 작은 소스로 1회 시범 실행해 비용을 가늠한 뒤 본 작업에 적용 권장.
- 저장/공유: 만족스러운 실행은 `/workflows` 에서 `s` 로 저장하거나 본 스킬에 동봉된 채로 재사용.

---

## ✅ 최종 자기 점검 체크리스트

**드리프트 방지**
- [ ] docx 스킬 / pptx 스킬을 직접 호출하지 않았다
- [ ] `references/build_*.template.*` 4개를 모두 읽고 적응했다
- [ ] 필수 reference `.md` 7개를 시작 시점에 모두 읽었다
- [ ] PPTX는 `bash references/build_pptx.sh`(또는 `build_pptx_checked.sh`) 오케스트레이터로만 빌드했다
- [ ] 원문 언어가 KR/EN이 아닐 때 Phase 1.5(언어 정규화)를 거쳤다
- [ ] 4개 산출물 모두 `verify_lang_purity.py` 가 PASS

**할루시네이션 차단 (v0.9)**
- [ ] `claims.json` 이 존재하고 모든 본문 수치·사건·인용이 등록되어 있다
- [ ] removed claim 이 본문에 남아 있지 않다 (`verify_claims.py` PASS)
- [ ] estimate claim 은 본문에 `추정`/`est.` 표기가 있다
- [ ] 기억(사전지식)에서 꺼낸 수치를 웹 확인 없이 쓰지 않았다
- [ ] 사실과 해석이 문형으로 구분된다 ("~임" vs "~로 해석됨")

**분석력·인사이트 (v0.9)**
- [ ] 모든 KEY MESSAGE 가 So-What L2 이상, 챕터당 1개 이상 L3 도달
- [ ] 핵심 주장마다 반론 1개 이상 처리
- [ ] 수치에 비교축(YoY/경쟁사/시장평균) 동반
- [ ] judge 채점(quality_rubric 8기준) 총점 ≥12, 0점 없음

**시각화 (권장)**
- [ ] Phase 2 시각화 계획표를 만들었고 챕터별 시각요소(표·차트·플로우차트)를 검토했다
- [ ] 프로세스·구조 설명이 줄글로만 길게 이어진 챕터가 없다
- [ ] 모든 그림·차트에 캡션/출처가 있다

**Word KR/EN**
- [ ] 표지: PB 없음, Source/해시태그 없음, 제목+부제 콜론 통합 sz=44
- [ ] Executive Summary: 단일 textBox + SL 4개 서브섹션
- [ ] 본문: bullets 없음, 산문 3~4 단락
- [ ] 챕터 헤딩 `1. / 1.1` 자동 번호 (H1C/H2C 사용, verify_content HEADNUM PASS)
- [ ] ShadingType.CLEAR
- [ ] 폰트 KR=Malgun Gothic, EN=Arial
- [ ] 한국어 차트 NanumGothic
- [ ] 이미지 크기 크롭 후 실제값
- [ ] `unzip -t` 통과

**PowerPoint KR/EN (오케스트레이터가 자동 검사하는 항목 포함)**
- [ ] TEMPLATE.pptx 기반 unpack/pack (python-pptx 미사용)
- [ ] 모든 Zone helper의 `<p:nvPr>` 빈 태그
- [ ] `rr()` 의 `u='none'` 기본값
- [ ] Zone 3 solidFill 없음 + 별도 밑줄 사각형
- [ ] Zone 1~5 모두 존재, KEY MESSAGE 완결문장, Zone5 Source 표기
- [ ] 영어본 전화번호 `+82-10-2202-8761`
- [ ] **맺음말 슬라이드가 sldIdLst의 마지막** (오케스트레이터 자동)
- [ ] **slide3 layout3→layout5 보정 완료** (오케스트레이터 자동)
- [ ] **`verify_toc.py` 가 PASS** — TOC 챕터 수 = 본문 챕터 수
- [ ] **Google 잔존물 0개** (오케스트레이터 자동 검사)
- [ ] PDF 변환 시각 검증 또는 실제 PowerPoint에서 열림 확인

**저장·전달**
- [ ] Phase 0 `$WORKSPACE` (OneDrive 영구 폴더)에 4종 + claims.json 저장
- [ ] Phase 7-B 안전 검증 후 `present_files` 호출
- [ ] gate_report 4게이트 결과와 claims 통계를 사용자에게 보고

체크박스 중 하나라도 비어 있으면 결과물은 신동형 인사이트 정합성에서 벗어난 것입니다.
