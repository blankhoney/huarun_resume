const page = document.body.dataset.page;
const statusText = {
  pending: "待记录",
  taken: "已服",
  later: "稍后",
  missed: "漏服",
  unwell: "不适",
};

function $(selector) {
  return document.querySelector(selector);
}

async function jsonApi(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: {"Content-Type": "application/json", ...(options.headers || {})},
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "请求失败");
  }
  return payload;
}

function setMessage(selector, text) {
  const node = $(selector);
  if (node) node.textContent = text;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function redirectLogin(error) {
  if (String(error.message || "").includes("Login")) {
    window.location.href = "/login";
  }
}

if (page === "login") {
  $("#login-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await jsonApi("/api/auth/demo-login", {
        method: "POST",
        body: JSON.stringify({
          email: form.get("email"),
          password: form.get("password"),
        }),
      });
      window.location.href = "/";
    } catch (error) {
      setMessage("#login-message", error.message);
    }
  });
}

if (page === "upload") {
  const input = $("#image-input");
  const preview = $("#image-preview");
  input?.addEventListener("change", () => {
    const file = input.files?.[0];
    if (!file || !preview) return;
    preview.src = URL.createObjectURL(file);
    preview.hidden = false;
  });

  $("#upload-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = input?.files?.[0];
    if (!file) {
      setMessage("#upload-message", "请先选择图片。");
      return;
    }
    const data = new FormData();
    data.append("image", file);
    setMessage("#upload-message", "正在识别，请稍候。");
    try {
      const response = await fetch("/api/medicines/scan", {
        method: "POST",
        body: data,
        credentials: "same-origin",
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "识别失败");
      window.location.href = `/confirm/${payload.scan_id}`;
    } catch (error) {
      redirectLogin(error);
      setMessage("#upload-message", error.message);
    }
  });
}

if (page === "confirm") {
  const form = $("#confirm-form");
  const scanData = JSON.parse($("#scan-data")?.textContent || "{}");
  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const reminderTimes = data.getAll("reminder_time").filter(Boolean);
    try {
      const response = await jsonApi(`/api/medicines/${form.dataset.scanId}/confirm`, {
        method: "POST",
        body: JSON.stringify({
          drug_name: data.get("drug_name"),
          generic_name: data.get("generic_name"),
          specification: data.get("specification"),
          dose_text: data.get("dose_text"),
          warning_text: data.get("warning_text"),
          source_quotes: scanData.source_quotes || [],
          reminder_times: reminderTimes,
          confirmed: data.get("confirmed") === "on",
        }),
      });
      setMessage("#confirm-message", "已保存。正在进入电子药箱。");
      window.location.href = `/pillbox?medicine_id=${response.medicine_id}`;
    } catch (error) {
      setMessage("#confirm-message", error.message);
    }
  });
}

if (page === "pillbox") {
  loadPillbox();
}

async function loadPillbox() {
  const target = $("#pillbox-list");
  if (!target) return;
  try {
    const payload = await jsonApi("/api/pillbox");
    if (!payload.medicines.length) {
      target.innerHTML = '<div class="panel"><h2>还没有药品</h2><p>先拍照添加并人工确认。</p><a class="secondary-link" href="/upload">去添加</a></div>';
      return;
    }
    target.innerHTML = payload.medicines.map((medicine) => `
      <article class="panel medicine-card">
        ${medicine.image_url ? `<img class="medicine-photo" src="${escapeHtml(medicine.image_url)}" alt="${escapeHtml(medicine.drug_name)}">` : ""}
        <header>
          <div>
            <h2>${escapeHtml(medicine.drug_name)}</h2>
            <p class="notice">${escapeHtml(medicine.specification || "未填写规格")}</p>
          </div>
          <span class="tag green">已确认</span>
        </header>
        <p>${escapeHtml(medicine.dose_text || "未填写用法")}</p>
        <p class="notice">提醒：${escapeHtml(medicine.reminder_times.join("、") || "未设置")}</p>
        <div class="pill-actions">
          <a class="secondary-link" href="/reminders">今日提醒</a>
          <a class="secondary-link" href="/qa?medicine_id=${encodeURIComponent(medicine.medicine_id)}">问一问</a>
        </div>
      </article>
    `).join("");
  } catch (error) {
    redirectLogin(error);
    target.innerHTML = `<div class="panel"><p>${escapeHtml(error.message)}</p></div>`;
  }
}

