export const meta = {
  name: 'extract-csp-ced-hierarchy',
  description: 'Extract the AP CSP CED big-idea/EU/LO/EK hierarchy from the PDF, one agent per big idea, then assemble csp/ced-hierarchy.md',
  phases: [
    { title: 'Extract', detail: 'one agent per big idea reads its PDF pages (as images) and writes markdown' },
    { title: 'Assemble', detail: 'concatenate the per-section files under their Big Idea headers' },
  ],
}

// RECONSTRUCTED from session 54430ae4 (2026-05-24), which produced
// csp/ced-hierarchy.md with no saved script -- the extraction was driven by
// inline Agent prompts, the per-big-idea output written to temporary csp/.biN.md
// files, then concatenated with a bash heredoc and the temp files removed. This
// workflow reproduces that mechanism: parallel agents read PDF pages AS IMAGES
// (CSP boxes don't extract cleanly as text), each writing one section file, then
// an assemble agent stitches them together under the five Big Idea headers.
//
// Big Idea 3 (AAP) is split across three agents (AAP-1, AAP-2, AAP-3/4) because
// its page run is long; each split agent is scoped to its enduring understanding.

const DEFAULTS = {
  pdf: 'csp/ap-computer-science-principles-course-and-exam-description.pdf',
  outdir: '/tmp/csp-extract',
  output: 'csp/ced-hierarchy.md',
  // One entry per extraction agent. `bi` groups split sections under one Big
  // Idea for assembly; `scope` (optional) restricts a split agent to part of the
  // page run; `idHint` (optional) is a verbatim count aid from the original run.
  sections: [
    {
      file: 'bi1.md', bi: 1, code: 'CRD', pages: '228-232',
      idHint: 'The IDs you should encounter: CRD-1, CRD-1.A (6 EKs), CRD-1.B (2 EKs), CRD-1.C (1 EK), then CRD-2, CRD-2.A (2 EKs), CRD-2.B (5 EKs), CRD-2.C (6 EKs), CRD-2.D (2 EKs), CRD-2.E (4 EKs), CRD-2.F (7 EKs), CRD-2.G (5 EKs), CRD-2.H (2 EKs), CRD-2.I (5 EKs), CRD-2.J (3 EKs). Verify counts match.',
    },
    { file: 'bi2.md', bi: 2, code: 'DAT', pages: '233-237' },
    {
      file: 'bi3a.md', bi: 3, code: 'AAP', pages: '238-241',
      scope: 'ONLY extract enduring understanding AAP-1 and all its learning objectives and essential knowledge items. Stop when AAP-2 begins.',
    },
    {
      file: 'bi3b.md', bi: 3, code: 'AAP', pages: '241-248',
      scope: 'ONLY extract AAP-2. Do NOT extract AAP-1 (it ends on the early part of page 241) and do NOT extract AAP-3 (it starts after AAP-2 ends). Start at the AAP-2 enduring understanding box and stop when you hit AAP-3.',
    },
    {
      file: 'bi3c.md', bi: 3, code: 'AAP', pages: '248-255',
      scope: 'Extract AAP-3 onward (AAP-3 and AAP-4) -- every enduring understanding of Big Idea 3 from AAP-3 to the end of the big idea. Do NOT re-extract AAP-1 or AAP-2.',
    },
    { file: 'bi4.md', bi: 4, code: 'CSN', pages: '256-259' },
    { file: 'bi5.md', bi: 5, code: 'IOC', pages: '260-265' },
  ],
  // Big Idea number -> the H1 line used when assembling the final file.
  bigIdeas: [
    { n: 1, h1: '# Big Idea 1: Creative Development (CRD)' },
    { n: 2, h1: '# Big Idea 2: Data (DAT)' },
    { n: 3, h1: '# Big Idea 3: Algorithms and Programming (AAP)' },
    { n: 4, h1: '# Big Idea 4: Computer Systems and Networks (CSN)' },
    { n: 5, h1: '# Big Idea 5: Impact of Computing (IOC)' },
  ],
}

