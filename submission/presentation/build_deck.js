const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/root/.claude/skills/synced/3a50b898-974f-4792-b87f-c7b3e90a0fc9_c3f89f6a-28e8-408d-acae-d4eda861bcf4/pptx/scripts/apply_theme.js");

const THEME = {
  name: "LearnMate Research",
  headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1:"0B1F33", lt1:"FFFFFF", dk2:"1B3A57", lt2:"EEF3F7",
    accent1:"1B7F8C", accent2:"C98200", accent3:"BF4A36", accent4:"5B6B7B", accent5:"3A7CA5", accent6:"4F8F5B",
    hlink:"1B7F8C", folHlink:"5B6B7B" }
};
const H = THEME.colors; // hex for charts / tables
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "LearnMate G06: Evidence-Grounded Course AI Tutor (progress presentation)";
pres.author = "Group G06";
const C = pres.SchemeColor;

pres.defineSlideMaster({ title: "LM_DARK", background: { color: "0B1F33" }, objects: [] , slideNumber: undefined});
pres.defineSlideMaster({
  title: "LM_CONTENT", background: { color: "FFFFFF" },
  objects: [
    { text: { text: "LearnMate · G06 · M.Tech AI&ML · Deep Learning Networks · CCA-2 / LCA-3", options: { x: 0.6, y: 7.05, w: 9, h: 0.3, fontSize: 10, color: "5B6B7B", fontFace: "Calibri", margin: 0 } } },
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.95, fontFace: "Cambria", fontSize: 30, bold: true, color: "0B1F33", align: "left", valign: "middle", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 12.2, y: 7.05, w: 0.5, h: 0.3, fontSize: 10, color: "5B6B7B", fontFace: "Calibri", align: "right" },
});

const TEAL = H.accent1, NAVY = H.dk1, SLATE = H.accent4, AMBER = H.accent2, CORAL = H.accent3, BLUE = H.accent5, GREEN = H.accent6, PALE = H.lt2;
let sectionOpen = null;
function section(t) { pres.addSection({ title: t }); sectionOpen = t; }
function content(title, notes, sec) {
  const s = pres.addSlide({ masterName: "LM_CONTENT", sectionTitle: sec || sectionOpen });
  s.addText(title, { placeholder: "title" });
  if (notes) s.addNotes(notes);
  return s;
}
function T(s, text, o) { s.addText(text, Object.assign({ isTextBox: true, fontFace: "Calibri", fontSize: 16, color: NAVY, margin: 0, valign: "top" }, o)); }
function box(s, x, y, w, h, fill, o) { s.addShape(pres.ShapeType.roundRect, Object.assign({ x, y, w, h, fill: { color: fill }, line: { color: fill, width: 0 }, rectRadius: 0.08 }, o || {})); }
function src(s, text) { T(s, text, { x: 0.6, y: 6.72, w: 12.1, h: 0.3, fontSize: 10.5, color: SLATE, italic: true }); }
function arrow(s, x1, y1, x2, y2, color) {
  const o = { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), line: { color: color || SLATE, width: 1.75, endArrowType: "triangle" } };
  if (x2 < x1) o.flipH = true; if (y2 < y1) o.flipV = true;
  s.addShape(pres.ShapeType.line, o);
}
function seg(s, x1, y1, x2, y2, color) {
  const o = { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), line: { color: color || SLATE, width: 1.75 } };
  if (x2 < x1) o.flipH = true; if (y2 < y1) o.flipV = true;
  s.addShape(pres.ShapeType.line, o);
}
function tag(s, text, x, y, w, color) {
  s.addText(text, { x, y, w, h: 0.3, shape: pres.ShapeType.roundRect, rectRadius: 0.15, fill: { color }, color: "FFFFFF", fontFace: "Calibri", fontSize: 11, bold: true, align: "center", valign: "middle", margin: 0, isTextBox: true });
}

// ============ 1 TITLE ============
section("Opening");
{
  const s = pres.addSlide({ masterName: "LM_DARK", sectionTitle: "Opening" });
  // motif: document stack -> retrieval -> verification -> answer (simple native shapes, right side)
  const cols = ["1B3A57", "1B7F8C", "3A7CA5", "C98200"];
  const labels = ["Course\ndocuments", "Retrieve", "Verify", "Answer or\nabstain"];
  labels.forEach((l, i) => {
    box(s, 8.25 + (i % 2) * 2.25, 1.55 + Math.floor(i / 2) * 2.1, 1.95, 1.55, cols[i]);
    T(s, l, { x: 8.25 + (i % 2) * 2.25, y: 1.55 + Math.floor(i / 2) * 2.1, w: 1.95, h: 1.55, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
  });
  arrow(s, 10.2 + 0.0, 2.32, 10.5, 2.32, "9FB3C8");
  arrow(s, 9.22, 3.1, 9.22, 3.65, "9FB3C8");
  arrow(s, 10.2, 4.42, 10.5, 4.42, "9FB3C8");
  T(s, "LearnMate", { x: 0.7, y: 1.3, w: 7.2, h: 1.0, fontFace: "Cambria", fontSize: 54, bold: true, color: "FFFFFF" });
  T(s, "Evidence-Grounded Course AI Tutor", { x: 0.7, y: 2.35, w: 7.2, h: 0.6, fontFace: "Cambria", fontSize: 26, color: "9ED5DC" });
  T(s, "Retrieval-augmented generation with evidence verification and calibrated abstention: implementation progress and preliminary results", { x: 0.7, y: 3.15, w: 6.9, h: 1.0, fontSize: 18, color: "D6E2EC" });
  T(s, [
    { text: "M.Tech Artificial Intelligence & Machine Learning · Deep Learning Networks", options: { breakLine: true } },
    { text: "CCA-2 / LCA-3 · Academic Year 2026–2027 · Group G06", options: { breakLine: true } },
    { text: "[Institution] · [Team members] · [Faculty guide] · [Presentation date]" },
  ], { x: 0.7, y: 5.2, w: 7.3, h: 1.2, fontSize: 14, color: "9FB3C8", paraSpaceAfter: 4 });
  s.addNotes("Open by stating the status: the system is built and evaluated once on a locked test set; the headline result is a preliminary null on our registered hypothesis, and the deck is honest about that. Placeholders in brackets (institution, names, guide, date) must be filled before presenting. Two presenters: agree the split between you in advance; nothing in this deck assigns sections to either member.");
}

// ============ 2 PROBLEM ============
section("Problem and context");
{
  const s = content("A plausible answer is not the same as a supported answer",
    "Explain the three cases. Case 1 is the goal: the course passage entails the answer and it is cited. Case 2 is the subtle failure: the statement may be true in the world, but the course text shown to the student does not say it, so for a course tutor it is unsupported. Case 3 is the dangerous one: an out-of-syllabus question that should be refused with pointers to related sections. Examples are drawn from our own evaluation set and smoke test, shown for illustration only. Transition: the handbook makes exactly this the assigned challenge.");
  const cards = [
    { c: GREEN, h: "1  Supported", q: "What does dropout do during training?", a: "“Dropout zeroes hidden units at random during training [C1].”", v: "The cited course passage entails the answer.", t: "ANSWER" },
    { c: AMBER, h: "2  True, not in the text", q: "How does multi-head attention combine its heads, and how many heads does the original Transformer use?", a: "States a specific head count for the original model.", v: "The retrieved passages never give that number: factual ≠ grounded.", t: "UNSUPPORTED CLAIM" },
    { c: CORAL, h: "3  Evidence missing", q: "Who proposed the VGG network?", a: "A fluent attribution is easy to generate.", v: "The indexed chapters do not say. Correct behaviour: abstain and show related sections.", t: "SHOULD ABSTAIN" },
  ];
  cards.forEach((k, i) => {
    const x = 0.6 + i * 4.1;
    box(s, x, 1.55, 3.85, 4.55, PALE);
    tag(s, k.t, x + 0.2, 1.7, 2.05, k.c);
    T(s, k.h, { x: x + 0.2, y: 2.1, w: 3.45, h: 0.4, fontFace: "Cambria", fontSize: 17, bold: true });
    T(s, [{ text: "Question", options: { bold: true, color: SLATE, fontSize: 12, breakLine: true } }, { text: k.q, options: { fontSize: 14 } }], { x: x + 0.2, y: 2.6, w: 3.45, h: 1.15 });
    T(s, [{ text: "Typical fluent answer", options: { bold: true, color: SLATE, fontSize: 12, breakLine: true } }, { text: k.a, options: { fontSize: 14, italic: true } }], { x: x + 0.2, y: 3.8, w: 3.45, h: 1.0 });
    T(s, [{ text: "Verdict", options: { bold: true, color: k.c, fontSize: 12, breakLine: true } }, { text: k.v, options: { fontSize: 14 } }], { x: x + 0.2, y: 4.85, w: 3.45, h: 1.15 });
  });
  src(s, "Illustrative cases drawn from our smoke test and evaluation items (course: Dive into Deep Learning [21]). Motivation: sufficient-context studies [1].");
}

// ============ 3 ASSIGNED CHALLENGE ============
{
  const s = content("The assigned research challenge: G06 LearnMate",
    "This slide is traceable to page 5 of the handbook. Read the problem statement, then point out the split: the left column is what the prototype must do; the right column is what the research must show. The handbook also says to check whether the approach is already published, which is why our framing is a controlled evaluation and not a novelty claim. Transition: what has the literature established?");
  box(s, 0.6, 1.5, 12.1, 1.15, NAVY);
  T(s, [{ text: "Handbook problem statement (G06). ", options: { bold: true, color: "9ED5DC" } }, { text: "“AI tutors may provide plausible but unsupported explanations. Develop a course-specific document-grounded assistant that cites its sources and abstains when evidence is inadequate.”", options: { color: "FFFFFF" } }], { x: 0.85, y: 1.5, w: 11.6, h: 1.15, fontSize: 17, valign: "middle" });
  const L = ["Input: a student question in English", "Output: answer with sentence-level citations, or a typed abstention", "Every citation resolves to a stored course passage", "Fail closed: any component error leads to abstention", "Working user-facing demonstration"];
  const R = ["Quantify an application-relevant failure mode", "Two justified baselines (Sentence Transformers, small LLM, RAG)", "SQuAD 2.0 plus course material with split, leakage and label audit", "Test evidence agreement and calibrated abstention with an ablation and a stressed condition", "Comparative metrics, limitations, reproducibility package"];
  [["Functional requirements (prototype)", L, TEAL, 0.6], ["Research requirements (evidence)", R, AMBER, 6.85]].forEach(([h, arr, col, x]) => {
    box(s, x, 2.9, 5.85, 3.65, PALE);
    T(s, h, { x: x + 0.25, y: 3.0, w: 5.4, h: 0.4, fontFace: "Cambria", fontSize: 18, bold: true, color: col });
    T(s, arr.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < arr.length - 1 } })), { x: x + 0.25, y: 3.5, w: 5.4, h: 2.95, fontSize: 16, paraSpaceAfter: 8 });
  });
  src(s, "Source: CCA-2/LCA-3 handbook, G06 specification (p. 5). Suggested architectures: Sentence Transformers, small LLM, RAG. Datasets: SQuAD 2.0 plus approved course materials [11].");
}

