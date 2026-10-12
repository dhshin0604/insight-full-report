---
name: report-harness
description: 여러 에이전트가 조사, 집필, 검증을 나눠 맡는 큰 보고서를 MD 토의본과 사용자 확인을 거쳐 게이트를 통과한 Word 보고서와 이미지 덱으로 낼 때 사용(조사 fan-out, 2차 검증, 재시도 3회 이하의 게이트, 독립 검토 포함). 소스 몇 개로 Word, PPTX 4종을 빠르게 만들 때는 generate-full-report 를 씀.
---

# 보고서 하네스 (report-harness) v1.0

> 결과물 : ① MD 토의본 ② Word 보고서(.docx, 합니다체 산문, 게이트 통과) ③ 이미지 덱(PDF, PPTX, PNG zip, image-deck 스킬)
> 순서 : 착수 질문 → 조사 → 2차 검증 → **MD 전달 → 사용자 확인** → 빌드(그림 → Word ∥ 덱) → 게이트 → 독립 검토 → 전달
> 방법론 전체 : `references/HARNESS.md` (7요소, 생산 하네스 P0~P8, 제작 하네스 M1~M10, 분업, 패키징, 공통 규칙, 게이트 체인, 학습 루프)
> 경로 : `{스킬}` = `${CLAUDE_SKILL_DIR}` (Claude Code, Cowork 는 실제 경로로 바꿔 보여 줌. 그대로 보이면 이 SKILL.md 가 있는 폴더). 스크립트는 모두 자기 위치 기준으로 파일을 찾음

## 0. GATE 0 : 바로 멈출 것

| 하려 한 일 | 대신 할 일 |
|---|---|
| 사용자가 MD 토의본을 확인하기 전에 Word 나 덱을 만들려 함 | STOP. MD 를 전달하고 답을 기다림(사용자가 「한 번에」를 고른 경우만 예외) |
| 기억(사전지식)의 수치, 날짜, 이름을 원문 확인 없이 쓰려 함 | STOP. 원문을 열어 확인하고 claims 에 등록. 못 찾으면 「미발견」 |
| 조사한 에이전트에게 자기 결과를 검증시키려 함 | STOP. 2차 검증과 검토는 다른 에이전트에게 맡김 |
| 원고 제목, 질문, 캡션에 번호(1., 1.1, Q1., [표 1])를 직접 쓰려 함 | STOP. 번호는 `build_docx.js` 가 붙임 |
| selfcheck 가 FIX 인데 빌드하려 함 | STOP. `!!` 줄부터 고침 |
| 게이트 재시도가 3회를 넘음 | STOP. 남은 fixes 를 NEEDS_REVIEW 로 사용자에게 보고 |
| 형제 스킬(generate-full-report, image-deck)이 없는데 게이트나 덱을 건너뛰고 「통과」라고 보고하려 함 | STOP. 「게이트 없음」 「덱 없음」을 분명히 알리고 설치를 안내(5-2) |
| 원고나 예시에 실제 개인 이름, 연락처를 넣으려 함 | STOP. 작성자 정보는 profile.json 에서만 읽음 |

## 1. 원칙 (어기면 다시 씀)

- **사람 확인 지점** : 되돌리기 비싼 곳(MD 토의본 뒤, 단계가 바뀔 때)에서 멈추고 확인을 받음. 토의 안건은 번호와 잠정안을 붙여 「잠정안대로 확정」 한 줄로 답할 수 있게 냄
- **작성자와 검증자 분리** : 조사 ≠ 2차 검증, 원고 ≠ 검토. 검토는 확인한 오류만 최소 수정
- **원장** : 본문의 모든 수치는 `claims.json` 에 출처와 함께 있음. 상태는 verified, estimate(본문에 「추정」), removed(본문에 남기지 않음)
- **단계 분리** : 현황 → 분석 → 진단 → 제언을 섞지 않음. 현황 단계는 판정, 평가, 제언, 점수 없음(`selfcheck --mode status`)
- **금지어 정본** : `references/lexicon.json`(과장, 평가어, AI 티 문형, 가리킴, 자기 해설, 팀 금지어, bullet, 줄표). 고칠 필요가 있으면 lexicon 을 바꾸고 두 사본을 같게 맞춤
- **표기** : 날짜 MD `2026-10-12` / 덱 `2026.10.12` / Word `2026년 10월 12일`. 원문 인용은 「」, 작은따옴표 인용 없음, 줄표(U+2014) 없음
- **출처의 주인** : 「표준」 「원칙」은 누구의 것인지, 기관 문서는 적힌 이름, 금액, 단계만 씀. 발행 기관의 관점에 기울지 않음
- **수정 요청** : 문구만 바꾸지 않고 제목, 논지, 구조에 미치는 영향을 먼저 보고 반영함
- **재시도 상한** : 게이트 3회, critic 재작성 2회. 넘으면 사람에게

