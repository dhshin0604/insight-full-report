# insight-full-report Plugin v0.5 (Determinism Edition)

소스(URL, YouTube, PDF, 문서, 텍스트)를 입력받아 **Word 한글 + Word 영어 + PowerPoint 한글 + PowerPoint 영어** 총 4종 문서를 자동 생성하는 "신동형 인사이트" 스타일 보고서 생성기입니다.

## v0.5 핵심 변경 (Determinism Edition)

- **build_pptx.sh 오케스트레이터**: 모든 OOXML 조작(unpack, sldIdLst 수정, slide3 layout 패치, Google strip, pack)을 외부 bash로 분리. 모델은 콘텐츠만 작성하므로 Opus 4.6 / Sonnet 4.6 어디서 돌려도 동일 결과.
- **verify_toc.py**: TOC(slide2)의 로마숫자 챕터와 본문 z1 헤더를 1:1 매칭 검증. 누락/순서불일치/중복 시 빌드 중단.
- **맺음말 슬라이드 자동 마지막 배치**: sldIdLst에서 closing slide를 마지막으로 강제 이동.
- **slide3 layout 자동 보정**: chapter divider(layout3) → contents(layout5) 패치.
- **폰트 조달**: GitHub raw 차단 환경에서도 `pip install koreanize-matplotlib`로 NanumGothic 확보.
- **GATE 0/1 + ANTI-DRIFT 14개 금지패턴**: SKILL.md에 자기검증 체크리스트 내장.
- **TARGET_UNPACKED 환경변수**: 절대경로 의존성 제거, 어느 세션에서도 동작.

## 스킬

### generate-full-report

소스를 받아 4종 문서를 순서대로 생성합니다.

**트리거 문구:**
- 보고서 만들어 / 워드랑 파워포인트 만들어 / 4종 문서
- generate full report / make study materials / 신동형 스타일

**생성 문서:**
1. `{주제}_KR_Report_{날짜}.docx` — 한국어 Word (analyst 산문체, Malgun Gothic)
2. `{주제}_EN_Report_{날짜}.docx` — 영어 Word (analyst prose, Arial)
3. `{주제}_KR_Presentation_{날짜}.pptx` — 한국어 PowerPoint (5-Zone 레이아웃, 13슬라이드 7챕터)
4. `{주제}_EN_Presentation_{날짜}.pptx` — 영어 PowerPoint