// ============ 4 LANDSCAPE ============
section("Literature");
{
  const s = content("Research landscape: three linked streams",
    "Walk left to right. Retrieval brings candidate evidence; generation turns it into cited prose; verification and abstention decide whether to show it. The tutoring context box reminds the audience that small local models with RAG are already used in computing education [10], but without verification or calibrated abstention. Cross-links matter: retrieval relevance does not guarantee sufficiency, and a citation being present does not guarantee support. Transition to the literature table.");
  const colsd = [
    { h: "Retrieve", c: TEAL, items: ["Retrieval-augmented generation [14]", "Dense retrieval and sentence embeddings [15][16]", "Hybrid fusion of rankings [17]"] },
    { h: "Generate and cite", c: BLUE, items: ["Citation-grounded generation, ALCE [12]", "Aligning models to cite or refuse, Trust-Align [2]", "Correct vs faithful attribution [9]"] },
    { h: "Verify and abstain", c: AMBER, items: ["Sufficient context [1]", "Claim-level support checking, MiniCheck [3]", "Hallucination data and detectors [4][5]", "Abstention evaluation [6][7][8]; selective prediction [13][18]"] },
  ];
  colsd.forEach((k, i) => {
    const x = 0.6 + i * 4.15;
    box(s, x, 1.55, 3.8, 0.6, k.c);
    T(s, k.h, { x, y: 1.55, w: 3.8, h: 0.6, fontFace: "Cambria", fontSize: 19, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
    box(s, x, 2.25, 3.8, 3.2, PALE);
    T(s, k.items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < k.items.length - 1 } })), { x: x + 0.2, y: 2.4, w: 3.45, h: 2.95, fontSize: 16.5, paraSpaceAfter: 9 });
    if (i < 2) arrow(s, x + 3.82, 3.85, x + 4.13, 3.85, SLATE);
  });
  box(s, 0.6, 5.65, 12.1, 0.85, NAVY);
  T(s, [{ text: "Tutoring context: ", options: { bold: true, color: "9ED5DC" } }, { text: "small local language models with RAG have been deployed in computing courses [10], but without claim-level verification or calibrated abstention.", options: { color: "FFFFFF" } }], { x: 0.85, y: 5.65, w: 11.6, h: 0.85, fontSize: 16, valign: "middle" });
  src(s, "Numbers refer to the reference slides. Verification status of each source is listed in the references appendix.");
}

// ============ 5 LIT TABLE ============
{
  const s = content("Literature review: key studies and what they leave open",
    "Pick two rows to talk through. Joren et al. propose using context sufficiency to guide selective generation, with large autoraters; we ask whether a small trained local gate transfers to course text. Setiawan shows prompt-only abstention is fragile under misleading context, which is exactly our B1 baseline. Wallat separates citation correctness from faithfulness, motivating our withheld-gold stress test. The full 10-paper matrix is in Deliverable B. Be explicit that we did not re-read numbers from the primary texts for every source; no quantitative claim from those papers is used in this deck.");
  const hdr = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, fontSize: 13, fontFace: "Calibri" } });
  const cell = (t, o) => ({ text: t, options: Object.assign({ fontSize: 13, fontFace: "Calibri", color: NAVY, valign: "middle" }, o || {}) });
  const rows = [
    ["Joren et al. 2025 [1]", "Context-sufficiency autorater feeds selective generation", "Large (24B-class) rater; open-domain QA", "Small trained local gate on course text"],
    ["Song et al. 2025 [2]", "Alignment for grounded citations and refusal (Trust-Align)", "Requires training the generator", "Abstain without retraining the generator"],
    ["Tang et al. 2024 [3]", "MiniCheck: small fact-checkers for grounding", "Not tested on notation-heavy text", "Claim-level verifier; report maths slice"],
    ["Kirichenko et al. 2025 [6]", "AbstentionBench: 20 datasets, 20 LLMs", "Not RAG-specific", "Do not rely on prompt-only abstention"],
    ["Setiawan 2026 [7]", "Prompt abstention fails under misleading context", "No trained or calibrated gate", "Trained, calibrated gate in a course setting"],
    ["Wallat et al. 2025 [9]", "Correctness is not faithfulness in attributions", "One model family", "Motivates withheld-evidence stress S1"],
    ["Yu et al. 2025 [10]", "Local small LM + RAG tutor in a CS1 course", "No verification or abstention", "Add verified citations and abstention"],
  ].map((r, i) => r.map((t, j) => cell(t, { bold: j === 0, fill: { color: i % 2 ? "FFFFFF" : PALE } })));
  s.addTable([[hdr("Study"), hdr("Method / contribution"), hdr("Limitation"), hdr("Relevance to LearnMate")], ...rows],
    { x: 0.6, y: 1.5, w: 12.1, colW: [2.35, 3.85, 2.85, 3.05], rowH: [0.4, 0.66, 0.66, 0.66, 0.66, 0.66, 0.66, 0.66], border: { type: "solid", color: "D5DEE6", pt: 0.75 }, margin: [0.04, 0.08, 0.04, 0.08] });
  src(s, "Selected from the 10-paper matrix (Deliverable B). Verification status per source in the references appendix; no numerical result from these papers is quoted.");
}