## 2. 생산 하네스 P0~P8

| 단계 | 하는 일 | 산출 | 넘어가는 조건 |
|---|---|---|---|
| P0 착수 질문 | 한 번에 물음 : ① 대상·범위(경계, 인접 대상 안/밖) ② 진행 순서(MD 먼저 → 확인 뒤 빌드가 기본 / 한 번에) ③ 산출물(MD, Word, 이미지 덱, 언어 KR·EN) ④ 양식 원본(직전 편 파일) | 작업 폴더, 결정 메모 | 범위, 순서, 형식 확정 |
| P1 정본 로드 | 이 SKILL.md, `references/HARNESS.md`, `references/content-schema.md` 를 읽고 작성자 문체 정리본·선호 규칙(있으면)을 읽음. 직전 편 파일은 `ref/` 에 둠. 형제 스킬 경로 확인(5-2) | | 3절 브리프 목록과 4절 명령을 설명할 수 있음 |
| P2 조사 fan-out | `briefs/BRIEF.md` 를 채워 작업 폴더에 두고 갈래(D1~Dn)마다 에이전트 하나. WebSearch, WebFetch 만, 갈래당 검색 30회 안팎 | `research/D<n>_*.md` | 행마다 출처, 날짜, URL, 태그 |
| P3 2차 검증 | 조사하지 않은 에이전트(S1~Sn)가 핵심 수치, 날짜, 소재, 단계, 금액 층위를 원문으로 다시 확인. 판정 5종(확인, 수정, 상충 유지, 부재 유지, 미확인) | 판정표 | 바뀐 값은 MD 부록에 기록 |
| P4 MD 토의본 | `briefs/INTEG_BRIEF.md`(고정 용어, 채택값, 문체, 블록 배정) → 블록 작성 → 통합 → 검토(`briefs/REVIEW.md`) → 수정 → 전달. 끝에 토의 안건과 잠정안 | `{대상}_{시리즈}_{단계}_v0.1.md` | **사용자 확인 대기** |
| P5 빌드 | 더미 원고로 파이프라인 먼저 시험(예시 모듈) → 그림 담당이 먼저 렌더하고 `figs/_DONE` → Word 원고(W1~Wn)와 덱 파트(P1~Pn) 병렬 | `content_*.py`, `figs/*.png`, 덱 PNG | 파트마다 selfcheck PASS, 덱 QA OK |
| P6 게이트·재시도 | 4절 명령 순서. `gate.json` 의 `fixes[]` 만 패치해 다시 빌드, 3회 이하. PDF 로 바꿔 쪽 그림 확인 | `gate.json` | `pass: true`, 쪽 확인 OK |
| P7 독립 검토 | 만들지 않은 검토 에이전트가 MD, 원문과 대조. 확인한 오류만 최소 수정, 수치는 원값으로 독립 재계산 | 수정 목록 | 미해결 0, 남으면 NEEDS_REVIEW |
| P8 전달 | docx, PDF, 덱(PDF, PPTX, PNG zip), MD, claims.json 을 전달하고 연결 폴더가 있으면 저장 | | 끝 메시지는 짧게(무엇, 파일, 게이트 결과, claims 통계, 남은 확인 1~3개) |

- 작업 공간은 초기화될 수 있음. 단계마다 산출물(MD 포함)을 전달해 둠

## 3. 역할과 브리프

규칙을 프롬프트에 길게 쓰지 않음. 오케스트레이터가 뼈대를 작업 폴더에 복사해 `{ }` 를 채우고, 에이전트에게는 「`{파일}` 을 처음부터 끝까지 읽고 그대로 따를 것. 담당은 {코드}」 한 줄만 줌.

