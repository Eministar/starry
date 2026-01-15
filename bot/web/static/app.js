const $ = (id) => document.getElementById(id);

function getToken() {
  return localStorage.getItem("starry_token") || "";
}
function setToken(t) {
  localStorage.setItem("starry_token", t);
}

function setStatus(ok, text) {
  const dot = $("statusDot");
  const label = $("statusText");
  dot.classList.remove("ok", "bad");
  dot.classList.add(ok ? "ok" : "bad");
  label.textContent = text;
}

function toast(msg) {
  const el = $("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2200);
}

async function api(path, opts = {}) {
  const token = getToken();
  if (!token) {
    throw new Error("Token fehlt");
  }
  const headers = Object.assign({}, opts.headers || {}, {
    "Authorization": "Bearer " + token
  });
  const res = await fetch(path, Object.assign({}, opts, { headers }));
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(res.status + " " + txt);
  }
  return res.json();
}

function formatDate(ts) {
  if (!ts) return "-";
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  return d.toLocaleString("de-DE");
}

function parseFields(raw) {
  const lines = (raw || "").split("\n").map(l => l.trim()).filter(Boolean);
  const out = [];
  for (const line of lines) {
    const parts = line.split("|");
    const name = (parts[0] || "").trim();
    const value = (parts[1] || "").trim();
    const inline = ((parts[2] || "").trim().toLowerCase() === "true");
    if (!name || !value) continue;
    out.push({ name, value, inline });
  }
  return out;
}

function setupTabs() {
  const buttons = document.querySelectorAll(".nav-btn");
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.tab;
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
      const panel = document.getElementById("tab-" + tab);
      if (panel) panel.classList.add("active");
    });
  });
}

async function loadSettings() {
  const s = await api("/api/settings");
  $("settings").value = JSON.stringify(s, null, 2);
  renderSnippets(s);
}

async function loadApplications() {
  const a = await api("/api/applications");
  $("applications").value = JSON.stringify(a, null, 2);
}

async function loadApplicationsList() {
  const list = await api("/api/applications/list?limit=100");
  const root = $("applicationsList");
  root.innerHTML = "";
  if (!list.length) {
    root.innerHTML = `<div class="list-item">Keine Bewerbungen.</div>`;
    return;
  }
  for (const row of list) {
    const div = document.createElement("div");
    div.className = "list-item";
    div.innerHTML = `<strong>#${row.id}</strong> · <code>${row.user_id}</code> · <code>${row.thread_id}</code><br><small>${row.status} · ${row.created_at}</small>`;
    root.appendChild(div);
  }
}