// ============ 6 INSIGHTS ============
{
  const s = content("What the literature reveals: four unguaranteed links",
    "The chain on top is the core argument. Each arrow is a place where a conventional RAG demo silently assumes success. Relevant retrieval does not guarantee sufficient evidence [1]; having evidence does not guarantee a faithful answer; a present citation does not guarantee support [9]; and a model asked to abstain may not [6][7]. The three cards underneath state what the literature implies for method design: verify at claim level, calibrate on held-out data, and report the coverage cost. Avoid saying any paper proves these hold for course tutoring.");
  const chain = ["Retrieved passages\nare relevant", "Evidence is\nsufficient", "Answer is faithful\nto the evidence", "Model abstains\nwhen it is not"];
  chain.forEach((c, i) => {
    const x = 0.6 + i * 3.1;
    box(s, x, 1.6, 2.5, 1.1, i === 3 ? AMBER : NAVY);
    T(s, c, { x, y: 1.6, w: 2.5, h: 1.1, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
    if (i < 3) {
      T(s, "≠", { x: x + 2.52, y: 1.6, w: 0.56, h: 0.7, fontFace: "Cambria", fontSize: 30, bold: true, color: CORAL, align: "center", valign: "middle" });
      T(s, "not implied", { x: x + 2.5, y: 2.15, w: 0.6, h: 0.4, fontSize: 10, color: SLATE, align: "center" });
    }
  });
  const cards = [
    ["Sufficiency is its own question", "Models can answer when the context cannot support an answer; sufficiency of context is a separate property to estimate [1].", TEAL],
    ["Citations need checking", "A citation can be correct without the answer being faithful to it; attribution must be verified, not assumed [9][12].", BLUE],
    ["Prompt-only refusal is fragile", "Abstention by instruction degrades under misleading context and is unsolved even for strong LLMs [6][7].", AMBER],
    ["Small verifiers are viable", "Compact checkers can approximate large-model grounding checks at far lower cost [3].", GREEN],
    ["Selective prediction costs coverage", "Lower risk is bought with fewer answers, so risk–coverage must be reported together [13][18].", SLATE],
    ["Calibration needs held-out data", "Confidence scores are only meaningful when calibrated and validated on data not used to fit them [19].", CORAL],
  ];
  cards.forEach((k, i) => {
    const x = 0.6 + (i % 3) * 4.1, y = 3.05 + Math.floor(i / 3) * 1.85;
    box(s, x, y, 3.9, 1.7, PALE);
    T(s, k[0], { x: x + 0.2, y: y + 0.12, w: 3.5, h: 0.4, fontFace: "Cambria", fontSize: 15.5, bold: true, color: k[2] });
    T(s, k[1], { x: x + 0.2, y: y + 0.58, w: 3.5, h: 1.05, fontSize: 13.5 });
  });
  src(s, "Findings are paraphrased from the cited works; none of their quantitative results are reproduced here.");
}

// ============ 7 GAP ============
{
  const s = content("Research gap: a controlled evaluation, not a new algorithm",
    "State the gap precisely and modestly. Each ingredient exists: sufficiency-based selective generation, claim-level verification, calibrated detectors. We found no study combining a small trained answerability gate with claim-level verification in a local course-tutor setting and testing it against a tuned reranker-score threshold under withheld-evidence stress on an independently labelled course set. That is a replication-plus-adaptation. A negative result is a valid outcome, and as we show later, ours is negative on the registered hypothesis.");
  const rows = [
    ["Prompt-only abstention", "Fragile under misleading or missing context [6][7]", "Baseline B1: measure it in a course setting"],
    ["Retrieval-score threshold", "Relevance is not sufficiency; coverage collapses if strict [1]", "Baseline B2: tuned reranker-score threshold"],
    ["Large autoraters for sufficiency", "24B-class models are impractical on a free T4 [1]", "Small trained gate (DeBERTa-v3-base) on SQuAD 2.0 with hard negatives"],
    ["Citation presence", "A citation does not prove support [9]", "Claim-level verification (MiniCheck + NLI) of each cited sentence [3]"],
  ];
  const hx = [0.6, 4.2, 8.3], wd = [3.4, 3.9, 4.4], hd = ["Existing method", "Documented limitation", "What we investigate"];
  hd.forEach((h, i) => { T(s, h, { x: hx[i], y: 1.5, w: wd[i], h: 0.35, fontFace: "Cambria", fontSize: 15, bold: true, color: SLATE }); });
  rows.forEach((r, j) => {
    const y = 1.95 + j * 0.98;
    r.forEach((t, i) => {
      box(s, hx[i], y, wd[i], 0.85, i === 2 ? "DCEFF1" : PALE);
      T(s, t, { x: hx[i] + 0.15, y, w: wd[i] - 0.3, h: 0.85, fontSize: 14, valign: "middle", bold: i === 0 });
    });
    arrow(s, 0.6 + 3.4 + 0.02, y + 0.425, 4.18, y + 0.425, SLATE);
    arrow(s, 4.2 + 3.9 + 0.02, y + 0.425, 8.28, y + 0.425, SLATE);
  });
  box(s, 0.6, 5.95, 12.1, 0.7, NAVY);
  T(s, [{ text: "Positioning: ", options: { bold: true, color: "9ED5DC" } }, { text: "adaptation and controlled evaluation of established components for course tutoring. No claim of a new algorithm; a null result is an acceptable finding.", options: { color: "FFFFFF" } }], { x: 0.85, y: 5.95, w: 11.6, h: 0.7, fontSize: 15, valign: "middle" });
}

// ============ 8 OBJECTIVES / HYPOTHESIS ============
{
  const s = content("Objectives and a falsifiable hypothesis, registered before testing",
    "Read the research question, then the hypothesis. H1 is deliberately demanding: it requires the whole confidence interval of the AURC difference to be below zero, and a limit on lost coverage. The tolerance m of 10 percentage points was set by the team and is flagged as pending instructor confirmation. Emphasise the pre-registration: the document was frozen with hashes before any test output was produced, and the analysis code and thresholds were fixed. Transition to the architecture.");
  const obj = ["Build a course-grounded tutor with traceable citations", "Detect insufficient evidence with a trained, calibrated gate", "Verify claims and abstain in a typed, auditable way", "Evaluate against strong baselines, a stress test and ablations"];
  obj.forEach((t, i) => {
    const y = 1.55 + i * 0.95;
    s.addShape(pres.ShapeType.ellipse, { x: 0.6, y: y + 0.1, w: 0.6, h: 0.6, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
    T(s, String(i + 1), { x: 0.6, y: y + 0.1, w: 0.6, h: 0.6, fontSize: 18, bold: true, color: "FFFFFF", align: "center", valign: "middle", fontFace: "Cambria" });
    T(s, t, { x: 1.4, y, w: 4.7, h: 0.8, fontSize: 16, valign: "middle" });
  });
  box(s, 6.4, 1.5, 6.3, 5.0, PALE);
  T(s, "Research question", { x: 6.65, y: 1.6, w: 5.8, h: 0.35, fontFace: "Cambria", fontSize: 16, bold: true, color: TEAL });
  T(s, "Does a trained evidence-sufficiency gate with claim-level verification reduce the risk of unsupported course answers, relative to a tuned reranker-score threshold, without losing too many answerable questions?", { x: 6.65, y: 2.0, w: 5.8, h: 1.35, fontSize: 15 });
  T(s, [{ text: "H1  ", options: { bold: true, color: TEAL } }, { text: "On the locked course test, the 95% paired-bootstrap CI (10,000 resamples) of AURC(G) − AURC(B2) lies entirely below 0, and answerable coverage of G is within 10 percentage points of B2 or higher.", options: {} }], { x: 6.65, y: 3.4, w: 5.8, h: 1.55, fontSize: 14.5 });
  T(s, [{ text: "H0  ", options: { bold: true, color: CORAL } }, { text: "Otherwise.", options: {} }], { x: 6.65, y: 4.95, w: 5.8, h: 0.35, fontSize: 14.5 });
  T(s, "Frozen with hashes on 2026-11-24 (01:55 UTC) before any test run. m = 10 pp is team-set; instructor confirmation pending.", { x: 6.65, y: 5.4, w: 5.8, h: 0.95, fontSize: 12.5, italic: true, color: SLATE });
}

// ============ 9 ARCHITECTURE ============
section("System and method");
{
  const s = content("System architecture as implemented",
    "This is the system as built, not a plan. The top row is offline preparation: the open textbook is parsed with provenance, chunked at section boundaries into 1,242 passages, and indexed with BM25 and BGE embeddings. The bottom row is online: hybrid retrieval with reciprocal-rank fusion and a cross-encoder rerank, then a trained sufficiency gate, grounded generation by Qwen3-4B with bracketed citations, claim-level verification with MiniCheck and an NLI model, and a fusion step that outputs a typed decision. Fail-closed: any component error leads to abstention. Colours encode function; the legend sits below.");
  const colr = { corpus: SLATE, retr: TEAL, dl: BLUE, ver: AMBER, dec: CORAL, ui: GREEN };
  const top = [
    ["Approved course documents", "Dive into Deep Learning, 10 chapters", colr.corpus],
    ["Parse + chunk", "section-aware, provenance span per chunk (1,242)", colr.corpus],
    ["Dual index", "BM25 + BGE-base embeddings in FAISS", colr.retr],
  ];
  const bw = 1.62, gap = 0.27;
  top.forEach((b, i) => {
    const x = 0.6 + i * (bw * 1.35 + 0.3), w = bw * 1.35;
    box(s, x, 1.55, w, 1.25, b[2]);
    T(s, [{ text: b[0], options: { bold: true, fontSize: 15, breakLine: true } }, { text: b[1], options: { fontSize: 12.5 } }], { x: x + 0.1, y: 1.55, w: w - 0.2, h: 1.25, color: "FFFFFF", valign: "middle", align: "center" });
    if (i < 2) arrow(s, x + w, 2.17, x + w + 0.3, 2.17);
  });
  T(s, "OFFLINE", { x: 9.3, y: 1.5, w: 2, h: 0.3, fontSize: 11, bold: true, color: SLATE });
  const bot = [
    ["Student question", "English text input", colr.ui],
    ["Hybrid retrieve + rerank", "BM25 + dense, RRF; cross-encoder, top 5", colr.retr],
    ["Sufficiency gate", "DeBERTa-v3-base trained on SQuAD 2.0 + hard negatives", colr.dl],
    ["Grounded generation", "Qwen3-4B, prompt with [C#] citations", colr.dl],
    ["Claim verification", "MiniCheck-FT5 + NLI per cited sentence", colr.ver],
    ["Fusion + decision", "logistic regression, threshold τ, typed state", colr.dec],
    ["Output", "cited answer or abstain + related sections", colr.ui],
  ];
  const w2 = 1.55, g2 = 0.2;
  bot.forEach((b, i) => {
    const x = 0.6 + i * (w2 + g2);
    box(s, x, 3.75, w2, 2.0, b[2]);
    T(s, [{ text: b[0], options: { bold: true, fontSize: 14, breakLine: true } }, { text: b[1], options: { fontSize: 12 } }], { x: x + 0.06, y: 3.75, w: w2 - 0.12, h: 2.0, color: "FFFFFF", valign: "middle", align: "center" });
    if (i < 6) arrow(s, x + w2, 4.75, x + w2 + g2, 4.75);
  });
  T(s, "ONLINE", { x: 0.6, y: 3.4, w: 2, h: 0.3, fontSize: 11, bold: true, color: SLATE });
  // elbow: Dual index bottom -> retrieval top
  const idxX = 0.6 + 2 * (bw * 1.35 + 0.3) + (bw * 1.35) / 2; // centre of index box
  const retX = 0.6 + 1 * (w2 + g2) + w2 / 2;
  seg(s, idxX, 2.8, idxX, 3.3); seg(s, idxX, 3.3, retX, 3.3); arrow(s, retX, 3.3, retX, 3.75);
  // legend
  const lg = [["Corpus", colr.corpus], ["Retrieval", colr.retr], ["Deep learning model", colr.dl], ["Verification", colr.ver], ["Decision logic", colr.dec], ["Interface", colr.ui]];
  lg.forEach((l, i) => {
    const x = 0.6 + i * 2.05;
    box(s, x, 6.0, 0.28, 0.28, l[1], { rectRadius: 0.04 });
    T(s, l[0], { x: x + 0.38, y: 5.97, w: 1.6, h: 0.34, fontSize: 12.5, valign: "middle" });
  });
  T(s, "Fail-closed: any component error produces an abstention. All citations resolve to stored passages with section path.", { x: 0.6, y: 6.5, w: 12.1, h: 0.35, fontSize: 13, italic: true, color: SLATE });
}

// ============ 10 TECHNOLOGY ============
{
  const s = content("Technology selection: pinned models per responsibility",
    "These are final choices as implemented, with pinned revisions recorded in the repository. Note what was evaluated but not adopted in the research reports: LettuceDetect is used only as an optional secondary evaluator and not as a decision component; MiniCheck is a decision component and is never used to evaluate itself. The generator fits on a free T4 in fp16 (8.1 GB peak measured in the smoke test); NF4 halves that. Selection rationale is cost, licence, and fit to a free T4.");
  const rows = [
    ["Document processing", "Markdown source of the open textbook, section-aware chunker", "Provenance span and heading path per chunk"],
    ["Embedding", "BAAI bge-base-en-v1.5 [23]", "Open licence; strong small embedder; FAISS flat inner product"],
    ["Hybrid retrieval", "BM25 + dense, reciprocal rank fusion k=60 [17]", "Lexical and semantic evidence complement each other"],
    ["Reranker", "ms-marco-MiniLM-L6-v2 cross-encoder, top 5", "Cheap precision gain; also the B2 baseline signal"],
    ["Generator", "Qwen3-4B-Instruct-2507 [22], fp16, greedy", "Fits free T4; deterministic, reproducible runs"],
    ["Sufficiency gate", "DeBERTa-v3-base [20] fine-tuned on SQuAD 2.0 + BM25 hard negatives", "Small trained answerability model, not a prompt"],
    ["Claim verification", "MiniCheck-Flan-T5-Large [3] + DeBERTa NLI", "Per-sentence support and contradiction features"],
    ["Fusion + threshold", "Logistic regression over 9 features; τ by utility on SQuAD calibration", "Calibrated on held-out data, no Platt in this profile"],
  ];
  const hdr = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, fontSize: 13, fontFace: "Calibri" } });
  const body = rows.map((r, i) => r.map((t, j) => ({ text: t, options: { fontSize: 12.5, fontFace: "Calibri", color: NAVY, bold: j === 0, valign: "middle", fill: { color: i % 2 ? "FFFFFF" : PALE } } })));
  s.addTable([[hdr("Responsibility"), hdr("Selected component"), hdr("Why")], ...body], { x: 0.6, y: 1.5, w: 12.1, colW: [2.4, 5.2, 4.5], rowH: [0.38, ...rows.map(() => 0.58)], border: { type: "solid", color: "D5DEE6", pt: 0.75 }, margin: [0.03, 0.1, 0.03, 0.1] });
  src(s, "Measured on a Colab T4 smoke test: generator fp16 peak 8.13 GB (NF4 4.03 GB), MiniCheck 3.30 GB. Model revisions pinned in the pre-registration.");
}

// ============ 11 VERIFICATION & ABSTENTION ============
{
  const s = content("Beyond RAG: when should the tutor answer?",
    "The policy has four typed outcomes. Sufficient evidence: answer with citations. Partial: answer only what is supported and say what is not covered. Insufficient: abstain and show nearby sections labelled related, not supporting. Contradictory: disclose the conflict. Be honest that in the frozen test run the contradiction state was disabled, because we built no development items for it; so the result slides cover three effective outcomes. The decision is a logistic fusion of gate, retrieval, and verifier features with a threshold chosen on SQuAD calibration data, and no probability is shown unless calibrated.");
  const flow = ["Question", "Retrieved evidence", "Sufficiency gate", "Grounded generation", "Claim verification", "Calibrated decision"];
  flow.forEach((f, i) => {
    const x = 0.6 + i * 2.05;
    box(s, x, 1.55, 1.8, 0.8, i === 5 ? CORAL : NAVY);
    T(s, f, { x, y: 1.55, w: 1.8, h: 0.8, fontSize: 14, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
    if (i < 5) arrow(s, x + 1.8, 1.95, x + 2.05, 1.95);
  });
  const out = [
    ["Sufficient", "Answer with sentence-level citations", GREEN, "All cited claims supported"],
    ["Partial", "Answer the supported part; state what the course does not cover", AMBER, "Some claims unsupported"],
    ["Insufficient", "Abstain; show nearest sections as “related, not supporting”", CORAL, "Gate and verifier find no support"],
    ["Contradictory", "Disclose the conflict, or abstain", SLATE, "Disabled in the frozen test run (no dev items built)"],
  ];
  out.forEach((o, i) => {
    const x = 0.6 + i * 3.08;
    box(s, x, 2.85, 2.9, 3.3, PALE);
    box(s, x, 2.85, 2.9, 0.55, o[2]);
    T(s, o[0], { x, y: 2.85, w: 2.9, h: 0.55, fontFace: "Cambria", fontSize: 17, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
    T(s, o[1], { x: x + 0.2, y: 3.55, w: 2.5, h: 1.45, fontSize: 16 });
    T(s, [{ text: "Trigger  ", options: { bold: true, color: SLATE } }, { text: o[3], options: {} }], { x: x + 0.2, y: 5.05, w: 2.5, h: 1.0, fontSize: 13.5 });
  });
  src(s, "Gate: trained sufficiency classifier [1][11][20]. Verifier: MiniCheck [3]. No probabilities are displayed unless calibrated on held-out data [19].");
}

// ============ 12 DATASETS ============
section("Data and evaluation");
{
  const s = content("Dataset strategy: article-level splits, locked course set",
    "Three data roles. SQuAD 2.0 trains the gate and calibrates thresholds: it is split by article, so no article appears in two partitions. The course corpus is the open textbook Dive into Deep Learning, 1,242 passages from 10 chapters, provisional pending faculty approval. The course evaluation set has 57 questions; the out-of-syllabus ones come from chapters that were deliberately not indexed. The items were drafted by an AI assistant from the corpus text and then accepted, edited or rejected by both members; this is disclosed. Be upfront that the second blind labelling failed and was not repeated, so we report no inter-annotator agreement.");
  // splits visual
  T(s, "SQuAD 2.0: split by article (no article crosses partitions)", { x: 0.6, y: 1.45, w: 6, h: 0.35, fontFace: "Cambria", fontSize: 15, bold: true, color: TEAL });
  const sp = [["Gate train", "420 articles", 3.05, TEAL], ["Gate dev", "22", 0.95, BLUE], ["Calibration", "12", 0.95, AMBER], ["Test", "23", 0.95, CORAL]];
  let xx = 0.6;
  sp.forEach(([n, v, w, c]) => {
    box(s, xx, 1.85, w - 0.06, 0.95, c);
    T(s, [{ text: n, options: { bold: true, fontSize: 12.5, breakLine: true } }, { text: v, options: { fontSize: 12 } }], { x: xx, y: 1.85, w: w - 0.06, h: 0.95, color: "FFFFFF", align: "center", valign: "middle" });
    xx += w;
  });
  T(s, [
    { text: "Gate train: 24,000 pairs (40% positive, 30% SQuAD no-answer, 30% BM25 hard negatives)", options: { bullet: true, breakLine: true } },
    { text: "Calibration: thresholds and fusion weights fitted here only", options: { bullet: true, breakLine: true } },
    { text: "Test: SQuAD-RAG run was not completed", options: { bullet: true } },
  ], { x: 0.6, y: 2.95, w: 6.1, h: 1.35, fontSize: 13.5, paraSpaceAfter: 3 });
  box(s, 0.6, 4.45, 6.1, 2.1, PALE);
  T(s, "Leakage controls", { x: 0.8, y: 4.52, w: 5.7, h: 0.3, fontFace: "Cambria", fontSize: 15, bold: true, color: TEAL });
  T(s, ["Article-level split; gate-train and test articles disjoint", "Thresholds fitted on SQuAD calibration only, never on course items", "Course set frozen with sha256 before test runs; analysis code pinned", "Withheld-evidence stress removes the gold passage from the index"].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1 } })),
    { x: 0.8, y: 4.85, w: 5.75, h: 1.65, fontSize: 13, paraSpaceAfter: 3 });
  // course items chart
  T(s, "Course evaluation set: 57 questions, all locked as test", { x: 7.1, y: 1.45, w: 5.6, h: 0.35, fontFace: "Cambria", fontSize: 15, bold: true, color: TEAL });
  s.addChart(pres.charts.BAR, [{ name: "Items", labels: ["A1 single-section", "A2 multi-section", "P partially covered", "U1 missing detail", "U2 out-of-syllabus"], values: [25, 4, 7, 11, 10] }], {
    x: 7.0, y: 1.85, w: 5.7, h: 3.1, barDir: "bar", chartColors: [TEAL, TEAL, AMBER, CORAL, CORAL], showTitle: false, showLegend: false, showValue: true, dataLabelPosition: "outEnd",
    dataLabelFontSize: 12, dataLabelColor: NAVY, dataLabelFontFace: "+mn-lt", catAxisLabelColor: NAVY, catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, catAxisOrientation: "maxMin", valAxisMaxVal: 30,
  });
  T(s, [
    { text: "36 answerable (A1, A2, P) and 21 not answerable from the indexed text (U1, U2)", options: { bullet: true, breakLine: true } },
    { text: "Corpus: Dive into Deep Learning [21], 10 chapters, 1,242 passages; provisional, pending faculty approval", options: { bullet: true, breakLine: true } },
    { text: "AI-drafted, then accepted by both members (57 of 57); the blind second labelling was invalid and not repeated", options: { bullet: true } },
  ], { x: 7.1, y: 5.0, w: 5.6, h: 1.65, fontSize: 13, paraSpaceAfter: 3 });
}

// ============ 13 BASELINES ============
{
  const s = content("Experimental comparison: two baselines, one gate, four ablations",
    "Handbook task 2 asks for two justified baselines. B1 is the small-LLM route: the same generator is allowed to say INSUFFICIENT_EVIDENCE by instruction only. B2 is the sentence-transformer route: the same retrieval and reranking, with a threshold on the cross-encoder score tuned on SQuAD calibration data. G adds the trained gate, the verifier features and the calibrated fusion. All systems share the same retrieved passages and generator, so the comparison isolates the abstention mechanism. Ablations remove one component at a time and are descriptive.");
  const sys = [
    ["B1", "Prompt-only abstention", "Same retrieval and generator; the model may emit INSUFFICIENT_EVIDENCE", SLATE],
    ["B2", "Reranker-score threshold", "Same retrieval; answer only if cross-encoder score ≥ τ (tuned on SQuAD calibration)", BLUE],
    ["G", "Proposed: fused gate", "Trained sufficiency gate + claim verifier + calibrated logistic fusion", TEAL],
  ];
  sys.forEach((r, i) => {
    const y = 1.55 + i * 1.12;
    box(s, 0.6, y, 7.0, 1.0, PALE);
    box(s, 0.6, y, 0.85, 1.0, r[3]);
    T(s, r[0], { x: 0.6, y, w: 0.85, h: 1.0, fontFace: "Cambria", fontSize: 24, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
    T(s, [{ text: r[1], options: { bold: true, fontSize: 15.5, breakLine: true } }, { text: r[2], options: { fontSize: 13 } }], { x: 1.6, y, w: 5.9, h: 1.0, valign: "middle" });
  });
  T(s, "Ablations of G (descriptive)", { x: 0.6, y: 5.0, w: 7, h: 0.35, fontFace: "Cambria", fontSize: 15, bold: true, color: TEAL });
  const ab = [["A1", "no verifier features"], ["A2", "no gate"], ["A3", "no calibration"], ["A5", "untrained gate"]];
  ab.forEach((a, i) => {
    const x = 0.6 + i * 1.78;
    box(s, x, 5.4, 1.68, 0.95, "DCEFF1");
    T(s, [{ text: a[0], options: { bold: true, fontSize: 16, breakLine: true } }, { text: a[1], options: { fontSize: 12 } }], { x, y: 5.4, w: 1.68, h: 0.95, align: "center", valign: "middle" });
  });
  box(s, 8.0, 1.55, 4.7, 4.8, NAVY);
  T(s, "Fair comparison by design", { x: 8.25, y: 1.7, w: 4.2, h: 0.4, fontFace: "Cambria", fontSize: 17, bold: true, color: "9ED5DC" });
  T(s, ["Identical passages, generator, prompt and greedy decoding for every system", "Only the answer/abstain mechanism differs", "Thresholds fixed from SQuAD calibration before any course test output", "Primary metric AURC; B1 has a single operating point, so it is compared by risk, coverage and utility", "A4 (no hard negatives) planned but not run"].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1 } })),
    { x: 8.25, y: 2.2, w: 4.25, h: 4.0, fontSize: 14, color: "FFFFFF", paraSpaceAfter: 6 });
}

