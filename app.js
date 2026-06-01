const uploadSection = document.getElementById('uploadSection');
const previewSection = document.getElementById('previewSection');

const dropZone   = document.getElementById('dropZone');
const fileInput  = document.getElementById('fileInput');
const fileChip   = document.getElementById('fileChip');
const fileName   = document.getElementById('fileName');
const removeFile = document.getElementById('removeFile');
const processBtn = document.getElementById('processBtn');
const statusEl   = document.getElementById('status');

const previewMeta = document.getElementById('previewMeta');
const previewBody = document.getElementById('previewBody');
const downloadBtn = document.getElementById('downloadBtn');
const backBtn     = document.getElementById('backBtn');

let selectedFile = null;
let resultDocxB64 = null;
let resultFilename = null;

function setFile(file) {
  if (!file || !file.name.endsWith('.docx')) {
    setStatus('error', 'Please upload a .docx file.');
    return;
  }
  selectedFile = file;
  fileName.textContent = file.name;
  fileChip.classList.add('visible');
  processBtn.disabled = false;
  clearStatus();
}

function clearFile() {
  selectedFile = null;
  fileInput.value = '';
  fileChip.classList.remove('visible');
  processBtn.disabled = true;
  clearStatus();
}

function setStatus(type, msg) {
  statusEl.className = 'status ' + type;
  statusEl.innerHTML = type === 'loading'
    ? `<span class="spinner"></span>${msg}`
    : msg;
}

function clearStatus() {
  statusEl.className = 'status';
  statusEl.textContent = '';
}

function showPreview(data) {
  resultDocxB64  = data.docx_b64;
  resultFilename = data.filename;

  const realParas = data.paragraphs.filter(p => p.trim() !== '');
  previewMeta.textContent = `${realParas.length} paragraph${realParas.length !== 1 ? 's' : ''} · ${selectedFile.name}`;

  previewBody.innerHTML = '';
  data.paragraphs.forEach(p => {
    const el = document.createElement('p');
    el.textContent = p;
    if (!p.trim()) el.classList.add('spacer');
    previewBody.appendChild(el);
  });

  uploadSection.hidden = true;
  previewSection.hidden = false;
}

function showUpload() {
  previewSection.hidden = true;
  uploadSection.hidden = false;
  clearFile();
  resultDocxB64  = null;
  resultFilename = null;
}

function downloadDocx() {
  if (!resultDocxB64) return;
  const bytes = Uint8Array.from(atob(resultDocxB64), c => c.charCodeAt(0));
  const blob  = new Blob([bytes], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
  const url   = URL.createObjectURL(blob);
  const a     = document.createElement('a');
  a.href      = url;
  a.download  = resultFilename;
  a.click();
  URL.revokeObjectURL(url);
}

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) setFile(fileInput.files[0]);
});

removeFile.addEventListener('click', clearFile);
backBtn.addEventListener('click', showUpload);
downloadBtn.addEventListener('click', downloadDocx);

dropZone.addEventListener('dragover', e => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
});

processBtn.addEventListener('click', async () => {
  if (!selectedFile) return;

  processBtn.disabled = true;
  setStatus('loading', 'Processing…');

  const form = new FormData();
  form.append('file', selectedFile);

  try {
    const res = await fetch('/api/process', { method: 'POST', body: form });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || `Server error ${res.status}`);

    showPreview(data);
  } catch (err) {
    setStatus('error', err.message);
    processBtn.disabled = false;
  }
});
