# content.json 스키마 (build_docx.js 입력)

> 만드는 곳 : `assemble.py` 가 원고 모듈(`content_*.py`)을 모아 만듦. 손으로 써도 됨
> 읽는 곳 : `build_docx.js`(빌드), `selfcheck.py --json`(점검)
> 검사 함수 : `wb.validate_document()` (assemble, selfcheck 가 같은 함수를 씀)
> 번호 : 장, 절, 그림, 표, 질문, 참고 자료 번호는 빌드가 붙임. 원고에는 번호를 쓰지 않음(selfcheck `auto_number`)

## 1. 전체 구조

| 키 | 필수 | 형식 | 원고 모듈 변수 | Word 에서 |
|---|---|---|---|---|
| `meta` | 예 | 객체 | `META` (front) | 표지 |
| `es` | 예 | 객체 | `ES` (front) | Executive Summary 박스 |
| `qa` | 아니오 | `[{q, a}]` | `QA` (front) | 핵심 질문과 답변 박스. 비면 쪽을 만들지 않음 |
| `chapters` | 예 | `[장]` | `CHAPTERS` (장 모듈) | 「1. 제목」 장들 |
| `devils` | 아니오 | 객체 | `DEVILS` (모듈 하나에만) | 마지막 번호 장(반론 점검) |
| `closing` | 예 | 객체 | `CLOSING` (모듈 하나에만) | 맺음말 |
| `references` | 아니오 | `[{text, url}]` | `REFERENCES` (여러 모듈 가능, 순서대로 합침) | 참고 자료 |

claims 는 content.json 에 넣지 않음. 모듈의 `CLAIMS`(와 `EXTRA`)를 assemble 이 `claims.json` 으로 따로 씀(5절).

## 2. meta

| 필드 | 필수 | 형식 | 설명 |
|---|---|---|---|
| `title_lines` | 예 | 문자열 1~2개 | 표지 제목 줄. 줄마다 22pt 굵게. 둘째 줄은 26자 안팎이 넘으면 한 단어만 다음 줄로 넘어갈 수 있음 |
| `subtitle` | 아니오 | 문자열 | 제목 아래 한 줄 |
| `date` | 아니오 | 문자열 | 작성일. 「2026년 10월 12일」, 2026-10-12, 2026.10.12, 「October 12, 2026」 을 받음. assemble 이 `lang` 형식으로 바꿔 둠. 없으면 오늘 |
| `lang` | 아니오 | `"kr"` / `"en"` | 기본 kr. 글꼴(kr Malgun Gothic, en Arial), 고정 라벨, 날짜 형식이 바뀜 |
| `cover_img` | 아니오 | PNG 경로 | 표지 그림. 표지와 같은 쪽에 들어가도록 높이를 자동으로 줄임 |
| `base_date` | 아니오 | 날짜 문자열 | 조사 기준일. 본문에 적을 때 미등록 수치가 되지 않게 assemble 이 Z001 에 함께 등록함 |
| `topic` | 아니오 | 문자열 | claims.json 의 `topic`. 없으면 제목 줄 |
| `author_label` | 아니오 | 문자열 | 표지 「작성」 라벨을 바꿀 때 |

표지 날짜 줄은 `{date} | 작성: {AUTHOR_EN} ({AUTHOR_KR})` 형식이고 작성자 값은 profile.json 에서 읽음. 원고에 작성자 이름과 연락처를 쓰지 않음.

## 3. es, qa

| 필드 | 필수 | 형식 | Word 에서 |
|---|---|---|---|
| `es.key_message` | 예 | 문자열 | ■ Key Message |
| `es.background` | 예 | 문자열 | ■ 배경 (en : ■ Background) |
| `es.flow` | 예 | `[[라벨, 문장], ...]` 4개 권장 | ■ 핵심 구조 흐름 (en : ■ Core Structure). 라벨 앞에 ①②③④ 를 빌드가 붙임 |
| `es.next` 또는 `es.outlook` | 예(둘 중 하나) | 문자열 | ■ 다음 단계 또는 ■ 전망 |
| `qa[].q` | 예 | 문자열 | 「Q1. 」을 빌드가 붙임 |
| `qa[].a` | 예 | 문자열 | 「A. 」를 빌드가 붙임 |

## 4. chapters 와 블록

```json
{"title": "이용 규모와 시간대",
 "intro": ["장 도입 단락(선택)"],
 "sections": [
   {"title": "연간 대여 건수와 등록 회원",
    "key_message": "KEY MESSAGE 박스 문장 (60~120자 권장)",
    "blocks": [ {"type": "p", "text": "단락"} ]}
 ]}
```