// ============ 14 EVALUATION FRAMEWORK ============
{
  const s = content("Evaluation framework and stress conditions",
    "Left: the four measurement dimensions. Right: the stress matrix with its true status. Only S1, withheld evidence, was run: the gold passage is removed from the index so that every answerable question becomes unsupported, and any answer is then an unsupported answer. S2 to S4 were not run in the time available. Error is defined strictly: a partially correct answer counts as an error in the primary analysis, with a lenient sensitivity analysis alongside. Judges labelled outputs blind to the system.");
  const dims = [
    ["Retrieval", "Recall@5, MRR", TEAL],
    ["Grounding", "Human verdict per answer: correct and supported, partial, incorrect, unsupported", BLUE],
    ["Abstention", "AURC (primary), risk at coverage, unsupported-answer rate, false-abstention cost, utility U(λ=2), ECE", AMBER],
    ["Efficiency", "Peak VRAM and latency (smoke test); gate training time not measured", SLATE],
  ];
  dims.forEach((d, i) => {
    const y = 1.5 + i * 1.2;
    box(s, 0.6, y, 6.0, 1.08, PALE);
    box(s, 0.6, y, 1.6, 1.08, d[2]);
    T(s, d[0], { x: 0.6, y, w: 1.6, h: 1.08, fontFace: "Cambria", fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
    T(s, d[1], { x: 2.35, y, w: 4.15, h: 1.08, fontSize: 13, valign: "middle" });
  });
  const hdr = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, fontSize: 13, fontFace: "Calibri" } });
  const st = [["S1", "Gold passages withheld", "Run", GREEN], ["S2", "Irrelevant or misleading passages", "Not run", CORAL], ["S3", "Edited fact in a passage", "Not run", CORAL], ["S4", "Conflicting sources", "Not run", CORAL]];
  const rows = st.map((r, i) => [
    { text: r[0], options: { bold: true, fontSize: 13, fontFace: "Calibri", color: NAVY, fill: { color: i % 2 ? "FFFFFF" : PALE } } },
    { text: r[1], options: { fontSize: 13, fontFace: "Calibri", color: NAVY, fill: { color: i % 2 ? "FFFFFF" : PALE } } },
    { text: r[2], options: { fontSize: 13, bold: true, fontFace: "Calibri", color: r[3], fill: { color: i % 2 ? "FFFFFF" : PALE } } }]);
  s.addTable([[hdr("ID"), hdr("Stress condition"), hdr("Status")], ...rows], { x: 6.95, y: 1.5, w: 5.75, colW: [0.7, 3.7, 1.35], rowH: [0.4, 0.5, 0.5, 0.5, 0.5], border: { type: "solid", color: "D5DEE6", pt: 0.75 } });
  box(s, 6.95, 4.15, 5.75, 2.35, NAVY);
  T(s, "Labelling and statistics", { x: 7.15, y: 4.25, w: 5.4, h: 0.35, fontFace: "Cambria", fontSize: 15, bold: true, color: "9ED5DC" });
  T(s, ["Strict error: partially correct counts as an error (registered); lenient as sensitivity", "One blind judge per output (the member who did not author the item)", "10,000-resample paired bootstrap, seed 2026; Clopper–Pearson intervals are descriptive only"].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1 } })),
    { x: 7.15, y: 4.65, w: 5.4, h: 1.8, fontSize: 12.5, color: "FFFFFF", paraSpaceAfter: 3 });
}

