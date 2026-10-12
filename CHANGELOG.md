# 변경 이력 / Changelog

형식 : [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/), 버전 : [Semantic Versioning](https://semver.org/lang/ko/)

## [1.0.0] - 2026-10-12

스킬 4개 묶음으로 확장한 첫 정식판. 다른 사람이 받아서 바로 설치하고 시험할 수 있게 설치 경로, 환경 점검, 자가 시험, 업로드용 zip 을 갖춤.

### 추가 (Added)

- **`image-deck` 스킬** : 확정된 원고(MD)를 1920×1080 5-Zone 이미지 슬라이드로 렌더
  - 컴포넌트 : 수치 타일, 카드, 표, 가로 막대, 타임라인, 2×2, 계층, 흐름, 꼬리표, 비주얼 요약(As-Is → To-Be 도해와 판정 한 줄), 시사점 3축 표
  - 자동 QA : 본문·도해 넘침, 헤드라인 3줄, 19px 미만 글자, 쪽 밖 글자, 출처와 본문 겹침, 이미지 로드 실패, 자리표시 잔존(오류) / 표 9행 이상, 빈 공간, 줄표, 금지어, 표만 3장 연속, 섹션 컴포넌트 3종 미만(경고)
  - 팔레트 검사 : WCAG 대비, 의미색 사이 ΔE, 적록색약 모사 ΔE
  - 묶기 : PDF, PPTX(쪽마다 그림 한 장), PNG zip. 쪽 수를 PNG 수와 대조
  - 가상 데이터 데모 15쪽(`examples/demo_deck.py`)
- **`report-harness` 스킬** : 여러 에이전트가 조사·집필·검증을 나눠 맡는 큰 보고서용
  - 생산 하네스 P0~P8 : 착수 질문 → 조사 fan-out → 2차 검증 → MD 토의본 → **사용자 확인** → 빌드 → 게이트(재시도 3회 이하) → 독립 검토 → 전달
  - 브리프 뼈대 6종(`briefs/`), 방법론 문서 `HARNESS.md`(하네스 7요소, 제작 하네스 M1~M10, 게이트 체인, 학습 루프)
  - 원고 헬퍼 `wb.py`, 자체 점검 `selfcheck.py`(현황·분석 모드), 조립 `assemble.py`(메타 claim Z001~Z004 자동 추가), Word 빌더 `build_docx.js`(content.json → .docx)
  - 가상 예시 원고(B시 공공자전거)와 그림
- **공용 금지어 사전 `lexicon.json`** : 과장(오류·경고), 평가어(현황 모드), AI 티 문형, 장 사이 가리킴, 자기 해설, 팀 금지어(`user_banned`), 글머리표, 줄표. generate-full-report 와 report-harness 에 같은 사본을 두고 자가 시험이 같은지 검사
- **`verify_content.py` 검사 추가** : `DASH`(줄표, 영문 오류·한글 경고), `AI_TONE`(경고), `POINTER`(경고), `BANNED`(오류). `lexicon.json` 의 과장어 목록과 글머리표 문자를 읽음
- **`ooxml_tools.py`** : 표준 라이브러리만으로 PPTX 를 풀고(unpack, zip-slip 방지) 슬라이드 추가(add-slides), 순서 조정(move-last), 레이아웃 교체(set-layout), 고아 파트 정리(clean), 묶기(pack, XML 파싱 검증), 구조 점검(check)
- **설치·배포 도구**
  - `.claude-plugin/marketplace.json` (마켓플레이스 이름 `wroding`)
  - `scripts/doctor.py` : 스킬별 필요한 프로그램·패키지·글꼴 점검과 OS별 설치 명령
  - `scripts/selftest.py` : 가상 프로필로 네 스킬을 임시 폴더에서 끝까지 빌드하고 게이트까지 돌림. 일부러 틀린 원고로 게이트가 실제로 잡는지도 확인. 정적 검사(매니페스트, SKILL.md 머리말, 참조 파일, 줄표, 개인정보·비밀값 패턴, 문법, 패키지 크기)
  - `scripts/package.py` : claude.ai 업로드용 플러그인 zip 과 스킬별 zip, 구조 검사, 재현 가능한 zip
- `plugin.json` : `displayName`, `homepage`, `repository`, `keywords`

### 바뀜 (Changed)

- **PPTX 빌드가 외부 pptx 스킬 없이 돌아감** : `build_pptx.sh` 가 `unpack.py`, `add_slide.py`, `clean.py`, `pack.py` 대신 `ooxml_tools.py` 를 씀. 해당 스크립트가 예전 경로에 없는 환경에서도 빌드됨. `TEMPLATE`, `PYTHON`, `N_CONTENT`, `LOGO` 환경변수를 받고, GNU 전용 명령(`stat -c`, `sed -i`, `unzip`)을 쓰지 않아 macOS 와 Git Bash 에서도 동작
- **저장 위치(Phase 0)** : 특정 환경 전용 경로 대신 실행 환경(Claude Code, Claude 앱, Cowork)별 표와 스크립트. `profile.json` 의 `WORKSPACE_ROOT`, `WORKSPACE_DIRNAME` 을 읽음
- **Word 템플릿** : 출력 경로를 인자나 `OUT` 환경변수로, 표지 그림을 `COVER_IMG` 환경변수로 받음. 표지 그림 높이를 PNG 원본 비율로 계산. 세션에 묶인 고정 경로를 없앰
- **정본 템플릿 4개의 예시 원고가 자기 게이트를 통과** : 괄호 밖 한자는 한글로, 가운뎃점·글머리표는 쉼표로, 과장 표현과 줄표를 뺌
- `apply_profile.py` : 선택 키 `BRAND`(이미지 덱 표지 라벨)
- `profile.json` 예시를 가상 값으로 통일(홍길동, 010-0000-0000, name@example.com)
- SKILL.md 4개 : 어느 스킬을 언제 쓰는지(스킬 경계)를 서로 맞추고, 스크립트 경로를 스킬 폴더(`${CLAUDE_SKILL_DIR}`) 기준으로 적음
- 확인 명령을 OS 와 무관하게 : `unzip -t` 대신 `python3 -m zipfile -t`, `ooxml_tools.py check`
- 배포 파일 전체에서 줄표(U+2014)를 뺌. 배너를 v1.0 으로

### 고침 (Fixed, 독립 검증에서 찾은 것)

- **게이트가 돌지 못하면 통과로 치던 문제** : `gate_report.py` 가 대상 파일이 없거나(종료코드 2), 하위 게이트가 리포트를 못 내거나, `claims.json`·judge 결과 형식이 틀리면 `GATE_ERROR` 로 실패 처리
- **Windows(cp949, cp1252)에서 출력 때문에 스크립트가 멈추던 문제** : 모든 파이썬 스크립트가 표준 출력을 UTF-8 로 맞추고, `build_pptx.sh`·`build_pptx_checked.sh` 가 `PYTHONUTF8=1` 을 설정하고, `gate_report.py` 가 하위 출력을 UTF-8 로 읽음. 예전에는 이 환경에서 내용 게이트가 멈추면 「건너뜀」으로 통과 처리될 수 있었음
- **슬라이드 순서** : `verify_toc.py`, `verify_content.py` 가 파일 번호가 아니라 실제 보이는 순서(`sldIdLst`)로 검사. `N_CONTENT` 가 빌드 스크립트와 다르면 「빈 슬라이드」 또는 「슬라이드 목록에 없는 슬라이드」로 빌드를 멈춤(예전에는 챕터가 빠진 덱이 통과할 수 있었음). 로마숫자 VIII~XII 장도 알아봄(동적 워크플로 5~9장)
- **KEY MESSAGE 경고** : 한글은 명사형 종결(임, 음, 함, 됨 등) 전체를, 영문은 40자 이상 완결 문장을 인정. 맺음말 슬라이드에 잘못 붙던 경고를 없앰
- **원장 대조의 구조 숫자** : `verify_claims.py` 가 장·절 카운터와 맞는 헤딩 번호(1. → 1.1 → 1.2), 캡션·질문 번호([표 3], Q1.), 날짜(2026.04.08, 2026년 10월 12일, 2025.12 기준)를 수치로 보지 않음. 「2025.10 TWh」, 「3.5 GW 시대」 같은 수량은 그대로 검사. 위치를 문단 번호(`docx:p12`)로 알려 줌. 통과 리포트를 쓰고 비정상 종료한 게이트도 실패로 봄
- `build_pptx_checked.sh` 가 `PYTHON` 환경변수를 따름(`python3` 이 없는 Windows)
- 프로필 : BOM 이 붙은 `profile.json`(메모장, PowerShell 5) 허용. `PROFILE` 경로가 틀리면 세 스킬 모두 종료코드 2 로 같은 안내
- `build_docx.js` 가 작업 폴더의 `node_modules` 에 설치한 `docx` 도 찾음
- Word 템플릿의 문서 속성 작성자를 프로필 값(`AUTHOR_EN`)으로 채움
- 문서 : 5-Zone 규격과 예시 코드를 정본 템플릿에 맞춤(Zone 3 은 글자 밑줄, Zone 4 는 y=1850000, 표는 1790000), 차트 글꼴 레시피를 OS 와 무관하게(`koreanize-matplotlib` 의 글꼴 경로), GNU 전용 `grep -P` 제거, Phase 0 스니펫이 폴더를 못 찾으면 멈춤, 줄표를 뺀 자리의 어색한 문장 정리
- `doctor.py` 에 bash, pdftoppm 점검 추가. `selftest.py` 에 cp949 출력, 원장 대조 왕복, 게이트 오류 경로 시험 추가. 시험이 저장소에 `__pycache__` 를 남기지 않음

### 뺌 (Removed)

- `copy_to_insights.sh`, `copy_to_insights.ps1` : 특정 PC 폴더 구조에 묶인 복사 스크립트. 저장 위치는 Phase 0 이 정함

### 올릴 때 (Upgrade notes)

- **v0.9.x 를 쓰는 중이면 PPTX 빌드가 멈출 수 있음** : v0.9.x 는 외부 pptx 스킬의 스크립트 경로에 기대는데, 최근 Claude 환경에서는 그 경로에 스크립트가 없음. v1.0 으로 올리면 해결됨
- 플러그인을 업데이트하면 플러그인 폴더가 새로 바뀜. 스킬 폴더 안 `profile.json` 에 넣어 둔 값은 다시 넣어야 하므로 작업 폴더의 `./profile.json` 이나 `PROFILE` 환경변수를 권장

## [0.9.2] - 2026-08-29

- 작성자 정보(이름, 전화, 이메일, 저장 경로)를 템플릿에서 `profile.json` 으로 분리. `apply_profile.py` 가 빌드 때 바꿔 넣고, 값이 비면 빌드를 멈춤
- 함께 배포된 `quality-core` 스킬 v0.1 : 원장, So-What, 문형·표기, 16점 judge, 재시도 루프를 어떤 초안에나 적용하는 범용 검증기

## [0.9.1]

- Word 헤딩 자동 번호(`1.` / `1.1`, H1C/H2C)와 HEADNUM 게이트

## [0.9]

- 동적 워크플로 하네스(챕터 5~9 가변, 병렬 초안, deep verification, critic, loop-until-done)
- Claims Ledger(`claims.json` : verified, estimate, removed)와 `verify_claims.py`
- 4중 게이트 `gate_report.py`(toc, content, claims, judge), So-What 사다리, 시각화 카탈로그, 중국어·일본어 소스 정규화와 `verify_lang_purity.py`

## [0.5]

- 단일 컨텍스트 스킬 `generate-full-report` : 정본 템플릿으로 Word KR·EN, PowerPoint KR·EN 4종을 만들고 `build_pptx.sh` 와 `verify_toc.py` 로 빌드를 외부화
