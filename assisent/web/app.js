const chatEl = document.getElementById('chat');
const statusEl = document.getElementById('status');
const formEl = document.getElementById('form');
const inputEl = document.getElementById('input');
const tempEl = document.getElementById('temp');
const modelEl = document.getElementById('model');
const historyPanel = document.getElementById('history');
const historyList = document.getElementById('history-list');
const historyDate = document.getElementById('history-date');
const historySearch = document.getElementById('history-search');
const historyToggle = document.getElementById('history-toggle');
const themeToggle = document.getElementById('theme-toggle');

const messages = [];
let sessionId = localStorage.getItem('sessionId');
if (!sessionId) {
  sessionId = Date.now().toString(36) + Math.random().toString(36).slice(2);
  localStorage.setItem('sessionId', sessionId);
}

function addMessage(role, content) {
  const wrap = document.createElement('div');
  wrap.className = `msg ${role}`;
  const roleEl = document.createElement('div');
  roleEl.className = 'role';
  roleEl.textContent = role === 'user' ? '你' : '心理支持';
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = content;
  wrap.appendChild(roleEl);
  wrap.appendChild(bubble);
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
}

async function checkHealth() {
  try {
    const r = await fetch('/health');
    if (!r.ok) throw new Error('bad');
    statusEl.textContent = '服务已就绪';
  } catch (e) {
    statusEl.textContent = '服务未就绪，请检查后端';
  }
}

checkHealth();

async function loadHistory() {
  try {
    const r = await fetch(`/history/${sessionId}`);
    if (!r.ok) return;
    const hist = await r.json();
    for (const h of hist) {
      addMessage(h.role === 'user' ? 'user' : 'assistant', h.content);
      messages.push({ role: h.role, content: h.content });
    }
  } catch (e) {}
}

loadHistory();

const HISTORY_KEY = 'chat_history_v1';

function loadLocalHistory() {
  const raw = localStorage.getItem(HISTORY_KEY);
  if (!raw) return [];
  try { return JSON.parse(raw) || []; } catch (e) { return []; }
}

function saveLocalHistory(records) {
  let s = JSON.stringify(records);
  const limit = 5 * 1024 * 1024;
  while (s.length > limit && records.length > 0) {
    records.shift();
    s = JSON.stringify(records);
  }
  localStorage.setItem(HISTORY_KEY, s);
}

function addLocalRecord(rec) {
  let r = JSON.stringify(rec);
  const max = 10 * 1024;
  if (r.length > max) {
    const over = r.length - max;
    const a = rec.assistant || '';
    if (a.length > over) rec.assistant = a.slice(0, a.length - over);
    r = JSON.stringify(rec);
    if (r.length > max) rec.assistant = rec.assistant.slice(0, Math.max(0, rec.assistant.length - (r.length - max)));
  }
  const arr = loadLocalHistory();
  arr.push(rec);
  saveLocalHistory(arr);
}

function formatTs(ts) {
  const d = new Date(ts);
  const y = d.getFullYear();
  const m = String(d.getMonth()+1).padStart(2,'0');
  const day = String(d.getDate()).padStart(2,'0');
  const hh = String(d.getHours()).padStart(2,'0');
  const mm = String(d.getMinutes()).padStart(2,'0');
  return `${y}-${m}-${day} ${hh}:${mm}`;
}

function renderHistory() {
  const q = (historySearch.value || '').toLowerCase();
  const dateVal = historyDate.value;
  let arr = loadLocalHistory();
  arr.sort((a,b)=>b.ts - a.ts);
  if (dateVal) {
    const target = new Date(dateVal);
    arr = arr.filter(r=>{
      const d = new Date(r.ts);
      return d.getFullYear()===target.getFullYear() && d.getMonth()===target.getMonth() && d.getDate()===target.getDate();
    });
  }
  if (q) {
    arr = arr.filter(r=> (r.user||'').toLowerCase().includes(q) || (r.assistant||'').toLowerCase().includes(q));
  }
  const frag = document.createDocumentFragment();
  for (const r of arr) {
    const item = document.createElement('div');
    item.className = 'history-item';
    const top = document.createElement('div');
    top.className = 'history-top';
    const ts = document.createElement('div');
    ts.textContent = formatTs(r.ts);
    const sid = document.createElement('div');
    sid.textContent = r.sessionId ? r.sessionId.slice(0,8) : '';
    const preview = document.createElement('div');
    preview.className = 'history-preview';
    const u = (r.user||'').slice(0,30);
    const a = (r.assistant||'').slice(0,50);
    const uText = r.user && r.user.length>30 ? u + '...' : u;
    const aText = r.assistant && r.assistant.length>50 ? a + '...' : a;
    preview.textContent = `你：${uText}\nAI：${aText}`;
    const expand = document.createElement('div');
    expand.className = 'history-expand';
    expand.textContent = `你：${r.user||''}\n\nAI：\n${r.assistant||''}`;
    top.appendChild(ts);
    top.appendChild(sid);
    item.appendChild(top);
    item.appendChild(preview);
    item.appendChild(expand);
    item.addEventListener('click', ()=>{
      item.classList.toggle('open');
    });
    frag.appendChild(item);
  }
  historyList.innerHTML = '';
  historyList.appendChild(frag);
}

let searchTimer = null;
historySearch.addEventListener('input', ()=>{
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(renderHistory, 150);
});
historyDate.addEventListener('change', renderHistory);
historyToggle.addEventListener('click', ()=>{
  if (window.matchMedia('(max-width: 768px)').matches) {
    historyPanel.classList.toggle('open');
  }
});
themeToggle.addEventListener('click', ()=>{
  const cur = localStorage.getItem('theme');
  const next = cur === 'dark' ? 'light' : 'dark';
  localStorage.setItem('theme', next);
  if (next === 'dark') document.body.classList.add('dark'); else document.body.classList.remove('dark');
});
const initTheme = localStorage.getItem('theme') || 'light';
if (initTheme === 'dark') document.body.classList.add('dark');

formEl.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;

  addMessage('user', text);
  messages.push({ role: 'user', content: text });
  inputEl.value = '';

  try {
    const resp = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, temperature: parseFloat(tempEl.value || '0.6'), model: modelEl.value, session_id: sessionId })
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      addMessage('assistant', `出错：${err.detail || '未知错误'}`);
      return;
    }
    const data = await resp.json();
    addMessage('assistant', data.content);
    messages.push({ role: 'assistant', content: data.content });
    if (data.session_id && data.session_id !== sessionId) {
      sessionId = data.session_id;
      localStorage.setItem('sessionId', sessionId);
    }
    addLocalRecord({ id: Date.now().toString(36)+Math.random().toString(36).slice(2), ts: Date.now(), sessionId, user: text, assistant: data.content });
    renderHistory();
  } catch (e) {
    addMessage('assistant', '网络异常或后端未启动');
  }
});

// 初始提示
addMessage('assistant', '你好，我在这里以温暖、无评判的方式陪伴你。你可以先用几个词描述此刻的状态，并给一个 1–10 的强度评分；或选择做一次 1 分钟的呼吸稳定练习。');
renderHistory();