async function applyApplications() {
  const raw = $("applications").value.trim();
  const data = JSON.parse(raw);
  await api("/api/applications", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
}

async function applySettings() {
  const raw = $("settings").value.trim();
  const data = JSON.parse(raw);
  await api("/api/settings", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
  renderSnippets(data);
}

async function loadSummary() {
  const s = await api("/api/summary");
  $("mOpen").textContent = s.open ?? 0;
  $("mClaimed").textContent = s.claimed ?? 0;
  $("mClosed").textContent = s.closed ?? 0;
  $("mTotal").textContent = s.total ?? 0;
  $("lastSync").textContent = "letzter Sync: " + new Date().toLocaleTimeString("de-DE");
}

function statusBadge(status) {
  if (status === "closed") return { text: "geschlossen", cls: "closed" };
  if (status === "claimed") return { text: "geclaimed", cls: "claimed" };
  return { text: "offen", cls: "open" };
}

function ticketMatches(t, query, filter) {
  const q = (query || "").toLowerCase();
  if (filter !== "all" && t.status !== filter) return false;
  if (!q) return true;
  return (
    String(t.id).includes(q) ||
    String(t.user_id).includes(q) ||
    String(t.thread_id).includes(q) ||
    String(t.claimed_by || "").includes(q)
  );
}

function renderTickets(list) {
  const el = $("tickets");
  const query = $("ticketSearch").value.trim();
  const filter = $("ticketFilter").value;
  el.innerHTML = "";

  const rows = list.filter(t => ticketMatches(t, query, filter));
  if (!rows.length) {
    el.innerHTML = `<div class="ticket"><small>Keine Treffer.</small></div>`;
    return;
  }

  for (const t of rows) {
    const badge = statusBadge(t.status);
    const div = document.createElement("div");
    div.className = "ticket";
    div.innerHTML = `
      <div class="ticket-row">
        <span class="badge ${badge.cls}">${badge.text} · #${t.id}</span>
        <small>erstellt: ${formatDate(t.created_at)}</small>
      </div>
      <div><strong>User:</strong> <code>${t.user_id}</code></div>
      <div><strong>Thread:</strong> <code>${t.thread_id}</code></div>
      <div><strong>Claimed by:</strong> <code>${t.claimed_by || "-"}</code></div>
      <div><strong>Rating:</strong> <code>${t.rating || "-"}</code></div>
    `;
    el.appendChild(div);
  }
}

let ticketCache = [];
async function loadTickets() {
  ticketCache = await api("/api/tickets?limit=200");
  renderTickets(ticketCache);
}

function renderSnippets(settings) {
  const root = $("snippets");
  const snippets = (settings && settings.ticket && settings.ticket.snippets) || {};
  const keys = Object.keys(snippets);
  root.innerHTML = "";
  if (!keys.length) {
    root.innerHTML = `<div class="snippet"><small>Keine Snippets konfiguriert.</small></div>`;
    return;
  }
  for (const k of keys) {
    const item = snippets[k] || {};
    const title = item.title || k;
    const body = item.body || "";
    const div = document.createElement("div");
    div.className = "snippet";
    div.innerHTML = `
      <div class="key"><strong>${title}</strong> · <code>${k}</code></div>
      <small>${body}</small>
    `;
    root.appendChild(div);
  }
}

async function loadLogs() {
  const list = await api("/api/logs?limit=200");
  const root = $("logs");
  root.innerHTML = "";
  if (!list.length) {
    root.innerHTML = `<div class="list-item">Keine Logs.</div>`;
    return;
  }
  for (const row of list) {
    const div = document.createElement("div");
    div.className = "list-item";
    div.innerHTML = `<strong>${row.event}</strong> · <small>${row.created_at}</small><br><code>${row.payload}</code>`;
    root.appendChild(div);
  }
}

let logSocket = null;
function connectLogs() {
  if (logSocket && logSocket.readyState === 1) return;
  const token = getToken();
  if (!token) return;
  const status = $("logsLiveStatus");
  status.textContent = "Verbinde…";
  logSocket = new WebSocket(`ws://${location.host}/ws/logs?token=${encodeURIComponent(token)}`);
  logSocket.onopen = () => { status.textContent = "Verbunden"; };
  logSocket.onclose = () => { status.textContent = "Getrennt"; };
  logSocket.onerror = () => { status.textContent = "Fehler"; };
  logSocket.onmessage = (ev) => {
    try {
      const row = JSON.parse(ev.data);
      const root = $("logs");
      const div = document.createElement("div");
      div.className = "list-item";
      div.innerHTML = `<strong>${row.event}</strong> · <small>${row.created_at}</small><br><code>${row.payload}</code>`;
      root.prepend(div);
    } catch (e) {
      /* ignore */
    }
  };
}

async function searchUsers() {
  const q = $("userSearchInput").value.trim();
  if (!q) return;
  const list = await api("/api/users/search?query=" + encodeURIComponent(q));
  const root = $("userSearchResults");
  root.innerHTML = "";
  if (!list.length) {
    root.innerHTML = `<div class="list-item">Keine Treffer.</div>`;
    return;
  }
  for (const row of list) {
    const div = document.createElement("div");
    div.className = "list-item";
    div.innerHTML = `<strong>${row.display_name}</strong> · <code>${row.id}</code>`;
    root.appendChild(div);
  }
}

async function loadLiveUsers() {
  const list = await api("/api/users/live?limit=50");
  const root = $("userLive");
  root.innerHTML = "";
  if (!list.length) {
    root.innerHTML = `<div class="list-item">Keine aktiven User.</div>`;
    return;
  }
  for (const row of list) {
    const div = document.createElement("div");
    div.className = "list-item";
    div.innerHTML = `<strong>${row.display_name}</strong> · <code>${row.id}</code><br><small>${row.status}</small>`;
    root.appendChild(div);
  }
}

async function postJson(path, payload) {
  return api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
}

async function refreshAll() {
  await loadSettings();
  await loadTickets();
  await loadSummary();
  await loadApplications();
  await loadApplicationsList();
  await loadLiveUsers();
}

async function testToken() {
  await loadSummary();
  setStatus(true, "Verbunden");
  toast("Token ok");
}

setupTabs();

$("token").value = getToken();
$("saveToken").onclick = () => {
  setToken($("token").value.trim());
  toast("Token gespeichert");
};
$("testToken").onclick = () => testToken().catch(e => setStatus(false, "Fehler: " + e.message));

$("reload").onclick = () => loadSettings().then(() => toast("Settings geladen")).catch(e => alert(e.message));
$("apply").onclick = () => applySettings().then(() => toast("Gespeichert. Bot übernimmt das automatisch.")).catch(e => alert(e.message));
$("prettify").onclick = () => {
  try {
    const obj = JSON.parse($("settings").value);
    $("settings").value = JSON.stringify(obj, null, 2);
    toast("Formatiert");
  } catch (e) {
    alert("JSON ungültig");
  }
};
$("appsReload").onclick = () => loadApplications().then(() => toast("Bewerbungen geladen")).catch(e => alert(e.message));
$("appsApply").onclick = () => applyApplications().then(() => toast("Bewerbungen gespeichert")).catch(e => alert(e.message));
$("appsListReload").onclick = () => loadApplicationsList().then(() => toast("Bewerbungen aktualisiert")).catch(e => alert(e.message));

$("ticketsReload").onclick = () => loadTickets().then(() => toast("Tickets aktualisiert")).catch(e => alert(e.message));
$("snippetsReload").onclick = () => loadSettings().then(() => toast("Snippets aktualisiert")).catch(e => alert(e.message));
$("ticketSearch").oninput = () => renderTickets(ticketCache);
$("ticketFilter").onchange = () => renderTickets(ticketCache);
$("logsReload").onclick = () => loadLogs().then(() => toast("Logs geladen")).catch(e => alert(e.message));
$("logsLive").onclick = () => connectLogs();
$("userSearchBtn").onclick = () => searchUsers().catch(e => alert(e.message));
$("userLiveReload").onclick = () => loadLiveUsers().then(() => toast("Live User geladen")).catch(e => alert(e.message));

$("sendMessage").onclick = () => postJson("/api/discord/message", {
  channel_id: $("msgChannelId").value.trim(),
  content: $("msgContent").value.trim()
}).then(() => toast("Nachricht gesendet")).catch(e => alert(e.message));

$("sendEmbed").onclick = () => postJson("/api/discord/embed", {
  channel_id: $("embedChannelId").value.trim(),
  title: $("embedTitle").value.trim(),
  description: $("embedDesc").value.trim(),
  color: $("embedColor").value.trim(),
  footer: $("embedFooter").value.trim(),
  thumbnail: $("embedThumbnail").value.trim(),
  image: $("embedImage").value.trim(),
  fields: parseFields($("embedFields").value)
}).then(() => toast("Embed gesendet")).catch(e => alert(e.message));

$("timeoutBtn").onclick = () => postJson("/api/moderation/timeout", {
  user_id: $("timeoutUserId").value.trim(),
  moderator_id: $("timeoutModeratorId").value.trim(),
  minutes: $("timeoutMinutes").value.trim(),
  reason: $("timeoutReason").value.trim()
}).then(() => toast("Timeout gesetzt")).catch(e => alert(e.message));

$("kickBtn").onclick = () => postJson("/api/moderation/kick", {
  user_id: $("kickUserId").value.trim(),
  moderator_id: $("kickModeratorId").value.trim(),
  reason: $("kickReason").value.trim()
}).then(() => toast("User gekickt")).catch(e => alert(e.message));

$("banBtn").onclick = () => postJson("/api/moderation/ban", {
  user_id: $("banUserId").value.trim(),
  moderator_id: $("banModeratorId").value.trim(),
  delete_days: $("banDays").value.trim(),
  reason: $("banReason").value.trim()
}).then(() => toast("User gebannt")).catch(e => alert(e.message));

$("purgeBtn").onclick = () => postJson("/api/moderation/purge", {
  channel_id: $("purgeChannelId").value.trim(),
  moderator_id: $("purgeModeratorId").value.trim(),
  amount: $("purgeAmount").value.trim(),
  user_id: $("purgeUserId").value.trim()
}).then(res => toast("Purge: " + res.deleted)).catch(e => alert(e.message));

$("roleAddBtn").onclick = () => postJson("/api/roles/add", {
  user_id: $("roleAddUserId").value.trim(),
  role_id: $("roleAddRoleId").value.trim()
}).then(() => toast("Rolle hinzugefügt")).catch(e => alert(e.message));

$("roleRemoveBtn").onclick = () => postJson("/api/roles/remove", {
  user_id: $("roleRemoveUserId").value.trim(),
  role_id: $("roleRemoveRoleId").value.trim()
}).then(() => toast("Rolle entfernt")).catch(e => alert(e.message));

$("ticketActionBtn").onclick = () => postJson("/api/tickets/action", {
  thread_id: $("ticketThreadId").value.trim(),
  actor_id: $("ticketActorId").value.trim(),
  user_id: $("ticketUserId").value.trim(),
  action: $("ticketAction").value,
  reason: $("ticketReason").value.trim()
}).then(() => toast("Ticket Aktion ausgeführt")).catch(e => alert(e.message));

refreshAll().then(() => setStatus(true, "Verbunden")).catch(() => setStatus(false, "Token fehlt oder API offline"));