const cfg = { ...DEFAULTS, ...(typeof args === 'string' ? JSON.parse(args) : args || {}) }
const { pdf: PDF, outdir: OUTDIR, output: OUTPUT, sections, bigIdeas } = cfg

const SUMMARY = {
  type: 'object',
  properties: { summary: { type: 'string' } },
  required: ['summary'],
}

function extractPrompt(s) {
  return `You are extracting curriculum content from the AP Computer Science Principles Course and Exam Description PDF at \`${PDF}\`.

Read pages ${s.pages} of the PDF (the appendix "Conceptual Framework" pages for Big Idea ${s.bi}, enduring understanding family ${s.code}). Use the Read tool with the \`pages\` parameter to load these pages AS IMAGES.

You're extracting a three-level hierarchy:
- Enduring Understandings (e.g., "${s.code}-1") -- H2 header
- Learning Objectives (e.g., "${s.code}-1.A") -- H3 header
- Essential Knowledge items (e.g., "${s.code}-1.A.1") -- H4 header
${s.scope ? `\nSCOPE: ${s.scope}\n` : ''}
Write the output to \`${OUTDIR}/${s.file}\` using exactly this format:

## ${s.code}-1 <the enduring understanding text from the CED>

### ${s.code}-1.A <the learning objective text>

#### ${s.code}-1.A.1 <the essential knowledge text>

Rules:
- Include the identifier followed by a space and then the exact text from the CED, all on one line as the header.
- Do NOT include a \`#\` Big Idea header -- only \`##\`, \`###\`, \`####\`. The H1 is added during assembly.
- Capture the text EXACTLY as it appears in the CED. Watch for spacing issues from PDF text extraction (e.g., "throughcollaboration" should be "through collaboration"). Use the images to verify correct spacing.
- For Essential Knowledge items that contain bulleted sub-lists, put the lead-in text on the header line, then a blank line, then a Markdown bullet list (use "- " for bullets).
- For Learning Objectives that use multi-part lettered tasks (like "a. Determine the result..."), put the lead-in line in the H3 header, then a blank line, then a Markdown lettered list ("a. ", "b. ", ...).
- If you encounter an "EXCLUSION STATEMENT" sub-box attached to an EK, omit it (it's not part of the hierarchy).
- Do not include skill tags (like "1.C", "4.A", "3.B") that appear at the end of LO text -- those are unrelated metadata badges.
- Put a blank line between every heading and block.
${s.idHint ? `- ${s.idHint}\n` : ''}
When done, report "done, wrote N lines".`
}

function assemblePrompt() {
  const plan = bigIdeas.map(bi => {
    const files = sections.filter(s => s.bi === bi.n).map(s => s.file)
    return `${bi.h1}\n  section files (in order): ${files.join(', ')}`
  }).join('\n')
  return `Assemble the final AP CSP CED hierarchy file from the per-section markdown files in ${OUTDIR}.

Write ${OUTPUT}. For each Big Idea below, emit its H1 line exactly as given, a blank line, then the contents of that Big Idea's section files in the listed order, separated by blank lines. The section files contain only \`##\`/\`###\`/\`####\` headings (no H1), so the H1 lines below are the only level-1 headings. Ensure exactly one blank line between blocks and a trailing newline.

${plan}

You may do this with a shell command (printf the H1 then cat the section files). After writing, report the total line count of ${OUTPUT}.`
}

phase('Extract')
const extracted = await parallel(
  sections.map(s => () =>
    agent(extractPrompt(s), { label: `extract:${s.file}`, phase: 'Extract', schema: SUMMARY })
      .then(r => ({ file: s.file, summary: r ? r.summary : null }))),
)

const failed = extracted.filter(r => !r || r.summary === null).map((r, i) => sections[i].file)
if (failed.length) log(`sections with no result: ${failed.join(', ')}`)

phase('Assemble')
const assembled = await agent(assemblePrompt(), { label: 'assemble', phase: 'Assemble' })

return { sections: extracted, assembled }