| 블록 | 필드 | 규칙 | Word 에서 |
|---|---|---|---|
| `p` | `text` | 산문 단락. bullet, 가운뎃점 없음 | 11pt 단락 |
| `fig` | `img`, `caption`, `source`(선택) | PNG 만. 경로는 content.json 폴더 기준 상대 경로 또는 절대 경로 | 폭 630px, 높이는 PNG 헤더의 원본 비율(한 쪽 넘으면 비율대로 줄임) + 「[그림 N] 캡션」 + 출처 줄 |
| `table` | `caption`, `headers`, `rows`, `widths`(선택), `source`(선택) | 열 5개 이하, 행 14개 이하, 셀 60자 이하, `widths` 합 9026(`W()` 헬퍼) | 「[표 N] 캡션」 + 머리 진회색(#3A3A3A, 흰 글씨) 표 + 출처 줄 |
| `box` | `title`, `paras` | `paras` 는 문자열 목록 | 연한 파랑 박스 + 제목 |
| `quote` | `text`, `sub`(선택) | 원문 문장은 「」 안에 | 왼쪽 회색 선 들여쓰기 + 출처 줄 |
| `note` | `text` | 기준일, 집계 범위 같은 주석 | 9pt 회색 |

## 5. devils, closing, references

| 필드 | 필수 | 형식 | Word 에서 |
|---|---|---|---|
| `devils.title` | 예 | 문자열 | 마지막 번호 장 제목(본문 장 다음 번호) |
| `devils.intro` | 아니오 | 문자열 목록 | 장 도입 |
| `devils.items[]` | 예 | `{claim, counter}` | 「① claim」 제목 박스 + counter 단락 |
| `closing.title` | 아니오 | 문자열 | 「맺음말: {title}」 (title 에 「맺음말」이 있으면 그대로) |
| `closing.key_sentence` | 예 | 문자열 | 「핵심 문장」 박스 |
| `closing.paras` | 아니오 | 문자열 목록 | 단락 |
| `closing.perspectives` | 아니오 | `[[관점, 문장], ...]` | 「관점별로 확인할 것」 (en : Stakeholder Perspectives). `perspectives_title` 로 이름을 바꿀 수 있음 |
| `closing.keywords` | 아니오 | 문자열 목록 | 「핵심 키워드」, 앞에 # 을 붙여 한 줄 |
| `references[]` | 아니오 | `{text, url}` | 「참고 자료」, 「[1] 」 번호 + 하이퍼링크 |

맺음말 아래 H2 이름(관점별, 핵심 키워드, 참고 자료)은 verify_content.py 의 HEAD_EXEMPT 목록과 맞춘 이름임. 바꾸면 HEADNUM 오류가 날 수 있음.

## 6. claims.json (assemble 이 씀)

```json
{"topic": "예시 B시 공공자전거 현황",
 "claims": [
  {"id": "C101", "text": "2025년 연간 대여 1,284,300건", "kind": "numeric", "value": "1,284,300",
   "source": "가상의 B시 교통정보센터(예시 자료)", "url": "https://example.com/...",
   "status": "verified", "method": "web", "note": ""}
 ]}
```

- 형식은 generate-full-report 의 `references/factcheck-pipeline.md` 와 같음. `status` 는 `verified`, `estimate`, `removed` 셋만 씀
- 수치 하나를 등록하려면 claim 의 `value` 나 `text` 안에 그 수를 적음(쉼표는 무시). 한 claim 에 여러 수를 넣어도 됨 : `"value": "412 / 3,150"`
- estimate claim 의 `text` 에는 추정값 말고 다른 수를 넣지 않음(그 수들도 추정값으로 묶여 「추정」 표시를 요구받음)
- 메타 claim(assemble 이 자동으로 넣음, id 가 Z 로 시작) : Z001 작성일과 조사 기준일 / Z002 헤딩 번호 / Z003 그림, 표, 질문 번호 / Z004 참고 자료 번호와 서지 정보 안의 수. 원고 담당은 Z 로 시작하는 id 를 쓰지 않음

## 7. 최소 예

```json
{
 "meta": {"title_lines": ["예시 보고서: 가상의 A사 현황"], "date": "2026년 10월 12일", "lang": "kr"},
 "es": {"key_message": "가상의 A사 매출은 35억 원임을 정리합니다.", "background": "예시입니다.",
        "flow": [["규모", "매출 35억 원"], ["사람", "직원 42명"], ["고객", "고객사 18곳"], ["한계", "원가 자료 미기재"]],
        "next": "분석 단계에서 원가를 확인합니다."},
 "qa": [{"q": "매출은 얼마입니까?", "a": "35억 원입니다."}],
 "chapters": [{"title": "규모", "intro": [], "sections": [
   {"title": "매출과 직원", "key_message": "매출 35억 원, 직원 42명입니다.",
    "blocks": [{"type": "p", "text": "가상의 A사 매출은 35억 원이고 직원은 42명입니다."}]}]}],
 "closing": {"key_sentence": "가상의 A사는 직원 42명이 매출 35억 원을 냅니다.", "paras": [], "keywords": ["예시"]},
 "references": [{"text": "가상의 A사 사업보고서(예시), 2026년 3월 31일", "url": "https://example.com/a"}]
}
```

이 예의 수치(35, 42, 18)는 claims.json 에 등록해야 게이트를 통과함.
