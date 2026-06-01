// ── Cleaning logic (ported from process.py) ──────────────────────────────────

const TIMESTAMP_PAT = [
  '\\d{1,2}:\\d{2}(?::\\d{2})?',
  '\\d+\\s+hours?,\\s*\\d+\\s+minutes?,\\s*\\d+\\s+seconds?',
  '\\d+\\s+hours?,\\s*\\d+\\s+minutes?',
  '\\d+\\s+hours?,\\s*\\d+\\s+seconds?',
  '\\d+\\s+minutes?,\\s*\\d+\\s+seconds?',
  '\\d+\\s+hours?',
  '\\d+\\s+minutes?',
  '\\d+\\s+seconds?',
].join('|');

const RX_STRIP_BRACKETS  = /\[.*?\]/g;
const RX_STRIP_TS_PREFIX = new RegExp('^(?:' + TIMESTAMP_PAT + ')\\s+');
const RX_SKIP_LINE       = new RegExp('^(?:' + TIMESTAMP_PAT + '|sync\\s+to\\s+video\\s+time)\\s*$', 'i');
const RX_STRIP_PREFIX    = /^(?:\d+[.)]\s+|-\s+|\*\s+|•\s+)/;
const RX_STRIP_TRAILING  = /\s*sync\s+to\s+video\s+time\s*$/i;

function stripPrefix(text) {
  text = text.replace(RX_STRIP_BRACKETS, '').trim();
  text = text.replace(RX_STRIP_TS_PREFIX, '');
  text = text.replace(RX_STRIP_PREFIX, '');
  text = text.replace(RX_STRIP_TRAILING, '').trim();
  return text.trim();
}

function ensurePeriod(text) {
  return text && !'.!?…'.includes(text.at(-1)) ? text + '.' : text;
}


function processParagraphs(rawLines) {
  const out = [];
  let joinNext = false;
  let afterTimestamp = false;

  for (const raw of rawLines) {
    const stripped = raw.trim();
    if (!stripped) continue;
    if (RX_SKIP_LINE.test(stripped)) { afterTimestamp = true; continue; }

    const hadBrackets  = /\[.*?\]/.test(stripped);
    const hadTimestamp = RX_STRIP_TS_PREFIX.test(stripped);
    const text = stripPrefix(stripped);

    if (!text) {
      if (stripped) joinNext = true;
      afterTimestamp = false;
      continue;
    }

    const isNextLower = /^\p{Ll}/u.test(text);

    // Force new paragraph when a skipped timestamp or bracket was followed by
    // an uppercase line — clear signal of a new sentence or speaker.
    const forceNew = (afterTimestamp || hadBrackets) && !isNextLower;

    const shouldJoin = !forceNew && out.length > 0 && (
      joinNext      ||
      hadTimestamp  ||
      isNextLower
    );

    if (shouldJoin) {
      out[out.length - 1] = out[out.length - 1].trimEnd() + ' ' + text;
    } else {
      if (out.length > 0) {
        out[out.length - 1] = ensurePeriod(out[out.length - 1]);
        out.push('');
      }
      out.push(text);
    }
    joinNext = false;
    afterTimestamp = false;
  }

  if (out.length > 0 && out.at(-1)) {
    out[out.length - 1] = ensurePeriod(out[out.length - 1]);
  }

  return out;
}

// ── .docx in-browser processing ───────────────────────────────────────────────

const WNS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main';

function paraText(paraEl) {
  return Array.from(paraEl.getElementsByTagNameNS(WNS, 't'))
    .map(t => t.textContent)
    .join('');
}

