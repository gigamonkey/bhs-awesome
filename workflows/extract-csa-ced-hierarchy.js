export const meta = {
  name: 'extract-csa-ced-hierarchy',
  description: 'Extract the AP CSA CED topic/LO/EK hierarchy from the PDF, one agent per topic, verify each, then assemble csa/ced-2025-hierarchy.md',
  phases: [
    { title: 'Extract', detail: 'one agent per topic reads its PDF pages and writes markdown' },
    { title: 'Verify', detail: 'one agent per topic re-reads the pages and corrects the markdown' },
    { title: 'Assemble', detail: 'concatenate the per-topic files under their unit headers' },
  ],
}

// Recovered from the original session workflow
// (extract-csa-ced-hierarchy-wf_ce8b003c-707.js). The PDF path, output dir, and
// topic page-ranges were originally passed in via `args`; they are inlined here
// as defaults so the workflow is self-contained and re-runnable from the repo
// root. Override any of them by passing an args object: {pdf, outdir, topics, units}.

const DEFAULTS = {
  pdf: 'csa/ced-2025.pdf',
  outdir: '/tmp/csa-extract',
  // The final hierarchy file assembled in the Assemble phase.
  output: 'csa/ced-2025-hierarchy.md',
  // Topic id -> the PDF page range carrying its "Required Course Content".
  topics: [
    { id: '1.1', pages: '36-37' }, { id: '1.2', pages: '38' },
    { id: '1.3', pages: '39-40' }, { id: '1.4', pages: '41' },
    { id: '1.5', pages: '42-43' }, { id: '1.6', pages: '44' },
    { id: '1.7', pages: '45' }, { id: '1.8', pages: '46' },
    { id: '1.9', pages: '47-48' }, { id: '1.10', pages: '49' },
    { id: '1.11', pages: '50' }, { id: '1.12', pages: '51' },
    { id: '1.13', pages: '52-53' }, { id: '1.14', pages: '54' },
    { id: '1.15', pages: '55-57' },
    { id: '2.1', pages: '67' }, { id: '2.2', pages: '68' },
    { id: '2.3', pages: '69' }, { id: '2.4', pages: '70' },
    { id: '2.5', pages: '71' }, { id: '2.6', pages: '72' },
    { id: '2.7', pages: '73' }, { id: '2.8', pages: '74' },
    { id: '2.9', pages: '75' }, { id: '2.10', pages: '76' },
    { id: '2.11', pages: '77' }, { id: '2.12', pages: '78' },
    { id: '3.1', pages: '86-87' }, { id: '3.2', pages: '88' },
    { id: '3.3', pages: '89' }, { id: '3.4', pages: '90' },
    { id: '3.5', pages: '91-92' }, { id: '3.6', pages: '93' },
    { id: '3.7', pages: '94' }, { id: '3.8', pages: '95' },
    { id: '3.9', pages: '96' },
    { id: '4.1', pages: '106' }, { id: '4.2', pages: '107' },
    { id: '4.3', pages: '108' }, { id: '4.4', pages: '109' },
    { id: '4.5', pages: '110' }, { id: '4.6', pages: '111-113' },
    { id: '4.7', pages: '114-115' }, { id: '4.8', pages: '116-117' },
    { id: '4.9', pages: '118' }, { id: '4.10', pages: '119' },
    { id: '4.11', pages: '120-121' }, { id: '4.12', pages: '122' },
    { id: '4.13', pages: '123' }, { id: '4.14', pages: '124' },
    { id: '4.15', pages: '125' }, { id: '4.16', pages: '126' },
    { id: '4.17', pages: '127-128' },
  ],
  // Unit number -> H1 title, used to assemble the final file. Topics whose id
  // starts with "<n>." are grouped under unit <n>.
  units: [
    { n: 1, title: 'Using Objects and Methods' },
    { n: 2, title: 'Selection and Iteration' },
    { n: 3, title: 'Class Creation' },
    { n: 4, title: 'Data Collections' },
  ],
}

const cfg = { ...DEFAULTS, ...(typeof args === 'string' ? JSON.parse(args) : args || {}) }
const { pdf: PDF, outdir: OUTDIR, output: OUTPUT, topics, units } = cfg

const SUMMARY = {
  type: 'object',
  properties: { summary: { type: 'string' } },
  required: ['summary'],
}

const VERIFY = {
  type: 'object',
  properties: { issues: { type: 'array', items: { type: 'string' } } },
  required: ['issues'],
}