// ============ 15 STATUS ============
section("Progress and results");
{
  const s = content("Implementation status: complete, partial, outstanding",
    "This is the honest status slide. Complete: the full pipeline runs end to end on a free T4; the gate trained to a gate-development AUROC of 0.954; hybrid retrieval with reranking reaches Recall@5 of 0.988 on SQuAD calibration; the test items were frozen and the pre-registration committed before any test output; 75 outputs were judged. Partial: the demo app is built but the recorded demo is pending; the instructor has not confirmed corpus approval or the coverage tolerance. Outstanding: the SQuAD test run, stress conditions S2 to S4, ablation A4, double judging, and a valid inter-annotator agreement.");
  const cols = [
    ["Complete", GREEN, [
      "Ingestion, chunking, provenance (1,242 passages)",
      "Hybrid retrieval + rerank; Recall@5 0.988 (SQuAD cal.)",
      "Generator, citation validator, typed policy",
      "Gate trained: gate-dev AUROC 0.954",
      "Verifier, fusion, thresholds fixed on SQuAD cal.",
      "57 items verified; pre-registration frozen",
      "Course-test clean + S1 run; 75 outputs judged",
      "Registered analysis and sensitivity analysis"]],
    ["Partial", AMBER, [
      "Streamlit demo built; recorded walk-through pending",
      "Corpus approval and tolerance m: instructor confirmation pending",
      "Contradiction state implemented but disabled in the frozen run",
      "Deliverables A, B, H and the paper: drafted, names and dates to fill"]],
    ["Not done", CORAL, [
      "SQuAD-test run",
      "Stress S2, S3, S4; ablation A4",
      "Double judging; valid second-label agreement",
      "Gate training wall-clock (log invalid)",
      "Larger course set (target was 150+)"]],
  ];
  const wd = [4.65, 3.65, 3.5], xs = [0.6, 5.4, 9.2];
  cols.forEach((c, i) => {
    box(s, xs[i], 1.5, wd[i], 0.5, c[1]);
    T(s, c[0], { x: xs[i], y: 1.5, w: wd[i], h: 0.5, fontFace: "Cambria", fontSize: 17, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
    box(s, xs[i], 2.05, wd[i], 4.55, PALE);
    T(s, c[2].map((t, j, a) => ({ text: t, options: { bullet: true, breakLine: j < a.length - 1 } })), { x: xs[i] + 0.2, y: 2.2, w: wd[i] - 0.4, h: 4.3, fontSize: 15, paraSpaceAfter: 7 });
  });
}

// ============ 16 RESULTS H1 ============
{
  const s = content("Preliminary result: H1 is not supported on 57 questions",
    "Lead with the verdict. The registered test of H1 gives a difference in AURC of plus 0.079 with a confidence interval from minus 0.002 to plus 0.181: not entirely below zero, so H1 is not supported; the coverage condition is met. Explain why B2's AURC is low: it answers two questions in total, so its risk is almost vacuous. The more useful reading is the table: G and B1 both abstain on 20 of 21 out-of-syllabus questions; G answers fewer questions than B1 and makes fewer judged errors, but loses utility because it refuses 42 percent of answerable questions that were answered correctly. Caveat strongly: with 0 to 5 errors per system, small differences are one or two items. Lenient sensitivity analysis gives the same verdict.");
  box(s, 0.6, 1.5, 3.5, 2.3, NAVY);
  T(s, [{ text: "H1 not supported", options: { bold: true, fontSize: 20, breakLine: true, color: "FFFFFF", fontFace: "Cambria" } }, { text: "ΔAURC (G − B2) = +0.079", options: { fontSize: 15, breakLine: true, color: "9ED5DC" } }, { text: "95% CI [−0.002, 0.181]", options: { fontSize: 15, breakLine: true, color: "9ED5DC" } }, { text: "Coverage condition met (55.6% vs 5.6%)", options: { fontSize: 12.5, color: "D6E2EC" } }], { x: 0.8, y: 1.5, w: 3.2, h: 2.3, valign: "middle", paraSpaceAfter: 3 });
  const hdr = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, fontSize: 12.5, fontFace: "Calibri", align: "center" } });
  const c = (t, o) => ({ text: t, options: Object.assign({ fontSize: 13, fontFace: "Calibri", color: NAVY, align: "center", valign: "middle" }, o || {}) });
  const data = [
    ["B1 prompt-only", "37", "5 (0.135)", "1 / 21", "0.00", "0.386"],
    ["B2 CE threshold", "2", "0 (0.000)", "0 / 21", "0.94", "0.035"],
    ["G fused gate", "21", "2 (0.095)", "1 / 21", "0.42", "0.263"],
  ].map((r, i) => r.map((t, j) => c(t, { bold: j === 0 || (i === 2), align: j === 0 ? "left" : "center", fill: { color: i === 2 ? "DCEFF1" : (i % 2 ? PALE : "FFFFFF") } })));
  s.addTable([[hdr("System"), hdr("Answered of 57"), hdr("Errors (risk)"), hdr("Out-of-syllabus answered"), hdr("Refused correct (FAC)"), hdr("Utility λ=2")], ...data], { x: 4.35, y: 1.5, w: 8.35, colW: [1.75, 1.15, 1.35, 1.5, 1.4, 1.2], rowH: [0.7, 0.38, 0.38, 0.38], border: { type: "solid", color: "D5DEE6", pt: 0.75 }, margin: [0.03, 0.06, 0.03, 0.06] });
  T(s, "Strict error definition (primary). Lenient sensitivity: G risk 0.048 vs B1 0.027; ΔAURC +0.069, CI [0.000, 0.169]; same verdict.", { x: 4.35, y: 3.5, w: 8.35, h: 0.5, fontSize: 12, italic: true, color: SLATE });
  s.addChart(pres.charts.BAR, [
    { name: "Answered (of 57)", labels: ["B1", "B2", "G"], values: [37, 2, 21] },
    { name: "Judged errors among answered", labels: ["B1", "B2", "G"], values: [5, 0, 2] },
  ], { x: 0.6, y: 4.05, w: 6.0, h: 2.6, barDir: "col", barGrouping: "clustered", chartColors: [TEAL, CORAL], showTitle: false, showLegend: true, legendPos: "b", legendFontSize: 12, legendColor: NAVY, legendFontFace: "+mn-lt",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: NAVY, dataLabelFontFace: "+mn-lt", catAxisLabelColor: NAVY, catAxisLabelFontSize: 13, catAxisLabelFontFace: "+mn-lt", valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, valAxisMaxVal: 45 });
  box(s, 6.95, 4.1, 5.75, 2.5, PALE);
  T(s, "How to read this", { x: 7.15, y: 4.15, w: 5.4, h: 0.35, fontFace: "Cambria", fontSize: 15, bold: true, color: TEAL });
  T(s, ["G and B1 both abstain on 20 of 21 out-of-syllabus questions", "G answers fewer questions and makes fewer errors, but refuses 42% of answerable questions it could have answered correctly", "B2's low AURC comes from answering only two questions", "With 0–5 errors per system, differences are one or two items: no ranking is claimed"].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1 } })),
    { x: 7.15, y: 4.5, w: 5.4, h: 2.05, fontSize: 12.5, paraSpaceAfter: 3 });
  src(s, "Source: results/runs/course-test__clean/analysis.json (strict) and analysis_lenient.json. Preliminary, 57 items, one judge per output.");
}