| 역할 | 코드 | 브리프 뼈대 | 산출 |
|---|---|---|---|
| 조사 | D1~Dn | `references/briefs/BRIEF.md` | `research/D<n>_*.md` |
| 2차 검증 | S1~Sn | `references/briefs/BRIEF.md` 5절 | 판정표 |
| MD 블록 작성 | B1~Bn | `references/briefs/INTEG_BRIEF.md` | `md/B<n>_*.md` |
| 그림 | FIG | `references/briefs/BRIEF_FIG.md` | `figs/*.png`, `figs/_DONE` |
| Word 원고 | W1~Wn | `references/briefs/BRIEF_WORD.md` | `content_front.py`, `content_ch<n>.py` |
| 덱 파트 | P1~Pn | `references/briefs/BRIEF_DECK.md` (+ image-deck SKILL.md) | 파트 PNG, `qa_report.json` |
| 검토, 독립 재계산 | R1~Rn, N1 | `references/briefs/REVIEW.md` | 수정 표, 재계산 표 |
| critic(선택) | | quality-core 스킬의 `{스킬}/../quality-core/references/quality-rubric.md` | 16점 채점(12점 이상, 0점 없음) |

- 동시 에이전트는 16개 이하. rate limit(429)이 나면 같은 지시로 모델만 바꿔 다시 실행
- 순서가 필요한 병렬 작업은 완료 표시 파일로 맞춤(그림 `_DONE` → 덱)

## 4. 원고 → Word 빌드

원고는 파이썬 모듈(블록 dict)로 쓰고, JSON 으로 모은 뒤 Word 로 빌드함. 형식은 `references/content-schema.md`, 예시는 `references/examples/`.

| 파일 | 하는 일 |
|---|---|
| `references/wb.py` | 원고 헬퍼 : `P`, `FIG`, `TBL`, `BOX`, `QUOTE`, `NOTE`, `W`(표 폭, 합 9026), `chapter`, `sec`, `claim` |
| `references/selfcheck.py` | 원고 자체 점검(금지어, 날짜, 표 규격, 미등록 수치, claim id 등). 마지막 줄 PASS / FIX n |
| `references/assemble.py` | 모듈 → `content.json` + `claims.json`. id 중복 검사, 메타 claim(Z001 작성일·기준일, Z002 헤딩 번호, Z003 그림·표·질문 번호, Z004 참고 자료) 자동 추가 |
| `references/build_docx.js` | `content.json` → `.docx`. 표지(제목, 날짜와 작성자 줄, 표지 그림이 한 쪽), ES 박스, 핵심 질문과 답변, 「1.」 장 「1.1」 절 + KEY MESSAGE, 반론 장, 맺음말, 참고 자료 |
| `references/profile.json` | 작성자 템플릿(빈 값). 표지 줄에 AUTHOR_KR, AUTHOR_EN 을 씀 |

명령 순서 (작업 폴더에서, 원고 모듈이 작업 폴더에 있을 때)

```bash
H={스킬}/references                         # 이 스킬의 references 폴더
G={스킬}/../generate-full-report/references  # 형제 스킬 (게이트)

# 1) 원고 자체 점검 : 마지막 줄 PASS 가 나올 때까지 고침
python3 "$H/selfcheck.py" content_front content_ch1 content_ch2 --mode status   # 현황 단계
#   분석·진단·제언 단계는 --mode analysis (평가어 검사 안 함), 영문은 --lang en

# 2) 조립 : content.json + claims.json
python3 "$H/assemble.py" --front content_front --chapters content_ch1,content_ch2 \
    --out content.json --claims claims.json --date "2026년 10월 12일"

# 3) Word 빌드 : 작성자는 profile.json (없으면 종료코드 2 와 해결 안내)
NODE_PATH="$(npm root -g)" node "$H/build_docx.js" content.json report.docx

# 4) 게이트 : pass 가 true 여야 함
python3 "$G/gate_report.py" --docx report.docx --lang kr --skill-dir "$G" \
    --claims claims.json --out gate.json

# 5) 쪽 확인 : PDF 로 바꿔 앞 쪽들을 그림으로 떠서 눈으로 봄
soffice --headless --convert-to pdf report.docx
pdftoppm -r 50 -png -f 1 -l 6 report.pdf page
```

