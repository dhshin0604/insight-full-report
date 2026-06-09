'use strict';
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel,
  ImageRun, Table, TableRow, TableCell, WidthType,
  BorderStyle, AlignmentType, VerticalAlign,
  ShadingType, UnderlineType, PageBreak, ExternalHyperlink,
  Footer, PageNumber,
} = require('docx');
const fs = require('fs');
const path = require('path');

const EN = { ascii: 'Arial', eastAsia: 'Arial', hAnsi: 'Arial' };
const F  = EN;

const B  = (t, sz, c) => new TextRun({ text: t, bold: true,  size: sz||22, font: F, color: c||'000000' });
const N  = (t, sz, c) => new TextRun({ text: t, bold: false, size: sz||22, font: F, color: c||'000000' });
const P  = (...runs) => new Paragraph({ children: runs, spacing: { before: 0, after: 200 } });
const BK = () => new Paragraph({ children: [], spacing: { before: 0, after: 80 } });
const PB = () => new Paragraph({ children: [new PageBreak()] });

const H1 = (t) => new Paragraph({
  children: [new TextRun({ text: t, bold: true, size: 28, font: F, color: '1A3A6B' })],
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 360, after: 160 },
});
const H2 = (t) => new Paragraph({
  children: [new TextRun({ text: t, bold: true, size: 24, font: F, color: '333333' })],
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 280, after: 120 },
});

// ─── 챕터 자동 번호 헬퍼 (v0.9.1) ─────────────────────────────────────────────
// 본문 챕터는 반드시 H1C/H2C 를 사용한다. H1C → "1. 제목", H2C → "1.1 소제목".
// 번호가 코드에서 자동 증가하므로 내용 치환 시 번호 누락 드리프트가 불가능하다.
// Executive Summary·핵심 질문과 답변·맺음말·참고 자료 등 특수 섹션만 번호 없는 H1/H2 사용.
let _ch = 0, _sec = 0;
const H1C = (t) => { _ch += 1; _sec = 0; return H1(`${_ch}. ${t}`); };
const H2C = (t) => { _sec += 1; return H2(`${_ch}.${_sec} ${t}`); };

function textBox(title, children) {
  const titleRow = title ? [new Paragraph({
    children: [new TextRun({ text: title, bold: true, size: 24, font: F, color: '1A3A6B' })],
    spacing: { before: 0, after: 120 },
  })] : [];
  return new Table({
    width: { size: 9026, type: WidthType.DXA },
    columnWidths: [9026],
    borders: {
      top:    { style: BorderStyle.SINGLE, size: 8, color: '1A3A6B' },
      bottom: { style: BorderStyle.SINGLE, size: 3, color: 'CCCCCC' },
      left:   { style: BorderStyle.NONE },
      right:  { style: BorderStyle.NONE },
      insideH:{ style: BorderStyle.NONE },
      insideV:{ style: BorderStyle.NONE },
    },
    rows: [new TableRow({ children: [new TableCell({
      width: { size: 9026, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: 'F0F4FA' },
      margins: { top: 250, right: 500, bottom: 250, left: 500 },
      verticalAlign: VerticalAlign.TOP,
      children: [...titleRow, ...children],
    })] })],
  });
}

const SL = (label) => new Paragraph({
  children: [new TextRun({ text: label, bold: true, size: 22, font: F, color: '1A3A6B' })],
  spacing: { before: 120, after: 60 },
});