// ============ 17 STRESS + ABLATION ============
{
  const s = content("Stress test S1 and ablations",
    "S1 withholds the gold passages, so every answer to an answerable question is unsupported by construction. Under S1 the prompt-only baseline still answers 56 percent of questions, 32 of 57, all unsupported; G answers about 10 percent, 6 questions; the threshold baseline answers none. That is the one condition where G clearly beats B1, but it is one stress condition on 57 items. The ablation table is descriptive: removing the verifier features (A1) gives a lower AURC and no errors at the price of more refusals; removing calibration (A3) raises coverage and doubles unsupported answers. Each difference is one or two items, so we do not rank components.");
  s.addChart(pres.charts.BAR, [
    { name: "B1 prompt-only", labels: ["Clean", "S1: gold withheld"], values: [64.9, 56.1] },
    { name: "B2 CE threshold", labels: ["Clean", "S1: gold withheld"], values: [3.5, 0.0] },
    { name: "G fused gate", labels: ["Clean", "S1: gold withheld"], values: [36.8, 10.5] },
  ], { x: 0.6, y: 1.5, w: 5.9, h: 4.0, barDir: "col", barGrouping: "clustered", chartColors: [SLATE, BLUE, TEAL], showTitle: true, title: "Answer rate (% of 57 questions)", titleFontSize: 14, titleColor: NAVY, titleFontFace: "+mn-lt", showLegend: true, legendPos: "b", legendFontSize: 12, legendColor: NAVY, legendFontFace: "+mn-lt",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: NAVY, dataLabelFontFace: "+mn-lt", dataLabelFormatCode: "0.0", catAxisLabelColor: NAVY, catAxisLabelFontSize: 13, catAxisLabelFontFace: "+mn-lt", valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, valAxisMaxVal: 80 });
  T(s, "Under S1 every answer is unsupported: B1 gave 32 unsupported answers, G gave 6, B2 gave none.", { x: 0.6, y: 5.6, w: 5.9, h: 0.9, fontSize: 14, bold: true, color: NAVY });
  const hdr = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, fontSize: 12.5, fontFace: "Calibri", align: "center" } });
  const ab = [["G (full)", "21", "0.095", "1", "0.42", "0.141"], ["A1 no verifier", "12", "0.000", "0", "0.64", "0.086"], ["A2 no gate", "16", "0.125", "1", "0.58", "0.158"], ["A3 no calibration", "34", "0.147", "2", "0.12", "0.125"], ["A5 untrained gate", "18", "0.111", "1", "0.52", "0.091"]]
    .map((r, i) => r.map((t, j) => ({ text: t, options: { fontSize: 12.5, fontFace: "Calibri", color: NAVY, bold: i === 0 || j === 0, align: j === 0 ? "left" : "center", valign: "middle", fill: { color: i === 0 ? "DCEFF1" : (i % 2 ? "FFFFFF" : PALE) } } })));
  T(s, "Ablations on clean course test (strict, descriptive)", { x: 6.85, y: 1.5, w: 5.85, h: 0.35, fontFace: "Cambria", fontSize: 15, bold: true, color: TEAL });
  s.addTable([[hdr("Variant"), hdr("Answered"), hdr("Risk"), hdr("Out-of-syl. answered"), hdr("FAC"), hdr("AURC")], ...ab], { x: 6.85, y: 1.9, w: 5.85, colW: [1.55, 1.0, 0.7, 0.95, 0.7, 0.95], rowH: [0.62, 0.42, 0.42, 0.42, 0.42, 0.42], border: { type: "solid", color: "D5DEE6", pt: 0.75 }, margin: [0.03, 0.06, 0.03, 0.06] });
  box(s, 6.85, 4.85, 5.85, 1.7, PALE);
  T(s, ["Removing the verifier features (A1) did not hurt here: the verifier is not shown to help on this set", "Removing calibration (A3) raised coverage and doubled out-of-syllabus answers", "Differences amount to one or two items; no component ranking is claimed"].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1 } })),
    { x: 7.05, y: 4.95, w: 5.5, h: 1.55, fontSize: 12.5, paraSpaceAfter: 3 });
  src(s, "Source: results/runs/course-test__clean/analysis.json and course-test__S1/analysis.json. AURC is uninformative under S1 (identical 0.910 for all systems), so answer counts are reported.");
}