- 프로필 : 환경변수 `PROFILE` → 작업 폴더 `./profile.json` → `{스킬}/references/profile.json` → 형제 스킬 `generate-full-report/references/profile.json` 순으로 찾고, AUTHOR_KR 과 AUTHOR_EN 이 모두 찬 첫 파일을 씀. 환경변수 `PROFILE_AUTHOR_KR`, `PROFILE_AUTHOR_EN` 도 받음
- 예시로 파이프라인 먼저 시험 : `cd {스킬}/references/examples` 에서 위 1)~4)를 `--out` 과 출력 파일만 작업 폴더로 바꿔 실행. 예시 그림은 `examples/figs/` 에 들어 있음(`make_figs.py` 로 다시 그릴 수 있음)
- 게이트 실패 시 `gate.json` 의 `fixes[]` 를 읽고 원고 모듈(또는 claims)만 고친 뒤 1)부터 다시. 3회를 넘으면 NEEDS_REVIEW
- 영문 보고서 : `META["lang"] = "en"` 이면 글꼴 Arial, 날짜 「October 12, 2026」, 고정 라벨이 영문으로 바뀜. 게이트는 `--lang en`

### 4-1. 게이트 함정

| 증상 | 원인 | 대응 |
|---|---|---|
| `NUM_UNREG 1.1` 같은 헤딩 번호 | 메타 claim 없이 빌드함 | assemble.py 를 거친 claims.json 을 씀 |
| `NUM_UNREG` 날짜의 월, 일 | 본문에 조사 기준일 등 날짜를 씀 | `META["base_date"]` 에 넣거나 claim 으로 등록 |
| `EST_UNMARKED` | estimate 수치 앞뒤 30자 안에 「추정」 없음 | 같은 문장 가까이에 「추정」 |
| `HEADNUM` | 제목에 번호를 직접 씀, 또는 HEAD_EXEMPT 에 없는 번호 없는 헤딩 | 번호를 지우고 빌드에 맡김. 맺음말 아래 헤딩 이름을 바꾸지 않음 |
| `CJK_KR` | 괄호 바로 뒤가 아닌 한자 | 한글로 쓰고 원문은 괄호 바로 안에 |
| `BULLET` 「·」 | 가운뎃점 | 쉼표, 「와/과」 로 이음 |

## 5. 덱과 형제 스킬

### 5-1. 덱은 image-deck 스킬로

- 덱은 이 스킬이 렌더하지 않음. image-deck 스킬(`{스킬}/../image-deck/SKILL.md`)을 읽고 그 렌더러 `deck_core.py` 의 `render_all` 과 `bundle.py` 를 씀
- 파트 나눔과 원고 규칙은 `references/briefs/BRIEF_DECK.md`. 숫자는 확인된 MD 토의본의 채택값 그대로
- 그림은 Word 와 덱이 함께 씀(`references/briefs/BRIEF_FIG.md`). 그림 담당이 먼저 끝내고 `figs/_DONE` 을 남김

### 5-2. 형제 스킬 경로 찾기

```bash
ls {스킬}/../generate-full-report/references/gate_report.py   # 게이트
ls {스킬}/../image-deck/references/deck_core.py              # 덱 렌더러
```

- 둘 다 있으면 그대로 씀. 없으면 멈추고 알림 : 「이 스킬은 insight-full-report 플러그인의 generate-full-report(게이트)와 image-deck(덱)을 함께 씀. 플러그인을 통째로 설치하거나 세 스킬 폴더(generate-full-report, image-deck, report-harness)를 같은 상위 폴더에 함께 올릴 것」
- 게이트가 없는 상태에서 만든 Word 는 「게이트 없음」으로 표시해 전달함. selfcheck PASS 만으로 「게이트 통과」라고 쓰지 않음

## 6. 단계 루프 : 현황 → 분석 → 진단 → 제언

| 단계 | 묻는 것 | 쓰지 않는 것 | selfcheck |
|---|---|---|---|
| 현황 | 무엇이 어디에 몇 개 있고, 무엇이 이어져 있고, 문서에 무엇이 적혔는가 | 판정, 평가어, 제언, 점수 | `--mode status` |
| 분석 | 셈과 비교로 무엇이 보이는가(비교축 하나 이상) | 근거 없는 판정 | `--mode analysis` |
| 진단 | 기준(누구의 기준인지 밝힘)에 비춰 어디가 어떤가 | 기준 없는 평가 | `--mode analysis` |
| 제언 | 진단에서 나온 차이마다 무엇을 할 것인가(1:1 대응) | 진단과 이어지지 않는 제언 | `--mode analysis` |

