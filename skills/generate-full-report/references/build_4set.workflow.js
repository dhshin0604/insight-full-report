/* =============================================================================
 * build_4set.workflow.js — 신동형 인사이트 4종 세트 동적 워크플로 (TEMPLATE) v0.9
 *
 * 이 파일은 "그대로 실행하는 스크립트"가 아니라 **템플릿**이다(Anthropic 권고).
 * Claude 는 작업/소스에 맞게 단계 수·프롬프트·모델을 조정해 워크플로를 작성한다.
 * 동적 워크플로 런타임의 실제 에이전트-스폰 함수명에 맞춰 spawn()/synthesize()
 * 자리표시 함수를 매핑할 것. 입력은 전역 `args` 로 받는다.
 *
 * 입력 args 예:
 *   { sources:[...], titleKR, subtitleKR, slug, langs:["kr","en"],
 *     docTypes:["docx","pptx"], maxRetries:3, tokenBudget:"high" }
 *
 * 적용한 동적 워크플로 패턴:
 *   - classify-and-act        : 소스를 읽고 구조(가변 챕터)·언어·모델·시각화 계획 결정
 *   - fan-out-and-synthesize  : 챕터 1개당 에이전트 1개로 병렬 초안 → 합성
 *   - deep verification       : claim 추출 → claim 묶음별 검증 에이전트 fan-out (v0.9)
 *   - adversarial verification: 초안마다 '다른' critic 에이전트가 루브릭 채점
 *   - loop-until-done         : 게이트 통과까지 패치-재빌드 반복(상한 maxRetries)
 *
 * 이 구조가 막는 실패 모드(블로그):
 *   agentic laziness(중도 포기) · self-preferential bias(자기편애) · goal drift(목표표류)
 *   + hallucination(미검증 수치) — v0.9 FACTCHECK 단계가 구조적으로 차단
 * ============================================================================= */

const REF = "references"; // 스킬 references 경로 (런타임에 맞게 조정)

// ── helper 자리표시(런타임 실제 API로 매핑) ───────────────────────────────────
// spawn({ prompt, model, tools, worktree }) -> Promise<{text, json}>
// synthesize(results) 는 fan-out 결과를 모으는 배리어(Promise.all 로 충분)