// ============ 18 ERROR ANALYSIS ============
{
  const s = content("Failure cases: seven judged errors, four questions",
    "Seven outputs were judged partially correct, all by one judge, covering four questions. Case 1: the warmup answer is correct at the core but adds claims about initialisation that the passages do not contain. Case 2: for a partially covered question about multi-head attention, the answer states a head count the course does not give; the course's own demo model differs from the original paper. Case 3: for max pooling versus average pooling, both systems flagged that a number was missing but added an unsupported claim. Case 4: a padding computation for a 5 by 3 kernel gave the wrong width padding in the prompt-only output only. We have not yet classified retrieval misses or false abstentions per item; that is future work.");
  const cases = [
    ["Learning-rate warmup", "Core is right; adds claims on initialisation and depth that the passages do not state", "Both systems", AMBER],
    ["Original Transformer head count", "Partially covered question: states a number the course does not give instead of saying the rest is not covered", "Both systems", CORAL],
    ["Max vs average pooling", "Flags the missing figure, then adds an unsupported claim about object recognition", "Both systems", AMBER],
    ["Padding for a 5×3 kernel", "Width padding computed wrongly", "B1 only; G's answer was judged correct", CORAL],
  ];
  cases.forEach((c, i) => {
    const x = 0.6 + (i % 2) * 6.1, y = 1.5 + Math.floor(i / 2) * 2.0;
    box(s, x, y, 5.95, 1.85, PALE);
    tag(s, "CASE " + (i + 1), x + 0.2, y + 0.15, 0.95, c[3]);
    T(s, c[0], { x: x + 1.3, y: y + 0.12, w: 4.5, h: 0.4, fontFace: "Cambria", fontSize: 16, bold: true });
    T(s, c[1], { x: x + 0.2, y: y + 0.65, w: 5.55, h: 0.75, fontSize: 14 });
    T(s, [{ text: "Affected: ", options: { bold: true, color: SLATE } }, { text: c[2], options: {} }], { x: x + 0.2, y: y + 1.42, w: 5.55, h: 0.35, fontSize: 12.5 });
  });
  box(s, 0.6, 5.6, 12.1, 0.95, NAVY);
  T(s, [{ text: "Takeaway: ", options: { bold: true, color: "9ED5DC" } }, { text: "the errors are plausible additions to a correct core, the case a claim-level verifier should catch. We did not analyse retrieval misses or the 14 correct answers G refused; a per-system error taxonomy is future work.", options: { color: "FFFFFF" } }], { x: 0.85, y: 5.6, w: 11.6, h: 0.95, fontSize: 14, valign: "middle" });
}

// ============ 19 LIMITATIONS & DISCLOSURE ============
{
  const s = content("Limitations and transparency",
    "Be direct with the examiner. The judging has a structural weakness: each output was judged by the member who did not write the item, and the two judges differ in strictness, so judge and item author are confounded. The judges saw an AI-suggested verdict which they could accept or override; 66 of 72 suggestions were accepted, 6 overridden; that is disclosed and the judge's choice is final. The first blind second labelling was invalid and not repeated, so there is no agreement statistic. The pre-registration was regenerated once after an interrupted run; only a helper script changed between the two commits. Gate training time was not measured. The AI assistant helped write the code, the specification and drafted the course items; no experimental number was produced by it.");
  box(s, 0.6, 1.5, 5.95, 5.05, PALE);
  T(s, "Scientific limitations", { x: 0.85, y: 1.6, w: 5.5, h: 0.4, fontFace: "Cambria", fontSize: 17, bold: true, color: CORAL });
  T(s, ["57 course items; only 0–5 judged errors per system, so confidence intervals are wide", "One textbook, English; corpus approval pending", "Thresholds fitted on SQuAD only and applied to course text with no domain adaptation", "One judge per output; judge strictness confounded with item author (judge A: 0 of 38 partial; judge B: 7 of 37)", "No formal selective-risk guarantee; calibration and test data are not exchangeable", "S2–S4, A4 and the SQuAD test run were not completed"].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1 } })),
    { x: 0.85, y: 2.05, w: 5.5, h: 4.4, fontSize: 15, paraSpaceAfter: 6 });
  box(s, 6.75, 1.5, 5.95, 5.05, PALE);
  T(s, "Process disclosure", { x: 7.0, y: 1.6, w: 5.5, h: 0.4, fontFace: "Cambria", fontSize: 17, bold: true, color: TEAL });
  T(s, ["Generative AI assistant (Claude Code) helped write the specification, code and tests, and drafted the 57 course items; both members verified every item", "Judging used AI-suggested verdicts (66 accepted, 6 overridden by the judges); the judge's choice is recorded", "First blind second-labelling was invalid (all “sufficient”, κ = 0) and not repeated: no agreement reported", "Pre-registration regenerated once after an interrupted run; only a helper script differed", "Gate training time was not measured (log overwritten)", "No experimental number was produced by the assistant: all come from logged runs"].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1 } })),
    { x: 7.0, y: 2.05, w: 5.5, h: 4.4, fontSize: 15, paraSpaceAfter: 6 });
}