function extractPrompt(t) {
  return `Use the Read tool to read pages ${t.pages} of the PDF file ${PDF} (pass pages: "${t.pages}").

These pages of the AP Computer Science A Course and Exam Description contain TOPIC ${t.id} and its "Required Course Content", laid out in two columns: LEARNING OBJECTIVE on the left (identifiers like ${t.id}.A, ${t.id}.B) and ESSENTIAL KNOWLEDGE on the right (identifiers like ${t.id}.A.1, ${t.id}.A.2). Each learning objective has one or more essential knowledge items beside it, and an item may continue onto the next page.

Write a markdown extract of JUST topic ${t.id} to the file ${OUTDIR}/topic-${t.id}.md with this structure:

## ${t.id} <topic title>

### ${t.id}.A <learning objective text>

#### ${t.id}.A.1 <essential knowledge text>

Rules:
- Capture the text EXACTLY as printed in the PDF: verbatim wording and punctuation. Join wrapped lines into single lines and repair words hyphenated across line breaks.
- Heading lines must each be a single line: the full topic title / learning-objective text / first paragraph of essential-knowledge text goes on the heading line itself.
- If an essential-knowledge item has content beyond its first paragraph, put it below the heading as markdown: bulleted lists as "- item"; lettered lists as "a. item"; code blocks indented by exactly 4 spaces (do NOT use fenced code blocks); further paragraphs as plain text.
- Words printed in monospace (code such as int, double, System.out.println, ArrayList) go in \`backticks\`. Words printed in italics go in *asterisks*.
- Put a blank line between every heading and block.
- Include ALL learning objectives and ALL essential knowledge items for this topic, in order. If the page range includes blank pages or material that is not part of topic ${t.id}'s Required Course Content, ignore it.
- EXCLUDE: SUGGESTED SKILLS sidebars, AVAILABLE RESOURCES boxes, exclusion-statement and note boxes, the "Required Course Content" label, page headers and footers, unit banners, and anything belonging to another topic.

Return a one-line summary: the topic title and the number of learning objectives and essential knowledge items you wrote.`
}

function verifyPrompt(t) {
  return `You are adversarially verifying an extraction. First read the file ${OUTDIR}/topic-${t.id}.md. Then use the Read tool to read pages ${t.pages} of the PDF file ${PDF} (pass pages: "${t.pages}").

The file should contain topic ${t.id} of the AP CSA Course and Exam Description as markdown: "## ${t.id} <topic title>", then "### ${t.id}.X <learning objective>" headings, each followed by its "#### ${t.id}.X.n <essential knowledge>" headings.

Check against the PDF:
1. Every learning objective and essential knowledge item of topic ${t.id} on those pages appears in the file, in order, under the correct identifier. None missing, none invented.
2. The text is verbatim from the PDF (allowing for line-wrap joining and the markdown conventions below).
3. Formatting conventions: heading lines are single lines containing the full title/text (first paragraph for EK items); extra EK content sits below the heading; bulleted lists use "- "; lettered lists use "a. "; code blocks are indented 4 spaces and NOT fenced; inline monospace uses \`backticks\`; italics use *asterisks*; blank lines separate headings and blocks.
4. No contamination: no SUGGESTED SKILLS / AVAILABLE RESOURCES / exclusion-statement / header / footer text, and nothing from other topics.

Fix any problems by editing the file directly. Return the list of issues you found and fixed (empty list if the file was already correct).`
}

function assemblePrompt() {
  const groups = units.map(u => {
    const ids = topics.filter(t => t.id.startsWith(`${u.n}.`)).map(t => t.id)
    return `Unit ${u.n}: ${u.title}\n  topic files (in order): ${ids.map(id => `topic-${id}.md`).join(', ')}`
  }).join('\n')
  return `Assemble the final AP CSA CED hierarchy file from the per-topic markdown files in ${OUTDIR}.

Write ${OUTPUT}. For each unit below, emit a level-1 heading "# Unit N: <title>", a blank line, then the contents of that unit's topic files in the listed order, separated by blank lines. Each topic file already begins with its "## <id> <title>" heading, so do not add or renumber headings. Ensure exactly one blank line between blocks and a trailing newline at end of file.

${groups}

You may do this with a shell command (e.g. printf the unit header then cat the topic files). After writing, report the total line count of ${OUTPUT}.`
}

phase('Extract')
const results = await pipeline(
  topics,
  t => agent(extractPrompt(t), { label: `extract:${t.id}`, phase: 'Extract', schema: SUMMARY }),
  (prev, t) => agent(verifyPrompt(t), { label: `verify:${t.id}`, phase: 'Verify', schema: VERIFY })
    .then(v => ({ id: t.id, extracted: prev ? prev.summary : null, issues: v ? v.issues : ['verifier died'] })),
)

const failed = results.map((r, i) => (r ? null : topics[i].id)).filter(Boolean)
if (failed.length) log(`topics with no result: ${failed.join(', ')}`)

phase('Assemble')
const assembled = await agent(assemblePrompt(), { label: 'assemble', phase: 'Assemble' })

return { topics: results.filter(Boolean), assembled }