- 단계마다 P2~P8 을 다시 돌고, 단계마다 MD 토의본과 사용자 확인을 둠. 사용자가 한 번에 요청하면 단계 확인을 생략함
- 앞 단계에서 확인된 MD 가 다음 단계의 정본임. 앞 단계 값을 바꿀 일이 생기면 토의 안건으로 올림

## 7. 겪은 문제와 대응

| 문제 | 대응 |
|---|---|
| 작업 공간 초기화로 파일이 사라짐 | 단계마다 산출물(MD 포함)을 전달해 둠. 다음 편 시작 때 직전 편 파일을 다시 받음(착수 질문 ④) |
| 조사 갈래가 검색 한도를 먼저 다 써 뒤 갈래가 못 찾음 | 세션 검색 한도를 갈래 수로 나눠 브리프에 적음(갈래당 30회 안팎). 공식 사이트와 아는 URL 은 바로 열람 |
| 에이전트 rate limit(429) | 같은 지시로 모델만 바꿔 다시 실행 |
| Word 미리보기에서 한글 글꼴이 바뀌거나 깨짐 | 미리보기 전용으로 fontconfig 별칭을 둠(아래). 문서의 글꼴 선언(Malgun Gothic)은 바꾸지 않음 |
| 표지 제목 둘째 줄에서 한 단어만 다음 줄로 넘어감 | 제목 줄을 26자 안팎으로 줄이거나 subtitle 로 옮김 |
| 같은 기관, 매체, 외국 이름의 한글 표기가 파일마다 다름 | `INTEG_BRIEF.md` 고정 용어 표에 올리고 블록마다 따름 |
| 덱 날짜에 하이픈이 섞임 | 렌더 전 정규식으로 `2026.10.12` 형식으로 바꿈 |

미리보기 글꼴 별칭 (Malgun Gothic 이 없는 리눅스에서, 미리보기를 만드는 동안만)

```bash
PREVIEW_HOME="$(mktemp -d)"; mkdir -p "$PREVIEW_HOME/.config/fontconfig"
cat > "$PREVIEW_HOME/.config/fontconfig/fonts.conf" <<'EOF'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <alias binding="same"><family>Malgun Gothic</family><prefer><family>Noto Sans CJK KR</family></prefer></alias>
  <alias binding="same"><family>맑은 고딕</family><prefer><family>Noto Sans CJK KR</family></prefer></alias>
</fontconfig>
EOF
HOME="$PREVIEW_HOME" soffice --headless --convert-to pdf report.docx
```

## 8. 환경 준비

| 항목 | 확인 | 없을 때 |
|---|---|---|
| Python 3.9 이상 | `python3 --version` | |
| Node 18 이상 + npm 패키지 docx | `NODE_PATH="$(npm root -g)" node -e "require('docx')"` | `npm install -g docx` |
| LibreOffice, poppler (쪽 확인용) | `soffice --version`, `pdftoppm -v` | 패키지 관리자로 설치. 없으면 쪽 확인을 건너뛰었다고 보고 |
| Playwright chromium (그림, 덱) | `python3 -c "import playwright"` | `pip install playwright && python3 -m playwright install chromium` |

## 최종 점검표

- [ ] 착수 질문 4개에 답을 받았음(범위, 순서, 산출물, 양식 원본)
- [ ] 조사 갈래마다 브리프와 검색 예산이 있었고, 2차 검증은 다른 에이전트가 했음
- [ ] MD 토의본을 전달하고 사용자 확인을 받은 뒤 빌드했음(「한 번에」를 고른 경우 제외)
- [ ] 원고 모듈 selfcheck 마지막 줄이 PASS 임(단계에 맞는 `--mode`)
- [ ] assemble 로 만든 claims.json 을 썼고, removed 가 본문에 없고, estimate 옆에 「추정」이 있음
- [ ] `gate.json` 이 `pass: true` 임(재시도 3회 이하). 게이트가 없었다면 그렇게 적었음
- [ ] PDF 쪽 그림으로 표지, ES, 헤딩, 표, 그림 모양을 눈으로 확인했음
- [ ] 덱은 image-deck `render_all` QA 오류 0, PNG 를 한 장씩 확인했음
- [ ] 만들지 않은 에이전트가 검토했고, 미해결 항목은 NEEDS_REVIEW 로 보고했음
- [ ] 산출물에 자리표시(`{AUTHOR_KR}` 등), 개인 연락처, 줄표가 없음