// ============ 20 CONCLUSION ============
section("Conclusion");
{
  const s = pres.addSlide({ masterName: "LM_DARK", sectionTitle: "Conclusion" });
  T(s, "Conclusion and next steps", { x: 0.7, y: 0.5, w: 12, h: 0.8, fontFace: "Cambria", fontSize: 34, bold: true, color: "FFFFFF" });
  T(s, [
    { text: "The full pipeline is built and runs on a free T4: hybrid retrieval, a trained sufficiency gate, claim-level verification and typed abstention.", options: { bullet: true, breakLine: true } },
    { text: "On the registered test, H1 is not supported: the gate did not beat a tuned reranker threshold on AURC, and did not improve out-of-syllabus abstention over a prompt-only baseline (both abstain on 20 of 21).", options: { bullet: true, breakLine: true } },
    { text: "Its measurable benefit is robustness when evidence is withheld (S1: 6 unsupported answers vs 32), paid for with refusals of answerable questions (FAC 0.42).", options: { bullet: true, breakLine: true } },
    { text: "With 0–5 judged errors per system the study cannot separate the components: it is a preliminary, honestly reported result.", options: { bullet: true } },
  ], { x: 0.7, y: 1.5, w: 7.2, h: 4.6, fontSize: 17, color: "FFFFFF", paraSpaceAfter: 10 });
  box(s, 8.3, 1.5, 4.4, 4.9, "1B3A57");
  T(s, "Next steps", { x: 8.55, y: 1.6, w: 4, h: 0.4, fontFace: "Cambria", fontSize: 18, bold: true, color: "9ED5DC" });
  T(s, ["Record the demo video (answer, abstention, B1 vs G, a failure)", "Fill names, dates and the contribution statement", "Confirm corpus approval and tolerance m with the instructor", "If time allows: SQuAD-test run, S2–S4, larger independently labelled course set, per-system error taxonomy"].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1 } })),
    { x: 8.55, y: 2.1, w: 3.95, h: 4.2, fontSize: 14.5, color: "FFFFFF", paraSpaceAfter: 8 });
  s.addNotes("Close with the synthesis: what we built, what the registered test showed, and what it cannot show. Do not present S1 as a general victory; it is one stress condition. Invite questions on judging, the null result, and the next steps. Presenters should be ready for: why is B2 so conservative (its threshold was fitted on SQuAD and transfers badly to course text), why is the verifier not shown to help (almost no errors to catch), and how reproducible the run is (pinned revisions, seeds, frozen hashes).");
}

// ============ REFERENCES ============
section("References");
const refs = [
  ["[1]", "N. Joren et al., “Sufficient Context: A New Lens on Retrieval Augmented Generation Systems,” ICLR 2025. arXiv:2411.06037.", "PV"],
  ["[2]", "M. Song et al., “Measuring and Enhancing Trustworthiness of LLMs in RAG through Grounded Attributions and Learning to Refuse” (Trust-Align), ICLR 2025. arXiv:2409.11242.", "PV"],
  ["[3]", "L. Tang, P. Laban, G. Durrett, “MiniCheck: Efficient Fact-Checking of LLMs on Grounding Documents,” EMNLP 2024. doi:10.18653/v1/2024.emnlp-main.499.", "V"],
  ["[4]", "C. Niu et al., “RAGTruth: A Hallucination Corpus for Developing Trustworthy RAG,” ACL 2024. doi:10.18653/v1/2024.acl-long.585.", "PV"],
  ["[5]", "Á. Kovács, G. Recski, “LettuceDetect: A Hallucination Detection Framework for RAG Applications,” arXiv:2502.17125, 2025.", "V (model card)"],
  ["[6]", "P. Kirichenko et al., “AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions,” NeurIPS 2025 D&B. arXiv:2506.09038.", "V"],
  ["[7]", "Setiawan, “Prompt-Based Abstention Fails Under Misleading Context,” AACL 2026. arXiv:2608.22228.", "V"],
  ["[8]", "Z. Peng et al., “Unanswerability Evaluation for Retrieval Augmented Generation” (UAEval4RAG), ACL 2025. aclanthology.org/2025.acl-long.415.", "PV"],
  ["[9]", "J. Wallat et al., “Correctness is not Faithfulness in RAG Attributions,” ICTIR 2025. doi:10.1145/3731120.3744592.", "PV"],
  ["[10]", "Yu et al., “Integrating Small Language Models with Retrieval-Augmented Generation in Computing Education,” SIGCSE 2025. doi:10.1145/3641554.3701844.", "PV"],
  ["[11]", "P. Rajpurkar, R. Jia, P. Liang, “Know What You Don’t Know: Unanswerable Questions for SQuAD,” ACL 2018. arXiv:1806.03822.", "V"],
  ["[12]", "T. Gao et al., “Enabling Large Language Models to Generate Text with Citations” (ALCE), EMNLP 2023. doi:10.18653/v1/2023.emnlp-main.398.", "PV"],
];
const refs2 = [
  ["[13]", "A. Kamath, R. Jia, P. Liang, “Selective Question Answering under Domain Shift,” ACL 2020. doi:10.18653/v1/2020.acl-main.503.", "PV"],
  ["[14]", "P. Lewis et al., “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” NeurIPS 2020. arXiv:2005.11401.", "G"],
  ["[15]", "V. Karpukhin et al., “Dense Passage Retrieval for Open-Domain Question Answering,” EMNLP 2020. doi:10.18653/v1/2020.emnlp-main.550.", "G"],
  ["[16]", "N. Reimers, I. Gurevych, “Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks,” EMNLP-IJCNLP 2019. doi:10.18653/v1/D19-1410.", "G"],
  ["[17]", "G. V. Cormack, C. L. A. Clarke, S. Buettcher, “Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods,” SIGIR 2009. doi:10.1145/1571941.1572114.", "G"],
  ["[18]", "Y. Geifman, R. El-Yaniv, “Selective Classification for Deep Neural Networks,” NeurIPS 2017. arXiv:1705.08500.", "G"],
  ["[19]", "C. Guo et al., “On Calibration of Modern Neural Networks,” ICML 2017. arXiv:1706.04599.", "G"],
  ["[20]", "P. He, J. Gao, W. Chen, “DeBERTaV3: Improving DeBERTa using ELECTRA-Style Pre-Training with Gradient-Disentangled Embedding Sharing,” ICLR 2023. arXiv:2111.09543.", "G"],
  ["[21]", "A. Zhang, Z. C. Lipton, M. Li, A. J. Smola, Dive into Deep Learning, Cambridge University Press, 2023. arXiv:2106.11342 (CC BY-SA 4.0 text).", "G"],
  ["[22]", "A. Yang et al., “Qwen3 Technical Report,” arXiv:2505.09388, 2025; model card Qwen/Qwen3-4B-Instruct-2507.", "G"],
  ["[23]", "S. Xiao et al., “C-Pack: Packed Resources For General Chinese Embeddings” (BGE), SIGIR 2024. arXiv:2309.07597; model card BAAI/bge-base-en-v1.5.", "G"],
];
[refs, refs2].forEach((arr, k) => {
  const s = content(k === 0 ? "References (1 of 2)" : "References (2 of 2)", "Verification codes: V = identifier and venue checked against a primary page or model card; PV = paper and venue consistent across sources, specific numbers not re-read; G = standard reference cited from general knowledge, identifier not re-checked online in this session. No number from a PV or G source is quoted in the deck.", "References");
  const rows = arr.map(r => [{ text: r[0], options: { bold: true, fontSize: 13, color: NAVY, fontFace: "Calibri", valign: "top" } }, { text: r[1], options: { fontSize: 13, color: NAVY, fontFace: "Calibri", valign: "top" } }, { text: r[2], options: { fontSize: 12, color: SLATE, fontFace: "Calibri", valign: "top", align: "center" } }]);
  s.addTable([[{ text: "#", options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, fontSize: 12 } }, { text: "Reference", options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, fontSize: 12 } }, { text: "Status", options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, fontSize: 12, align: "center" } }], ...rows],
    { x: 0.6, y: 1.4, w: 12.1, colW: [0.6, 10.4, 1.1], border: { type: "solid", color: "E1E8EE", pt: 0.5 }, margin: [0.03, 0.08, 0.03, 0.08] });
  T(s, "Status: V = identifier and venue checked against a primary page or model card; PV = paper and venue consistent across sources, numbers not re-read; G = standard reference, identifier not re-checked online.", { x: 0.6, y: 6.62, w: 12.1, h: 0.35, fontSize: 10.5, italic: true, color: SLATE });
});

(async () => {
  await pres.writeFile({ fileName: "LearnMate_G06_Research_Presentation.pptx" });
  await applyTheme("LearnMate_G06_Research_Presentation.pptx", THEME);
  console.log("done");
})();