if (page === "reminders") {
  startCountdown();
  loadReminders();
}

function startCountdown() {
  let seconds = 60;
  const node = $("#countdown-text");
  window.setInterval(() => {
    seconds = Math.max(0, seconds - 1);
    if (node) node.textContent = `Demo 提醒倒计时 ${seconds} 秒，可直接记录当前状态。`;
  }, 1000);
}

async function loadReminders() {
  const focus = $("#reminder-focus");
  const summary = $("#summary-list");
  if (!focus || !summary) return;
  try {
    const reminders = await jsonApi("/api/reminders/today");
    if (!reminders.reminders.length) {
      focus.innerHTML = '<h2>暂无提醒</h2><p>先添加并确认药品。</p><a class="secondary-link" href="/upload">去添加</a>';
    } else {
      const first = reminders.reminders[0];
      focus.innerHTML = `
        <p class="eyebrow">${escapeHtml(first.time_of_day)}</p>
        <h2>${escapeHtml(first.drug_name)}</h2>
        <p class="notice">当前状态：${escapeHtml(statusText[first.status] || first.status)}</p>
        <div class="status-grid" data-schedule-id="${escapeHtml(first.schedule_id)}">
          <button class="status-button taken" data-status="taken">已服</button>
          <button class="status-button later" data-status="later">稍后</button>
          <button class="status-button missed" data-status="missed">漏服</button>
          <button class="status-button unwell" data-status="unwell">不适</button>
        </div>
      `;
    }
    const recordButtons = focus.querySelectorAll("[data-status]");
    recordButtons.forEach((button) => {
      button.addEventListener("click", () => recordDose(button.dataset.status));
    });

    const recordSummary = await jsonApi("/api/records/summary?days=7");
    summary.innerHTML = recordSummary.days.map((day) => `
      <div class="summary-row">
        <span>${escapeHtml(day.date)}</span>
        <strong>已服 ${escapeHtml(day.taken)} / 稍后 ${escapeHtml(day.later)} / 漏服 ${escapeHtml(day.missed)} / 不适 ${escapeHtml(day.unwell)}</strong>
      </div>
    `).join("");
  } catch (error) {
    redirectLogin(error);
    focus.innerHTML = `<p>${escapeHtml(error.message)}</p>`;
  }
}

async function recordDose(status) {
  const grid = $(".status-grid");
  if (!grid) return;
  try {
    await jsonApi("/api/dose-records", {
      method: "POST",
      body: JSON.stringify({
        schedule_id: Number(grid.dataset.scheduleId),
        status,
        note: "",
      }),
    });
    await loadReminders();
  } catch (error) {
    alert(error.message);
  }
}

if (page === "qa") {
  setupQa();
}

function setupQa() {
  const params = new URLSearchParams(window.location.search);
  const selectedMedicine = params.get("medicine_id");
  if (selectedMedicine && $("#qa-medicine")) {
    $("#qa-medicine").value = selectedMedicine;
  }
  document.querySelectorAll("[data-question]").forEach((button) => {
    button.addEventListener("click", () => {
      $("#qa-question").value = button.dataset.question;
    });
  });
  $("#qa-submit")?.addEventListener("click", askQuestion);
}

async function askQuestion() {
  const question = $("#qa-question")?.value.trim();
  const medicineId = $("#qa-medicine")?.value;
  if (!question) {
    setMessage("#qa-message", "请先输入问题。");
    return;
  }
  setMessage("#qa-message", "正在生成回答。");
  try {
    const payload = {question};
    if (medicineId) payload.medicine_id = Number(medicineId);
    const answer = await jsonApi("/api/qa", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderAnswer(answer);
    setMessage("#qa-message", "");
  } catch (error) {
    setMessage("#qa-message", error.message);
  }
}

function renderAnswer(answer) {
  const target = $("#qa-answer");
  if (!target) return;
  const labelClass = answer.safety_label === "red" ? "red" : answer.safety_label === "yellow" ? "amber" : "green";
  target.hidden = false;
  target.innerHTML = `
    <span class="tag ${labelClass}">安全标签：${escapeHtml(answer.safety_label)}</span>
    <p class="answer-text">${escapeHtml(answer.answer)}</p>
    <h2>来源</h2>
    <ul class="source-list">
      ${(answer.sources || []).map((source) => `<li>${escapeHtml(source)}</li>`).join("") || "<li>无来源片段</li>"}
    </ul>
  `;
}
