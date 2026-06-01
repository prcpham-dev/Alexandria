const SLOT_COUNT = 3;

const slots = Array.from({ length: SLOT_COUNT }, (_, i) => ({
  id: i,
  addedAt: null,
  state: 'idle',   // idle | processing | done | error
  file: null,
  result: null,
  error: null,
}));

let activePreviewSlot = null;

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const previewSection = document.getElementById('previewSection');
const previewTabs = document.getElementById('previewTabs');
const previewMeta = document.getElementById('previewMeta');
const previewBody = document.getElementById('previewBody');
const downloadBtn = document.getElementById('downloadBtn');
const closePreviewBtn = document.getElementById('closePreviewBtn');

function els(id) {
  return {
    root: document.getElementById(`slot-${id}`),
    name: document.getElementById(`slot-name-${id}`),
    mid: document.getElementById(`slot-mid-${id}`),
    clearBtn: document.getElementById(`slot-clear-${id}`),
    openBtn: document.getElementById(`slot-open-${id}`),
    dlBtn: document.getElementById(`slot-dl-${id}`),
  };
}

function render(id) {
  const slot = slots[id];
  const e = els(id);

  e.root.dataset.state = slot.state;
  e.name.textContent = slot.file ? slot.file.name : '—';

  const statusHTML = {
    processing: '<span class="slot-spinner"></span><span class="slot-status-text">Processing…</span>',
    done: '<span class="slot-done-icon">✓</span>',
    error: `<span class="slot-error-icon">!</span><span class="slot-status-text slot-error-text" title="${slot.error}">${slot.error}</span>`,
  };
  e.mid.innerHTML = statusHTML[slot.state] ?? '';

  e.clearBtn.hidden = slot.state === 'idle' || slot.state === 'processing' || slot.state === 'done';
  e.openBtn.hidden = slot.state !== 'done';
  e.dlBtn.hidden = slot.state !== 'done';
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

  slots[id].file = file;
  slots[id].addedAt = Date.now();
  slots[id].state = 'idle';
  slots[id].result = null;
  slots[id].error = null;
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

  const form = new FormData();
  form.append('file', slot.file);

  try {
    const res = await fetch('/api/process', { method: 'POST', body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `Server error ${res.status}`);
    slot.result = data;
    slot.state = 'done';
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

  const active = slots[activePreviewSlot];
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
  const blob = new Blob([bytes], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = slot.result.filename;
  a.click();
  URL.revokeObjectURL(url);
}

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) assignFile(fileInput.files[0]);
  fileInput.value = '';
});

dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
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
  e.clearBtn.addEventListener('click', () => clearSlot(id));
  e.openBtn.addEventListener('click', () => openSlot(id));
  e.dlBtn.addEventListener('click', () => downloadSlot(id));
}
