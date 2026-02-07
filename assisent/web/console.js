const apiKeyEl = document.getElementById('apiKey');
const statusEl = document.getElementById('status');
const servicesEl = document.getElementById('services');
const statsEl = document.getElementById('stats');
const logsEl = document.getElementById('logs');
const svcEl = document.getElementById('svc');
const methodEl = document.getElementById('method');
const pathEl = document.getElementById('path');
const payloadEl = document.getElementById('payload');
const invokeBtn = document.getElementById('invoke');
const themeToggle = document.getElementById('theme-toggle');

function getHeaders() {
  const h = { 'Content-Type': 'application/json' };
  const k = apiKeyEl.value.trim();
  if (k) h['X-API-Key'] = k;
  return h;
}

async function loadServices() {
  try {
    const r = await fetch('/mcp/services', { headers: getHeaders() });
    if (!r.ok) throw new Error('unauthorized');
    const data = await r.json();
    const frag = document.createDocumentFragment();
    Object.entries(data).forEach(([name, cfg]) => {
      const div = document.createElement('div');
      div.className = 'service';
      const eps = (cfg.endpoints||[]).map(e=>`${e.url}${e.health_path||''}`).join('\n');
      div.innerHTML = `<strong>${name}</strong><pre>${eps}</pre>`;
      div.addEventListener('click', ()=>{ svcEl.value = name; });
      frag.appendChild(div);
    });
    servicesEl.innerHTML = '';
    servicesEl.appendChild(frag);
    statusEl.textContent = '服务已加载';
  } catch (e) {
    statusEl.textContent = '无法加载服务';
  }
}

async function loadStats() {
  try {
    const r = await fetch('/mcp/stats', { headers: getHeaders() });
    if (!r.ok) throw new Error('unauthorized');
    const data = await r.json();
    const frag = document.createDocumentFragment();
    Object.entries(data.services||{}).forEach(([name, s]) => {
      const div = document.createElement('div');
      div.className = 'stat';
      div.textContent = `${name} 请求=${s.requests} 错误=${s.errors} 平均延迟=${s.avg_latency_ms}ms`;
      frag.appendChild(div);
    });
    statsEl.innerHTML = '';
    statsEl.appendChild(frag);
    logsEl.textContent = JSON.stringify((data.recent||[]).slice(-50), null, 2);
  } catch (e) {}
}

invokeBtn.addEventListener('click', async ()=>{
  const body = {
    service: svcEl.value.trim(),
    method: methodEl.value,
    path: pathEl.value.trim() || '/health',
    payload: (()=>{ try { return JSON.parse(payloadEl.value||'{}'); } catch(e) { return {}; } })()
  };
  try {
    const r = await fetch('/mcp/call', { method: 'POST', headers: getHeaders(), body: JSON.stringify(body) });
    const data = await r.json();
    document.getElementById('result').textContent = JSON.stringify(data, null, 2);
    loadStats();
  } catch (e) {
    document.getElementById('result').textContent = '调用失败';
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

loadServices();
loadStats();
setInterval(loadStats, 2000);