async function main() {
  const cfg = Object.assign(
    { langs: ["kr", "en"], docTypes: ["docx", "pptx"], maxRetries: 3, tokenBudget: "high" },
    (typeof args !== "undefined" && args) || {}
  );

  /* ── Phase A. CLASSIFY (classify-and-act) ──────────────────────────────────
   * 소스를 읽고 '동적 구조'를 결정한다. 고정 7챕터/13장 제약을 여기서 푼다.
   * v0.9: 챕터별 시각화 계획(visual)도 여기서 세운다 (visual-catalog.md 매핑). */
  const plan = (await spawn({
    model: "sonnet", // 분류는 가벼운 모델
    prompt: `다음 소스를 분석해 보고서 설계를 JSON 으로 반환하라.
소스: ${JSON.stringify(cfg.sources)}
반환 스키마:
{
  "sourceLang": "KR|EN|ZH|JA|MIXED",
  "needNormalize": true|false,
  "chapters": [ {"roman":"I","title":"...","subtopics":["..",".."],
                 "visual":{"type":"flowchart|table|hbars|timeline|matrix|none",
                           "what":"무엇을 그릴지 한 줄"}}, ... ],
  "execSummaryParts": ["Key Message","배경","핵심 구조 흐름","전망"],
  "modelHint": "opus|sonnet"
}
- chapters 는 소스 깊이에 따라 5~9개 가변. VII(Devil's Advocate)는 비판 소재가 있을 때만.
- visual 은 ${REF}/visual-catalog.md 의 '내용 유형→시각요소' 매핑으로 권장 지정(강제 아님).
규칙: ${REF}/pptx-style-guide.md, ${REF}/docx-build-pipeline.md 의 신동형 정본 준수.`
  })).json;

  /* ── Phase B. NORMALIZE (조건 분기) ────────────────────────────────────────
   * 비 한/영 소스만 정규화 노트 + Glossary 생성 (SKILL.md Phase 1.5).            */
  let glossary = null;
  if (plan.needNormalize) {
    glossary = (await spawn({
      model: "opus",
      prompt: `소스를 한/영으로 정규화하라. notes_kr.md / notes_en.md 와 Glossary 표 생성.
첫 등장만 '한글(原文)' / 'English (Pinyin, 中文)', 재등장은 번역어만. 결과 JSON 으로 요약 반환.`
    })).json;
  }

  /* ── Phase C. DRAFT CHAPTERS (fan-out-and-synthesize) ─────────────────────
   * 챕터마다 독립 컨텍스트 에이전트가 병렬 초안 작성 → goal drift 방지.
   * v0.9: 초안과 함께 claim 을 등록하게 한다 (factcheck-pipeline.md 스키마).      */
  async function draftChapter(ch) {
    return (await spawn({
      model: plan.modelHint || "opus",
      prompt: `챕터 ${ch.roman}. ${ch.title} 를 신동형 산문체로 작성하라.
- 소주제 ${ch.subtopics.length}개, 각 H2 에 KEY MESSAGE(40~100자, ~임./~음.)
- KEY MESSAGE 는 ${REF}/insight-frameworks.md So-What 사다리 L2 이상에서 도출,
  챕터당 1개 이상 L3(2차 효과·수혜/피해 주체)까지. 핵심 주장에 최강 반론 1개 처리.
- 내러티브 3~4 단락(비유·수치·맥락), 비교는 표로, 시각화 권장: ${JSON.stringify(ch.visual || null)}
- 모든 수치·사건·인용은 claims[] 로 등록 (id,text,kind,value,source,url,status,method).
  소스에 없는 수치는 만들지 말 것. 추정이면 status=estimate + 본문 '추정' 표기.
- 금지: bullet(Word 본문), 과장 형용사(혁명적/압도적 등), 한글본 한자 혼입
${glossary ? "- Glossary 재등장열만 사용" : ""}
반환: {roman, title, keyMessages:[...], narrative:"...", tables:[...], claims:[...]}`
    })).json;
  }
  const chapters = await Promise.all(plan.chapters.map(draftChapter)); // fan-out

  /* ── Phase C2. FACTCHECK (deep verification fan-out) — v0.9 신규 ──────────
   * claim 묶음(8개)마다 '작성자가 아닌' 검증 에이전트를 fan-out.
   * skeptic 에이전트가 verified 표본을 재감사해 false-verified 차단.             */
  const allClaims = chapters.flatMap(ch => (ch.claims || []).map(c => ({ ...c, roman: ch.roman })));
  const batches = [];
  for (let i = 0; i < allClaims.length; i += 8) batches.push(allClaims.slice(i, i + 8));

  async function verifyBatch(batch) {
    return (await spawn({
      model: "sonnet",
      tools: ["WebSearch", "WebFetch", "Read"],
      prompt: `너는 사실 검증자다. 다음 claim 들을 소스 원문/웹으로 대조해 판정하라.
${REF}/factcheck-pipeline.md 규칙:
- 직접 확인 → status=verified (+source/url 보강)
- 확인 불가하나 합리적 계산/외삽 → status=estimate (+method, note)
- 확인 실패·소스와 모순 → status=removed
반환: claims 배열(JSON) — 각 항목에 status/source/url/note 갱신.
claims: ${JSON.stringify(batch)}`
    })).json;
  }
  const verifiedBatches = await Promise.all(batches.map(verifyBatch)); // fan-out
  const ledger = verifiedBatches.flat();

  // skeptic: verified 표본 재검증 (전수 아닌 표본 — 비용 절충)
  const sample = ledger.filter(c => c.status === "verified").filter((_, i) => i % 4 === 0);
  if (sample.length) {
    const audit = (await spawn({
      model: "opus",
      tools: ["WebSearch", "WebFetch"],
      prompt: `너는 회의적 감사자다. 다음 'verified' claim 표본을 재검증해
잘못 verified 된 항목의 {id, status, note} 배열(JSON)을 반환하라: ${JSON.stringify(sample)}`
    })).json;
    for (const fix of audit || []) {
      const c = ledger.find(x => x.id === fix.id);
      if (c) Object.assign(c, fix);
    }
  }

  // removed claim 반영 — 해당 챕터를 작성자 모델이 수정
  const removedByCh = {};
  for (const c of ledger.filter(c => c.status === "removed")) {
    (removedByCh[c.roman] = removedByCh[c.roman] || []).push(c);
  }
  for (const roman of Object.keys(removedByCh)) {
    const i = chapters.findIndex(ch => ch.roman === roman);
    chapters[i] = (await spawn({
      model: plan.modelHint || "opus",
      prompt: `다음 removed claim 들을 본문에서 삭제/완화하고 챕터를 다시 반환하라(JSON).
removed: ${JSON.stringify(removedByCh[roman])}
챕터: ${JSON.stringify(chapters[i])}`
    })).json;
  }
  // ledger 는 빌드 단계에서 claims.json 으로 저장 → gate 가 사용

  // 합성: Executive Summary(4파트) 작성 — 배리어 이후 1회
  const execSummary = (await spawn({
    model: "opus",
    prompt: `다음 챕터들을 관통하는 Executive Summary 를 4파트(${plan.execSummaryParts.join(" / ")})로,
1300자 내외 소제목 없는 연결 문장으로 작성. Key Message 는 So-What L3~L4 명제로:
${JSON.stringify(chapters).slice(0, 6000)}`
  })).text;

  /* ── Phase D. ADVERSARIAL VERIFICATION ────────────────────────────────────
   * 초안 작성자와 '다른' critic 에이전트가 루브릭으로 채점 → self-bias 방지.
   * 통과 못한 챕터만 재작성(loop-until-done, 상한 2회).                          */
  async function critique(ch) {
    for (let pass = 0; pass < 2; pass++) {
      const v = (await spawn({
        model: "opus",
        prompt: `너는 비판적 검수자다. ${REF}/quality_rubric.md 기준(8개·각 0~2점)으로
다음 챕터를 채점하라. 합격선: 총점>=12 그리고 0점 기준 없음.
#8(인사이트 깊이)은 ${REF}/insight-frameworks.md 의 So-What 사다리로 판정.
반환 {pass:bool, score:int, fixes:[{loc,detail,fix}]}.
챕터: ${JSON.stringify(ch)}`
      })).json;
      if (v.pass) return ch;
      ch = (await spawn({ // 작성자(critic 아님)가 fixes 적용해 재작성
        model: plan.modelHint || "opus",
        prompt: `다음 지적을 반영해 챕터를 고쳐 다시 작성: ${JSON.stringify(v.fixes)}
원본: ${JSON.stringify(ch)}`
      })).json;
    }
    return ch; // 상한 도달 시 마지막본 채택(이후 게이트가 한 번 더 잡음)
  }
  const verified = await Promise.all(chapters.map(critique));

  const content = { titleKR: cfg.titleKR, subtitleKR: cfg.subtitleKR,
                    chapters: verified, execSummary, slug: cfg.slug,
                    claims: ledger };

  /* ── Phase E. BUILD DOCUMENTS (fan-out) ───────────────────────────────────
   * 문서 4종을 병렬 빌드. 각 빌드 에이전트가 정본 템플릿을 적응해 실행한다.
   * (스크립트 자체는 셸/FS 접근 불가 — 에이전트가 cp/치환/실행을 수행)            */
  const targets = [];
  for (const lang of cfg.langs) {
    for (const dt of cfg.docTypes) targets.push({ lang, dt });
  }

  async function buildOne(t) {
    const verb = t.dt === "pptx"
      ? `bash ${REF}/build_pptx_checked.sh ${t.lang} build_pptx_${t.lang}.py ${cfg.slug}_${t.lang.toUpperCase()}_Presentation.pptx`
      : `node build_${t.lang}.js 실행 후 python3 ${REF}/gate_report.py --docx --claims claims.json 으로 검사`;
    return (await spawn({
      model: "sonnet", // 빌드는 절차 실행 — 가벼운 모델
      tools: ["Bash", "Read", "Write", "Edit"],
      prompt: `1) content.claims 를 claims.json 으로 저장.
2) 정본 템플릿을 cp 후 아래 content 로 치환해 ${t.dt.toUpperCase()}(${t.lang}) 를 빌드하라.
   챕터 visual 계획이 있으면 ${REF}/visual-catalog.md 레시피로 시각요소 생성.
빌드 명령: ${verb}
content: ${JSON.stringify(content).slice(0, 8000)}
반환 {lang, dt, unpacked, output, gateJson}`
    })).json;
  }
  let built = await Promise.all(targets.map(buildOne)); // fan-out

  /* ── Phase F. GATE + RETRY (loop-until-done) ──────────────────────────────
   * 각 산출물에 통합 게이트(toc+content+claims+judge). 실패분만 패치-재빌드.      */
  for (let attempt = 1; attempt <= cfg.maxRetries; attempt++) {
    const failed = [];
    for (const b of built) {
      const gate = (await spawn({
        model: "sonnet", tools: ["Bash", "Read"],
        prompt: `python3 ${REF}/gate_report.py 로 ${b.output} (${b.dt}/${b.lang}) 검증.
PPTX 는 --unpacked ${b.unpacked}, DOCX 는 --docx ${b.output}.
--claims claims.json --skill-dir ${REF} 포함. gate JSON 내용을 그대로 반환.`
      })).json;
      if (!gate.pass) failed.push({ b, fixes: gate.fixes });
    }
    if (failed.length === 0) break;            // ✅ 전부 통과 → 종료
    if (attempt === cfg.maxRetries) {
      return { status: "NEEDS_REVIEW", built, failed }; // 무한 루프 금지 → 사람에게
    }
    // 실패분만 패치 후 재빌드
    for (const f of failed) {
      await spawn({
        model: plan.modelHint || "opus", tools: ["Read", "Edit"],
        prompt: `gate fixes 를 build 소스(build_${f.b.lang}.js / build_pptx_${f.b.lang}.py)와
claims.json 에 반영: ${JSON.stringify(f.fixes)}`
      });
    }
    const rebuilt = await Promise.all(failed.map(f => buildOne(f.b)));
    built = built.map(b => rebuilt.find(x => x.lang === b.lang && x.dt === b.dt) || b);
  }

  /* ── Phase G. FINALIZE (Observability) ────────────────────────────────────
   * manifest.json 으로 무엇을·왜 통과했는지 기록 + $WORKSPACE 저장 지시.        */
  return {
    status: "DONE",
    docs: built.map(b => b.output),
    chapters: verified.length,
    claims: { total: ledger.length,
              verified: ledger.filter(c => c.status === "verified").length,
              estimate: ledger.filter(c => c.status === "estimate").length,
              removed: ledger.filter(c => c.status === "removed").length },
    manifest: { plan, gatePassed: true, builtAt: new Date().toISOString() }
  };
}

return main(); // 워크플로 런타임이 main() 결과를 최종 답으로 받는다