function buildDocXml(paragraphs, sectPrXml) {
  const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const body = paragraphs.map(p =>
    p.trim()
      ? `<w:p><w:r><w:t xml:space="preserve">${esc(p)}</w:t></w:r></w:p>`
      : '<w:p/>'
  ).join('') + (sectPrXml || '<w:sectPr/>');

  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`
    + `<w:document xmlns:w="${WNS}">`
    + `<w:body>${body}</w:body>`
    + `</w:document>`;
}

async function processDocx(file) {
  const zip    = await JSZip.loadAsync(await file.arrayBuffer());
  const xmlStr = await zip.file('word/document.xml').async('string');
  const xmlDoc = new DOMParser().parseFromString(xmlStr, 'application/xml');

  const rawLines = Array.from(xmlDoc.getElementsByTagNameNS(WNS, 'p'))
    .map(paraText)
    .filter(t => t.trim());

  const sectPrEl  = xmlDoc.getElementsByTagNameNS(WNS, 'sectPr')[0];
  const sectPrXml = sectPrEl ? new XMLSerializer().serializeToString(sectPrEl) : '';

  const cleaned = processParagraphs(rawLines);
  zip.file('word/document.xml', buildDocXml(cleaned, sectPrXml));

  const bytes   = await zip.generateAsync({ type: 'uint8array', compression: 'DEFLATE' });
  const docx_b64 = btoa(Array.from(bytes, b => String.fromCharCode(b)).join(''));
  const filename  = file.name.replace(/\.docx$/i, '_cleaned.docx');

  return { paragraphs: cleaned, docx_b64, filename };
}

// ── Slot state management ─────────────────────────────────────────────────────

const SLOT_COUNT = 3;

const slots = Array.from({ length: SLOT_COUNT }, (_, i) => ({
  id: i,
  addedAt: null,
  state: 'idle',
  file: null,
  result: null,
  error: null,
}));

let activePreviewSlot = null;

const dropZone        = document.getElementById('dropZone');
const fileInput       = document.getElementById('fileInput');
const previewSection  = document.getElementById('previewSection');
const previewMeta     = document.getElementById('previewMeta');
const previewBody     = document.getElementById('previewBody');
const downloadBtn     = document.getElementById('downloadBtn');
const closePreviewBtn = document.getElementById('closePreviewBtn');

function els(id) {
  return {
    root:    document.getElementById(`slot-${id}`),
    name:    document.getElementById(`slot-name-${id}`),
    mid:     document.getElementById(`slot-mid-${id}`),
    openBtn: document.getElementById(`slot-open-${id}`),
    dlBtn:   document.getElementById(`slot-dl-${id}`),
  };
}

function render(id) {
  const slot = slots[id];
  const e = els(id);

  e.root.dataset.state = slot.state;
  e.name.textContent = slot.file ? slot.file.name : '—';

  const statusHTML = {
    processing: '<span class="slot-spinner"></span><span class="slot-status-text">Processing…</span>',
    done:       '<span class="slot-done-icon">✓</span>',
    error:      `<span class="slot-error-icon">!</span><span class="slot-status-text slot-error-text" title="${slot.error}">${slot.error}</span>`,
  };
  e.mid.innerHTML = statusHTML[slot.state] ?? '';

  e.openBtn.hidden = slot.state !== 'done';
  e.dlBtn.hidden   = slot.state !== 'done';
}

function findTargetSlot() {
  const idle = slots.find(s => s.state === 'idle');
  if (idle) return idle.id;
  const evict = slots
    .filter(s => s.state !== 'processing')
    .sort((a, b) => a.addedAt - b.addedAt)[0];
  return evict ? evict.id : null;
}

function assignFile(file) {
  if (!file || !file.name.toLowerCase().endsWith('.docx')) return;
  const id = findTargetSlot();
  if (id === null) return;

  if (activePreviewSlot === id) {
    activePreviewSlot = null;
    renderPreview();
  }

  slots[id] = { id, addedAt: Date.now(), state: 'idle', file, result: null, error: null };
  render(id);
  processSlot(id);
}

function clearSlot(id) {
  slots[id] = { id, addedAt: null, state: 'idle', file: null, result: null, error: null };
  render(id);
  if (activePreviewSlot === id) {
    activePreviewSlot = null;
    renderPreview();
  }
}

async function processSlot(id) {
  const slot = slots[id];
  slot.state = 'processing';
  render(id);

  try {
    slot.result = await processDocx(slot.file);
    slot.state  = 'done';
  } catch (err) {
    slot.error = err.message;
    slot.state = 'error';
  }

  render(id);

  if (slot.state === 'done') {
    if (activePreviewSlot === null) activePreviewSlot = id;
    renderPreview();
  }
}

function openSlot(id) {
  activePreviewSlot = id;
  renderPreview();
  previewSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function renderPreview() {
  const doneSlots = slots.filter(s => s.state === 'done');
  if (doneSlots.length === 0) {
    previewSection.hidden = true;
    activePreviewSlot = null;
    return;
  }

  if (activePreviewSlot === null || slots[activePreviewSlot].state !== 'done') {
    activePreviewSlot = doneSlots[0].id;
  }

  const active   = slots[activePreviewSlot];
  const realPara = active.result.paragraphs.filter(p => p.trim() !== '');
  previewMeta.textContent = `${realPara.length} paragraph${realPara.length !== 1 ? 's' : ''} · ${active.file.name}`;

  previewBody.innerHTML = '';
  active.result.paragraphs.forEach(p => {
    const el = document.createElement('p');
    el.textContent = p;
    if (!p.trim()) el.classList.add('spacer');
    previewBody.appendChild(el);
  });

  previewSection.hidden = false;
}

function downloadSlot(id) {
  const slot = slots[id];
  if (!slot.result) return;
  const bytes = Uint8Array.from(atob(slot.result.docx_b64), c => c.charCodeAt(0));
  const blob  = new Blob([bytes], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
  const url   = URL.createObjectURL(blob);
  const a     = document.createElement('a');
  a.href      = url;
  a.download  = slot.result.filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Events ────────────────────────────────────────────────────────────────────

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) assignFile(fileInput.files[0]);
  fileInput.value = '';
});

dropZone.addEventListener('dragover',  e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) assignFile(file);
});

downloadBtn.addEventListener('click', () => {
  if (activePreviewSlot !== null) downloadSlot(activePreviewSlot);
});

closePreviewBtn.addEventListener('click', () => {
  const id = activePreviewSlot;
  activePreviewSlot = null;
  previewSection.hidden = true;
  if (id !== null) clearSlot(id);
});

for (let i = 0; i < SLOT_COUNT; i++) {
  const id = i;
  const e = els(id);
  e.openBtn.addEventListener('click', () => openSlot(id));
  e.dlBtn.addEventListener('click',   () => downloadSlot(id));
}