function makeTable(headers, rows) {
  const colWidths = headers.map(() => Math.floor(9026 / headers.length));
  const headerCells = headers.map((h, i) => new TableCell({
    width: { size: colWidths[i], type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: '1A3A6B' },
    margins: { top: 100, right: 200, bottom: 100, left: 200 },
    children: [new Paragraph({
      children: [new TextRun({ text: h, bold: true, size: 19, font: F, color: 'FFFFFF' })],
    })],
  }));
  const dataRows = rows.map(cells => new TableRow({
    children: cells.map((c, i) => new TableCell({
      width: { size: colWidths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: 'FFFFFF' },
      margins: { top: 80, right: 200, bottom: 80, left: 200 },
      children: [new Paragraph({
        children: [new TextRun({ text: c, size: 19, font: F, color: '333333' })],
      })],
    })),
  }));
  return new Table({
    width: { size: 9026, type: WidthType.DXA },
    columnWidths: colWidths,
    borders: {
      top:    { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
      left:   { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
      right:  { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
      insideH:{ style: BorderStyle.SINGLE, size: 2, color: 'DDDDDD' },
      insideV:{ style: BorderStyle.SINGLE, size: 2, color: 'DDDDDD' },
    },
    rows: [new TableRow({ children: headerCells }), ...dataRows],
  });
}

const imgData = fs.readFileSync(path.join(__dirname, 'workflow_chart_en_cropped.png'));

const doc = new Document({
  styles: {
    default: {
      heading1: {
        run: { font: F, size: 28, bold: true, color: '1A3A6B' },
        paragraph: { spacing: { before: 360, after: 160 } },
      },
      heading2: {
        run: { font: F, size: 24, bold: true, color: '333333' },
        paragraph: { spacing: { before: 280, after: 120 } },
      },
    },
  },
  sections: [{
    properties: {
      titlePage: true,
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1701, right: 1440, bottom: 1440, left: 1440 },
        pageNumbers: { start: 0 },
      },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ children: [PageNumber.CURRENT], size: 18, font: F, color: '888888' }),
            new TextRun({ text: ' / ', size: 18, font: F, color: '888888' }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, font: F, color: '888888' }),
          ],
          spacing: { before: 120, after: 120 },
        })],
      }),
      first: new Footer({ children: [new Paragraph({ children: [] })] }),
    },
    children: [

      // ═══════════════════════════════════════════════════════
      // PAGE 0: Cover + Flow Chart
      // ═══════════════════════════════════════════════════════
      new Paragraph({
        children: [new TextRun({
          text: 'Embodied AI Development Report 2025:',
          bold: true, size: 44, font: F, color: '1A3A6B',
        })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 600, after: 0 },
      }),
      new Paragraph({
        children: [new TextRun({
          text: 'A Comprehensive Analysis of Technology, Products & Ecosystem',
          bold: true, size: 44, font: F, color: '1A3A6B',
        })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 200 },
      }),
      new Paragraph({
        children: [new TextRun({
          text: 'April 8, 2026  |  By: DH Shin (Dong Hyung Shin)',
          size: 18, font: F, color: '555555',
        })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 280 },
      }),
      new Paragraph({
        children: [new ImageRun({
          data: imgData,
          transformation: { width: 450, height: 407 },
          type: 'png',
        })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 160 },
      }),
      PB(),

      // ═══════════════════════════════════════════════════════
      // PAGE 1: Executive Summary
      // ═══════════════════════════════════════════════════════
      H1('Executive Summary'),
      textBox(null, [
        SL('■ Key Message'),
        P(N('Embodied AI represents far more than a simple combination of AI and robotics — it is the defining technological breakthrough of our era. Just as humans cannot interact with the world through intellect alone, AI must unite with a physical body to generate real-world value. Embodied AI achieves a complete closed-loop of perception, decision-making, and action through its physical form — a new technological paradigm. In 2025 alone, papers featuring the single keyword "end-to-end VLA" quadrupled year-over-year to over 1,700, and the world\'s largest technology companies have declared Embodied AI their "next frontier."')),

        SL('■ Background'),
        P(N('The International Telecommunication Union formally defined Embodied AI in ITU-T F.748.66 as "AI that autonomously interacts with the physical world and adapts to its environment by integrating with a physical entity," signaling that this technology has moved beyond laboratory concept. NVIDIA CEO Jensen Huang declared at CES 2025 that "the next frontier of AI is physical AI," and global market research firms project the combined market for humanoid robots, autonomous vehicles, and drones to reach $339.8 billion by 2030. Figure AI\'s $1 billion funding round in September 2025 at a $39 billion valuation, alongside Apptronik\'s $350 million Series A close in February 2025, confirm that capital markets have already placed their bets on this sector.')),

        SL('■ Core Structure'),
        P(B('① Technology Pathways: ', 22), N('Four parallel approaches are co-evolving and complementing one another: modular layering (Path 1), layered foundation models (Path 2), end-to-end VLA (Path 3), and world models (Path 4). Figure AI\'s Helix system demonstrated the fusion of Paths 3 and 4 in production by combining a 7-9 Hz cognitive-reasoning loop with a 200 Hz body motion control loop within a single framework.')),
        P(B('② Dual Data Strategy: ', 22), N('Given that Embodied AI requires tens of thousands to millions of hours of training data, a "dual strategy" combining simulation-synthesized data with real-robot collection has become the industry standard. Overcoming the Sim-to-Real Gap — the performance degradation when policies learned in simulation are transferred to the real world — is the central technical challenge.')),
        P(B('③ Products & Ecosystem: ', 22), N('In the humanoid robot space, three competing camps have emerged: full-stack integrators (Figure AI, ZHIYUAN), hardware-focused players (Unitree, Agility, Apptronik), and software-brain specialists (Physical Intelligence, Field AI). China\'s market alone recorded 744 investment transactions totaling 73.543 billion yuan through end-2025.')),
        P(B('④ Unresolved Challenge: ', 22), N('The "challenge cycle" of data-model-hardware-deployment remains unsolved. Current state-of-the-art VLA models achieve only 20-40% success rates on long-horizon tasks.')),

        SL('■ Outlook'),
        P(N('Near-term: High-speed simulators like Genesis and Isaac Sim will dramatically lower training costs, accelerating industrial deployment. Mid-term: The shift from "custom development" to "standardized delivery" will complete the commercialization loop as use cases expand into home and healthcare. Long-term: Architecture will transition from "stacked functional modules" to "multimodal cognitive fusion," and Physical AI will unlock the $339.8 billion market.')),
      ]),
      BK(), PB(),

      // ═══════════════════════════════════════════════════════
      // PAGE 2: Key Questions & Answers
      // ═══════════════════════════════════════════════════════
      H1('Key Questions & Answers'),
      textBox(null, [
        P(B('Q1. What is Embodied AI and how does it differ from conventional software AI?', 22, '1A3A6B')),
        P(N('A. Embodied AI can be summarized in one phrase: "AI with a body." While conventional AI systems like GPT operate by exchanging text within a screen, Embodied AI perceives objects through cameras, grasps them with robotic arms, and places them at target locations — executing physical actions in the real world. The ITU formally defined it as "AI that autonomously interacts with the physical world and adapts to its environment by integrating with a physical entity" (ITU-T F.748.66). Its three core components are: ① a physical body (humanoid robots, autonomous vehicles, drones), ② an intelligence core (LLM, VLM, VLA, World Model), and ③ an environment interaction loop (sensor-actuator feedback). If conventional AI is like a librarian who finds you a book, Embodied AI is the one who physically retrieves it and brings it to you.')),
        BK(),
        P(B('Q2. What are the four technology pathways and which is attracting the most attention?', 22, '1A3A6B')),
        P(N('A. Path 1 (Modular Layering) stacks deep learning and machine learning in layers — a battle-tested approach deployed in AMR warehouse robots. Path 2 (Layered Foundation Models) uses LLMs/VLMs for high-level task planning, calling lower-level action policies via API; Google Gemini Robotics-ER 1.5 has adopted this approach. Path 3 (End-to-End VLA) unifies vision, language, and action within a single transformer network — exemplified by Figure AI Helix and Physical Intelligence pi0.5 in production. Path 4 (World Model) internalizes the physics of the environment, enabling the agent to simulate the consequences of actions before executing them, as demonstrated by Ctrl-World and DreamVLA. The dramatic surge in VLA papers (1,700+ in 2025, up 4x YoY) makes the convergence of Paths 3 and 4 the most closely watched frontier.')),
        BK(),
        P(B('Q3. How do the three humanoid robot business strategies differ in strengths and risks?', 22, '1A3A6B')),
        P(N('A. Full-Stack Integrators seek vertical integration from software to hardware. Figure AI raised $1 billion in September 2025 at a $39 billion valuation to develop its Helix end-to-end model in-house. High capex is required, but SW-HW co-optimization enables class-leading performance. Hardware-Focused Players concentrate on hardware cost innovation. Unitree Robotics\' launch of the R1 humanoid at 39,900 yuan is the emblematic event for this approach, while Agility\'s Digit robots operating in Amazon fulfillment centers validate commercial viability. Software-Brain Specialists develop hardware-agnostic general algorithms. Physical Intelligence\'s decision to open-source pi0.5 is a deliberate strategy to build an ecosystem where hardware partners develop on its platform.')),
        BK(),
        P(B('Q4. What is the "challenge cycle" and why does it constrain commercialization?', 22, '1A3A6B')),
        P(N('A. The challenge cycle is a structural loop in which the four elements of data, model, hardware, and deployment mutually block each other\'s development. Without high-quality data, model performance degrades; without capable models, hardware is difficult to control; without stable hardware, real-world deployment is impossible; and without real-world deployment, data collection cannot scale. The result: Google Gemini Robotics-ER 1.5 achieves only 20-40% success on long-horizon tasks such as "sorting trash" or "swapping items." A more fundamental bottleneck is the temporal-scale mismatch between high-level task planning (1-10 Hz) and low-level body control (100+ Hz). Industry\'s response combines large-scale simulation, physical training grounds, and domain randomization techniques to break out of this loop.')),
        BK(),
        P(B('Q5. What is the scale and character of China\'s Embodied AI investment ecosystem?', 22, '1A3A6B')),
        P(N('A. China\'s investment in Embodied AI has grown to the world\'s largest scale. By end-2025, there were 744 investment transactions totaling 73.543 billion yuan, with over 352 companies participating across four industry blocks: sector applications, product & services, technical services, and infrastructure. Firms are concentrated in the four major hubs of Beijing, Shanghai, Shenzhen, and Hangzhou. A construction boom in "training grounds" — dedicated facilities where robots repeatedly learn in simulated real-world environments — is a defining characteristic of this ecosystem. However, the extent to which training ground performance translates to complex real-world environments remains insufficiently verified.')),
        BK(),
        P(B('Q6. What are the three development directions and what should investors and enterprises focus on?', 22, '1A3A6B')),
        P(N('A. Architecture: AI will shift from "stacked functional modules" to "multimodal cognitive fusion," where vision, audio, and tactile information are processed within a unified network. Applications: Use cases will expand sequentially — manufacturing and logistics (near-term), home services and healthcare (mid-term), and extreme or hazardous environments (long-term). Safety and Ethics: Functional safety, cybersecurity, liability attribution, and privacy protection must be resolved as prerequisites for scaled commercialization. Investors and enterprises should balance clear-eyed recognition of the current maturity gap (VLA success rates of 20-40%) with the long-term view that this technology will be the core driver of a $339.8 billion market by 2030.')),
      ]),
      BK(), PB(),

      // ═══════════════════════════════════════════════════════
      // PAGE 3: Chapter I
      // ═══════════════════════════════════════════════════════
      H1C('Global Overview — The Embodied AI Macro Landscape'),
      H2C('Defining the Concept: The Rise of "AI with a Body"'),
      textBox('KEY MESSAGE', [
        P(N('Embodied AI is not a simple merger of AI and robotics. It is a new technology paradigm that implements a complete closed-loop of perception, decision-making, and action through a physical body. Just as humans need both brain and body to interact with the world, AI must unite with a physical entity to create value in reality.')),
      ]),
      BK(),
      P(N('To understand why Embodied AI commands such attention, we must first answer the question: "Why now?" Earlier AI possessed only a "brain" — it analyzed data and generated text, but could not act. Like a mind with no body, it could think but not do. The emergence of large language models (LLMs) and vision-language models (VLMs) now enables AI to couple with robotic bodies and act directly in the physical world. This is the essence of Embodied AI.')),
      P(N('The ITU formalized this concept in ITU-T F.748.66, defining Embodied AI as "AI that autonomously interacts with the physical world and adapts to its environment by integrating with a physical entity." This definition encodes three core capabilities. Cognitive capability — the ability to perceive and understand the surrounding environment through cameras, LiDAR, and other sensors. Collaborative capability — the ability to transition from solo operation to joint work with other robots or humans. Learning capability — the ability to adapt and learn from new situations in the field, building on pre-trained knowledge.')),
      P(N('The physical architecture of Embodied AI spans three layers. ① The physical body — humanoid robots, quadrupeds, autonomous vehicles, drones: the physical vessel that carries the AI. ② The intelligence core — LLM, VLM, VLA (Vision-Language-Action), and World Models: the software brain responsible for reasoning and planning. ③ Environment interaction — the closed-loop feedback system that takes in data through sensors and outputs actions through actuators. The three platforms commonly called the "smart trinity" of future production and daily life — humanoid robots, autonomous vehicles, and drones — all share this three-layer architecture.')),
      BK(),
      H2C('Surging Global Interest: Capital and Technology Converge'),
      textBox('KEY MESSAGE', [
        P(N('When NVIDIA, McKinsey, and other global leaders declared Embodied AI "the next frontier," this was not mere technological optimism. The projected market of $339.8 billion across humanoid robots, autonomous vehicles, and drones by 2030, combined with already-deployed enterprise capital, signals a structural shift in the technology investment landscape.')),
      ]),
      BK(),
      P(N('After NVIDIA CEO Jensen Huang declared at his CES 2025 keynote that "the next frontier of AI is physical AI," the global technology industry\'s gaze shifted decisively toward this domain. This is not marketing language. NVIDIA itself is deploying massive capital into robotics learning infrastructure through its Omniverse platform and Isaac Sim. McKinsey projects that Physical AI could enhance productivity in manufacturing, logistics, and services by tens of percent by 2030, and specific market forecasts bear this out: Grand View Research estimates humanoid robots at $4.04 billion, autonomous vehicles (L1-L3) at $172.2 billion, and drones at $163.6 billion by 2030, for a combined $339.8 billion.')),
      P(N('Venture activity reflects these expectations. Figure AI\'s $1 billion raise from Microsoft, OpenAI, and Bezos Expeditions in September 2025 at a $39 billion valuation stands as a landmark. Apptronik\'s $350 million Series A close in February 2025 further validates investor conviction. Three distinct strategic camps have crystallized: Full-Stack Integrators (Figure AI, ZHIYUAN Robotics) who seek vertical integration from software to hardware for maximum performance; Hardware-Focused Players (Unitree, Agility, Apptronik) who concentrate on high-performance body manufacturing and resolve software through partnerships; and Software-Brain Specialists (Physical Intelligence, Field AI, Galaxy General) who develop hardware-agnostic algorithms and supply software to multiple hardware manufacturers.')),
      BK(),
      H2C('Still in Early Stage: Bridging Expectation and Reality'),
      textBox('KEY MESSAGE', [
        P(N('Despite white-hot technology enthusiasm and investment, the "challenge cycle" of data-model-hardware-deployment remains unresolved. The fact that current state-of-the-art VLA models achieve only 20-40% success on long-horizon tasks is a sobering reminder of the distance between current capabilities and scaled commercial deployment.')),
      ]),
      BK(),
      P(N('The challenge cycle is the structural impediment to Embodied AI commercialization. Without high-quality data, model performance is limited; with limited models, hardware control is unreliable; with unreliable hardware, real-world deployment is infeasible; and without real-world deployment, large-scale data collection is impossible. This circular dependency constrains overall industry progress and is the root cause of three major unresolved debates: ① the algorithm pathway debate (which architecture is optimal?), ② the hardware form-factor debate (humanoids versus task-specific robots), and ③ the data strategy debate (simulation versus real-robot collection).')),
      P(N('Performance statistics are unsparing about current realities. Google Gemini Robotics-ER 1.5 achieves only 20-40% success on long-horizon tasks such as "trash sorting" or "item exchange," and all current VLA systems show significant performance degradation with unfamiliar objects or occluded environments — a structural generalization (fan hua xing) limitation. The temporal-scale mismatch between high-level task planning (1-10 Hz) and low-level body control (100+ Hz) remains an unresolved bottleneck.')),
      P(N('Despite these constraints, field deployment is expanding rapidly. The dominant industry approach follows a "custom development to standardized delivery" path, beginning with controlled, repetitive environments such as manufacturing plants and logistics warehouses and progressively expanding to more complex settings. This reflects a pragmatic strategy of creating immediate value while acknowledging technical limitations.')),
      BK(), PB(),

      // ═══════════════════════════════════════════════════════
      // PAGE 4: Chapter II
      // ═══════════════════════════════════════════════════════
      H1C('Technology Innovation — Data-Driven SW-HW Integration'),
      H2C('Algorithm Technology: Four Pathways in Parallel'),
      textBox('KEY MESSAGE', [
        P(N('The technology evolution from LLM to VLM to VLA to World Model is rapidly elevating the cognitive and decision-making capabilities of Embodied AI. The four-fold surge in VLA-related papers to 1,700+ in 2025 demonstrates that both academia and industry are investing intensively in this direction.')),
      ]),
      BK(),
      P(N('The algorithmic brain of Embodied AI divides into four distinct development pathways. These four paths compete with and complement one another simultaneously, with different approaches proving optimal for different application scenarios. The analogy to automotive powertrains is apt: just as internal combustion, hybrid, electric, and hydrogen engines each find their optimum use cases and environments, no single AI pathway is the definitive answer across all Embodied AI applications.')),
      P(N('Path 1 (Modular Layering) stacks deep learning for perception, machine learning for motor skills, and programmed logic in hierarchical layers. This approach is already validated in AMR warehouse logistics and sports-demonstration robots, with high stability and predictability as its core advantages. Path 2 (Layered Foundation Models) uses LLMs and VLMs to formulate high-level plans and calls lower-level action policies via API. Google\'s Gemini Robotics-ER 1.5 has adopted this approach, with the ability to directly understand language commands as its key strength.')),
      P(N('Path 3 (End-to-End VLA) unifies visual, linguistic, and action modalities within a single transformer architecture. Physical Intelligence\'s pi0.5, Figure AI\'s Helix, and BAAI\'s RoboBrain 2.0 are the leading examples. Figure AI Helix\'s achievement of combining a 7-9 Hz perception-reasoning loop with a 200 Hz body motion control loop in a single system marks a milestone for Path 3 in production. Path 4 (World Model) internalizes the physics of the environment, enabling the agent to simulate future states before acting — analogous to a human estimating the weight of an object and adjusting grip force before lifting it. NVIDIA\'s Cosmos Predict, Ctrl-World, and DreamVLA are representative research directions.')),
      BK(),
      new Paragraph({
        children: [new TextRun({ text: '< VLA Architecture Design Comparison >', bold: true, size: 20, font: F, color: '555555' })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 100, after: 80 },
      }),
      makeTable(
        ['Dimension', '"Unified" Single-System', '"Layered" Dual-System'],
        [
          ['Representative', 'UniAct, GEN-0', 'Helix (Figure AI), FiS'],
          ['Design', 'One network integrates planning to control', 'High-speed cognition + high-frequency control separate'],
          ['Strength', 'Parameter efficiency & generalization potential', 'Real-time control accuracy & stability'],
          ['Weakness', 'Low-level control speed limits', 'Complexity of synchronizing two systems'],
          ['Primary Use', 'Cross-embodiment generalization research', 'Industrial production deployment'],
        ]
      ),
      BK(),
      H2C('Data: The "Crude Oil" of Embodied AI'),
      textBox('KEY MESSAGE', [
        P(N('Training Embodied AI requires tens of thousands to millions of hours of high-quality motion data. How efficiently companies acquire and leverage this data has become the defining variable for competitive advantage, and a dual strategy combining simulation-synthesized and real-robot-collected data has become the industry standard.')),
      ]),
      BK(),
      P(N('Data is the crude oil of Embodied AI. Just as crude oil is useless without vehicles to power, robot motion data is valueless without Embodied AI systems to train. Paradoxically, those AI systems cannot advance without the data. To resolve this chicken-and-egg dilemma, the industry has adopted a dual strategy: large-scale simulation-synthesized data for volume and real-robot-collected data for quality fine-tuning. Each approach has distinct tradeoffs, and no single method currently provides a complete answer.')),
      P(N('Simulation-synthesized data uses physics simulators and world models to generate motion trajectories, collision responses, and object manipulation data at scale in virtual environments. Its strengths are low cost, zero safety risk, and 24/7 parallel generation capacity. However, the physics of virtual environments never perfectly mirror reality, creating the "Sim-to-Real Gap" — the performance degradation that occurs when policies learned in simulation are transferred to real robots. This gap is particularly severe for contact dynamics such as friction, elasticity, and multi-point contact, which are notoriously difficult to simulate accurately.')),
      P(N('Real-robot collection gathers actual robot motion data through teleoperation, VR gloves, exoskeleton rigs, optical motion capture, and inertial measurement systems. This produces realistic, high-fidelity data, but at high cost and with limited scalability. The current best practice combines the two approaches: generating foundational training data in simulation at scale, then collecting high-quality fine-tuning data from real robots. The question of "what to collect and how to use it" remains an active area without industry consensus.')),
      BK(),
      H2C('Hardware Diversification: Competing Visions of the Optimal Form'),
      textBox('KEY MESSAGE', [
        P(N('Diverse hardware forms — humanoids, quadrupeds, collaborative arms — are accelerating SW-HW integrated component innovation around sensing, actuation, energy, and execution systems. Unitree Robotics\' launch of the R1 humanoid at 39,900 yuan is a symbolic event demonstrating that the price barrier for humanoid robots is falling rapidly.')),
      ]),
      BK(),
      P(N('In Embodied AI, the hardware body is the physical interface through which AI capability is realized in the world. The choice of hardware form fundamentally determines the applicable use cases, required control algorithms, and data collection strategies. Currently, the market features humanoid robots optimized for human-designed environments, quadruped robots suited to rough terrain, and collaborative arms specialized for precision work — all developing in parallel to address distinct needs.')),
      P(N('Among recent noteworthy hardware innovations, Unitree Robotics\'s R1 humanoid at 39,900 yuan represents a paradigm-shifting reduction in market entry cost. Agility Robotics\' Digit validated commercial viability by executing real logistics missions in Amazon fulfillment centers. Apptronik\'s Apollo secured software competitiveness through its collaboration with Google DeepMind. These examples illustrate how hardware innovation and AI innovation are mutually catalyzing, accelerating the entire Embodied AI ecosystem.')),
      P(N('The three-tier cloud-edge-terminal computing architecture is also a critical hardware development direction. The cloud handles large-scale data storage, simulation, and model training; the edge manages data preprocessing and skill orchestration; and the terminal (onboard inference chip) handles real-time motion control. This architecture enables robots to maintain basic operations without cloud connectivity while leveraging advanced capabilities when connected — a critical resilience property for real-world deployment.')),
      BK(), PB(),

      // ═══════════════════════════════════════════════════════
      // PAGE 5: Chapter III
      // ═══════════════════════════════════════════════════════
      H1C('Product Ecosystem — Scene-Driven Diversification'),
      H2C('Robots: The Hottest Embodied AI Platform'),
      textBox('KEY MESSAGE', [
        P(N('Humanoid robots have emerged as the primary platform for Embodied AI as competition between US and Chinese companies intensifies. Three competing business models — full-stack integration, hardware focus, and software-brain specialization — are each validating their thesis in different market segments.')),
      ]),
      BK(),
      P(N('The reason humanoid robots have become the primary Embodied AI product form is straightforward: the human-designed world — factories, homes, offices — is optimized for human bodies. A humanoid form that walks on two legs, manipulates objects with two hands, and perceives at eye level can leverage existing infrastructure without modification. In this regard, humanoid robots offer broader generalizability and potentially larger market scale than purpose-built task-specific robots.')),
      P(N('Full-Stack Integrators pursue vertical integration from software to hardware. Figure AI is developing its Helix end-to-end model in-house and integrating it with its own robot platform, seeking world-class integrated performance. The $1 billion raised from Microsoft, OpenAI, and Bezos Expeditions — validating a $39 billion enterprise valuation — reflects the market\'s conviction in this strategy. ZHIYUAN Robotics in China is building a competing full-stack approach by integrating its Go-1 platform with its proprietary world model, Genie.')),
      P(N('Hardware-Focused Players concentrate on radical hardware cost reduction. Unitree Robotics\'s R1 at 39,900 yuan is the symbolic event of this strategy. Agility Robotics\' Digit has demonstrated commercial viability in Amazon warehouses, and Apptronik\'s Apollo secured software competitiveness through its Google DeepMind collaboration. Software-Brain Specialist Physical Intelligence\'s decision to open-source pi0.5 is a deliberate ecosystem play — enabling hardware partners to develop on its platform and building a network-effect moat.')),
      BK(),
      new Paragraph({
        children: [new TextRun({ text: '< Humanoid Robot: Three Strategic Camps >', bold: true, size: 20, font: F, color: '555555' })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 100, after: 80 },
      }),
      makeTable(
        ['Camp', 'Key Players', 'Core Strategy', 'Strength', 'Risk'],
        [
          ['Full-Stack', 'Figure AI, ZHIYUAN', 'Vertical SW-HW integration', 'Best-in-class performance', 'High capex requirement'],
          ['Hardware-Focus', 'Unitree, Agility, Apptronik', 'Hardware cost innovation', 'Fast market entry', 'SW capability dependency'],
          ['SW-Brain', 'Physical Intelligence, Field AI', 'General algorithm dev', 'Multi-HW compatibility', 'Body control limitations'],
        ]
      ),
      BK(),
      H2C('Smart Mobility: The Fastest-Commercializing Segment'),
      textBox('KEY MESSAGE', [
        P(N('Autonomous vehicles and drones are the fastest-commercializing Embodied AI platforms. The combined market of $172.2 billion for AVs and $163.6 billion for drones by 2030 is already being validated by commercial services expanding in structured environments today.')),
      ]),
      BK(),
      P(N('While humanoid robots remain in early commercialization, autonomous vehicles and drones have already accumulated millions of kilometers of real-road driving data and hundreds of thousands of hours of flight data. These platforms serve as the most extensively validated testbeds for Embodied AI technology — particularly perception, planning, and control. The algorithms and data accumulated in the process represent valuable assets that can be transferred to humanoid robots and other Embodied AI platforms.')),
      P(N('Autonomous vehicles — currently dominated by L1-L3 — are advancing toward full autonomy (L4-L5) along a path that extends from structured highway environments to unstructured urban and off-road environments. The 2030 market projection of $172.2 billion (L1-L3) reflects only the near-term trajectory. Drones are expanding into aerial, underwater, and extreme environment applications toward a projected $163.6 billion market by 2030. Swarm drone and micro-device technologies are also developing rapidly, opening new application frontiers.')),
      BK(), PB(),

      // ═══════════════════════════════════════════════════════
      // PAGE 6: Chapter IV
      // ═══════════════════════════════════════════════════════
      H1C('Industrial Ecosystem — Investment Boom and Structural Challenges'),
      H2C('Supply Chain Expansion and Early Ecosystem Formation'),
      textBox('KEY MESSAGE', [
        P(N('The Embodied AI industrial ecosystem is forming rapidly. China\'s market alone recorded 744 investment transactions totaling 73.543 billion yuan through end-2025, with 352+ companies forming a four-block ecosystem of sector applications, product & services, technical services, and infrastructure. Sustaining this growth, however, requires simultaneously resolving three fundamental challenges: safety, standardization, and proven utility.')),
      ]),
      BK(),
      P(N('The Embodied AI supply chain consists of four major blocks. ① Infrastructure: high-performance computing chips (NVIDIA H100, GB200, etc.), training ground facilities, and cloud platforms. ② Technical Services: simulator providers (Isaac Sim, SAPIEN, Genesis), VLA model developers, and data labeling services. ③ Product Services: system integrators combining robot hardware and software to deliver solutions for specific industries. ④ Sector Applications: actual end-use deployments across manufacturing, logistics, healthcare, and construction.')),
      P(N('China\'s investment scale is the world\'s largest. By December 2025, 744 transactions had deployed 73.543 billion yuan, with 352+ companies distributed across the four hubs of Beijing, Shanghai, Shenzhen, and Hangzhou. A construction boom in "training grounds" — dedicated facilities where robots learn through repetition in simulated real-world environments — is a defining feature. However, the degree to which training-ground performance translates to complex real-world performance remains insufficiently validated, a critical question the industry must answer to sustain investor confidence.')),
      P(N('Safety and standardization are the core constraints on scaling. Unlike software AI, Embodied AI involves physical action — malfunctions can cause direct physical harm to humans. The three safety imperatives — preventing physical hazards, securing data, and attributing liability for accidents — have not been clearly resolved. The international standardization efforts of ITU and ISO, running in parallel with Chinese domestic industry standards development, are progressing, but standard completion remains years away.')),
      BK(), PB(),

      // ═══════════════════════════════════════════════════════
      // PAGE 7: Chapter V
      // ═══════════════════════════════════════════════════════
      H1C('Outlook — Three Development Directions and Long-Term Scenarios'),
      H2C('Architecture Transformation: From Modules to Fusion'),
      textBox('KEY MESSAGE', [
        P(N('The transition from "stacked functional modules" to "multimodal cognitive fusion" will drive the next technical leap in Embodied AI. As World Models evolve from supporting tools into the AI brain itself, behavior simulation and action prediction will become natively integrated capabilities.')),
      ]),
      BK(),
      P(N('Most Embodied AI systems today are built by developing perception, planning, and control modules separately and then connecting them. This is analogous to how the first smartphones combined cellular capability, a camera, and a music player as separate components. But just as the iPhone unified all these functions under a single operating system, Embodied AI is moving rapidly toward architectures where multimodal perception and action planning are processed within a single network.')),
      P(N('World Models are central to this architectural transition. A World Model enables AI to internalize the physics of its environment — to simulate "what will happen if I do this" before actually acting. This is analogous to a human estimating the weight of an object and calibrating grip force before lifting it. The surge in World Model research — NVIDIA\'s Cosmos Predict, Ctrl-World, V-JEPA 2 — signals broad conviction in this technical direction.')),
      BK(),
      H2C('Application Deepening: From "Demonstration" to "Utility"'),
      textBox('KEY MESSAGE', [
        P(N('Embodied AI application scenarios will expand in stages — from controlled environments (manufacturing, logistics) through semi-structured environments (home, healthcare) to unstructured environments (extreme, outdoor). The completion of the "custom development to standardized delivery to lifecycle support" commercialization loop is the key performance indicator for this transition.')),
      ]),
      BK(),
      P(N('Current Embodied AI commercialization is largely in the "demonstration" phase. Impressive results are shown at exhibitions and in pilot projects, but cases where robots have replaced human workers in actual production environments to generate economic value remain limited. The reason Agility Robotics\' Digit deployment in Amazon warehouses attracts such attention is precisely its rarity. The speed of the "demonstration to utility" transition is existential for Embodied AI companies.')),
      P(N('Application scenario expansion will likely follow a difficulty gradient. Near-term: repetitive, predictable tasks in manufacturing and logistics will be automated first. Medium-term: home services (domestic assistance, elderly care) and healthcare assistance (medication delivery, patient transfer support) will be unlocked — here, the ability to handle unpredictable human interactions becomes the critical requirement. Long-term: Embodied AI will extend to extreme environments inaccessible to humans — disaster zones, deep ocean, space.')),
      BK(),
      H2C('Safety and Ethics: Prerequisites for Sustainable Growth'),
      textBox('KEY MESSAGE', [
        P(N('The transition from "regulatory compliance" to a "comprehensive ethical cooperation framework" is necessary. Without resolving the four imperatives of functional safety, cybersecurity, liability attribution, and privacy protection, Embodied AI\'s technological progress may be blocked by the wall of social acceptability.')),
      ]),
      BK(),
      P(N('Embodied AI carries fundamentally different risks than software AI. When a chatbot produces an incorrect answer, users are disappointed. When a humanoid robot malfunctions, physical injury results. When an autonomous vehicle makes a wrong judgment, lives may be lost. This physicality means Embodied AI safety standards must be far stricter than those for software AI, and international standards bodies are actively working to define them.')),
      P(N('Cybersecurity is a distinct concern: if an Embodied AI system is compromised, the attack vector is not just data exfiltration but physical harm. Privacy issues are particularly acute for home service robots — devices that perceive and learn from every activity within the home generate extraordinarily sensitive personal data. Liability attribution for accidents — who bears responsibility among manufacturer, operator, and user — remains a legal frontier without established precedent in most jurisdictions.')),
      BK(), PB(),

      // ═══════════════════════════════════════════════════════
      // PAGE 8: Devil's Advocate
      // ═══════════════════════════════════════════════════════
      H1C("Devil's Advocate — Five Critical Challenges"),
      textBox("① VLA Generalization Limitations: Still Only Good at the Familiar", [
        P(N('The impressive demo videos produced by VLA models come with an implicit asterisk: they were generated "within the training data distribution." Both 1X World Model and Physical Intelligence pi0.5 are reported to show sharp performance drops with unfamiliar objects, novel environments, or unexpected occlusions. A robot trained 1,000 times to grasp a cup may still fail when the cup shape is slightly different or the lighting changes. This reflects the fundamental limitation of current VLAs — they rely on "pattern recognition" rather than "understanding." The distance to a truly general-purpose Embodied AI remains considerable.')),
      ]),
      BK(),
      textBox("② Insufficient Long-Horizon Task Capability: The 20-40% Reality", [
        P(N('Google Gemini Robotics-ER 1.5\'s 20-40% success rate on "trash sorting" and "item exchange" tasks is not merely a symptom of technical immaturity — it reflects a structural problem. Long-horizon tasks require dozens of sub-actions to execute in precise sequence; a single error at any step cascades to complete failure. More fundamentally, the temporal-scale mismatch between high-level task planning (1-10 Hz) and low-level body control (100+ Hz) creates a persistent bottleneck. The dilemma of a slow-thinking brain directing fast-moving limbs will continue to block complex assembly, sophisticated cooking, and other dexterous multi-step tasks until resolved.')),
      ]),
      BK(),
      textBox("③ Incomplete SW-HW Integration: One Weak Link Breaks the Chain", [
        P(N('The performance of an SW-HW co-control chain is determined by its weakest link. A 1ms signal transmission delay in a 100 Hz control loop causes motion instability that cascades to task failure. The "cross-embodiment transfer problem" — VLA models validated on one robot failing to reproduce their performance when transferred to a different robot architecture — remains unresolved. Overcoming this without standardized hardware interfaces and software abstraction layers presents a formidable technical challenge. Until the industry converges on common standards, each deployment effectively requires bespoke engineering.')),
      ]),
      BK(),
      textBox("④ Data Scarcity and the Sim-to-Real Gap: A Deep Structural Divide", [
        P(N('Real-robot data remains scarce, and the diversity provided by training grounds falls short of covering the full complexity of real-world environments. Simulation-synthesized data has compelling cost and scale advantages, but accurately simulating contact dynamics — friction, elasticity, multi-point contact — remains particularly difficult. Models trained on simulation data frequently experience performance collapse on contact-dynamics-related tasks when deployed to real robots. Domain Randomization can reduce but not eliminate this gap. The industry\'s question of "what data to collect and how to use it" lacks consensus, leaving each player to rediscover lessons independently.')),
      ]),
      BK(),
      textBox("⑤ High Cost and Absent Standardization: Two Barriers to Scale", [
        P(N('Humanoid robot systems still cost hundreds of thousands to millions of Korean won, making economic viability in the home services market dependent on substantial further cost reduction. Unitree Robotics\' R1 at 39,900 yuan is a symbolic milestone but still not consumer-grade pricing. The absence of standardization is a separate but equally constraining challenge: each robot manufacturer\'s proprietary interfaces and communication protocols make supply chain optimization and software reuse extremely difficult. While ROS 2 (Robot Operating System) is emerging as a software standard, physical interface standards remain in their infancy. Without common standards, the industry cannot achieve the network effects that accelerate maturation in other technology sectors.')),
      ]),
      BK(), PB(),

      // ═══════════════════════════════════════════════════════
      // PAGE 9: Conclusion
      // ═══════════════════════════════════════════════════════
      H1('Conclusion & Outlook: Embodied AI — The Long Hill with Deep Snow'),
      P(B('Summary: ', 22), N('Embodied AI is a "long hill with deep snow" race in which technology (VLA, World Models), products (humanoid robots, autonomous vehicles), and the industrial ecosystem are all developing simultaneously. Currently in the early commercialization phase, it is a market where the sober reality of a 20-40% VLA success rate coexists with the long-term potential of a $339.8 billion market. A period of explosive growth beginning in 3-5 years as technology matures appears increasingly likely.')),
      BK(),
      P(N('NVIDIA CEO Jensen Huang\'s reaffirmation of Physical AI as the "next frontier" at GTC 2026 confirms that Embodied AI is no longer a future concept. Through the three carrier platforms of humanoid robots, autonomous driving, and drones, Embodied AI is already deployed in industrial settings, accumulating millions of hours of training data at this very moment. The most important question for this industry is when the "virtuous cycle" begins — when more data produces better models, better models enable more real-world deployments, and more deployments generate even more data.')),
      BK(),
      H2('Stakeholder Perspectives'),
      P(N('► Individuals: As home service robots evolve into AI "smart assistants," AI literacy and Embodied-AI-adjacent skills (ROS, simulators, VLA fine-tuning) will become new competitive advantages. Proactive preparation for job displacement and human-robot collaboration models is advisable.')),
      P(N('► Organizations: Develop ROI frameworks for manufacturing and logistics automation, and make ahead-of-time decisions on Embodied AI adoption strategy (build vs. fine-tune vs. API). Establish data ownership and utilization policies for robot operational data.')),
      P(N('► Society: Urgently needed: legal frameworks for autonomous robot safety standards and accident liability. Social safety nets and reskilling systems must be developed in anticipation of labor market restructuring in manufacturing, logistics, and healthcare.')),
      P(N('► Nations: Physical AI infrastructure investment (high-performance simulators, data centers, training grounds) and specialist talent development (robotics + ML + systems engineering) are core national competitiveness variables. Leading the international standards negotiation for Embodied AI is a critical diplomatic priority.')),
      P(N('► Global: Competition for supply chain stability and international standardization leadership will intensify across the $339.8 billion market. The standard-setting contest between Western tech giants (NVIDIA, Google, Meta) and Chinese players will fundamentally determine the topology of the global Embodied AI ecosystem.')),
      BK(),
      H2('Core Keywords'),
      P(N('#EmbodiedAI, #VLA, #WorldModel, #HumanoidRobot, #AutonomousVehicles, #Drone, #FigureAI, #Helix, #PhysicalIntelligence, #pi0.5, #Unitree, #AgilityRobotics, #ITU-T-F748-66, #EndToEnd, #ModularLayering, #LayeredFoundationModel, #SimToRealGap, #SimulationData, #ChallengeCycle, #CAICT, #EmbodiedIntelligence, #339billionMarket')),
      BK(),
      H2('References'),
      new Paragraph({
        children: [
          new TextRun({ text: '• ', font: F, size: 21 }),
          new ExternalHyperlink({
            link: 'https://www.caict.ac.cn',
            children: [new TextRun({
              text: 'CAICT, "Embodied Intelligence Development Report (2025)," China Academy of Information and Communications Technology & Tsinghua University School of Electronics Engineering, January 2026',
              font: F, size: 21, color: '0563C1',
              underline: { type: UnderlineType.SINGLE, color: '0563C1' },
            })],
          }),
        ],
        spacing: { before: 0, after: 120 },
      }),
    ],
  }],
});

const OUTPUT = '/sessions/funny-jolly-euler/embodiedai_build/EmbodiedAI_EN_Report_20260408.docx';
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(OUTPUT, buf);
  console.log('English DOCX written:', OUTPUT, '(' + Math.round(buf.length/1024) + ' KB)');
}).catch(err => {
  console.error('Build failed:', err.message);
  process.exit(1);
});
