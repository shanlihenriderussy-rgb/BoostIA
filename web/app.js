(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const templateSelect = $("template");
  const templateDesc = $("template-desc");
  const toneGroup = $("tone-group");
  const contextEl = $("context");
  const goBtn = $("go");
  const copyBtn = $("copy");
  const clearBtn = $("clear");
  const resultEl = $("result");
  const statusEl = $("status");
  const modelPicker = $("model-picker");
  const themeToggle = $("theme-toggle");

  const API_BASE = "";
  const THEME_KEY = "boostia.theme";
  const MODEL_KEY = "boostia.model";
  const MARKDOWN_TEMPLATES = new Set(["compte_rendu"]);

  let abortController = null;
  let templatesById = {};
  let currentTone = "neutre";
  let currentModel = null; // null = utiliser le default backend
  let rawText = "";

  // ---------- Theme ----------

  const initTheme = () => {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved === "light" || saved === "dark") {
      document.documentElement.dataset.theme = saved;
    } else {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      document.documentElement.dataset.theme = prefersDark ? "dark" : "light";
    }
  };

  themeToggle.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem(THEME_KEY, next);
  });

  // ---------- Tone chips ----------

  toneGroup.addEventListener("click", (e) => {
    const chip = e.target.closest(".tone-chip");
    if (!chip || chip.disabled) return;
    toneGroup.querySelectorAll(".tone-chip").forEach((c) => {
      const active = c === chip;
      c.classList.toggle("active", active);
      c.setAttribute("aria-checked", active ? "true" : "false");
    });
    currentTone = chip.dataset.value;
  });

  // ---------- UI helpers ----------

  const setStatus = (msg, kind = "default") => {
    statusEl.textContent = msg;
    statusEl.classList.remove("error", "success");
    if (kind === "error") statusEl.classList.add("error");
    if (kind === "success") statusEl.classList.add("success");
  };

  const setBusy = (busy) => {
    goBtn.disabled = busy;
    goBtn.classList.toggle("loading", busy);
    templateSelect.disabled = busy;
    contextEl.disabled = busy;
    modelPicker.disabled = busy;
    toneGroup.querySelectorAll(".tone-chip").forEach((c) => (c.disabled = busy));
  };

  const updateTemplateDescription = () => {
    const t = templatesById[templateSelect.value];
    templateDesc.textContent = t ? t.description : "";
  };

  const showPlaceholder = () => {
    resultEl.classList.remove("rendered", "streaming");
    resultEl.classList.add("empty");
    resultEl.innerHTML = `
      <div class="placeholder">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <p>Le texte généré apparaîtra ici.</p>
      </div>`;
  };

  const renderResult = (text, { streaming }) => {
    resultEl.classList.remove("empty");
    resultEl.classList.toggle("streaming", streaming);

    const id = templateSelect.value;
    if (!streaming && MARKDOWN_TEMPLATES.has(id) && window.marked) {
      resultEl.classList.add("rendered");
      window.marked.setOptions({ gfm: true, breaks: false });
      resultEl.innerHTML = window.marked.parse(text);
    } else {
      resultEl.classList.remove("rendered");
      resultEl.textContent = text;
    }
  };

  // ---------- API loads ----------

  const loadTemplates = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/templates`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const list = await res.json();
      templateSelect.innerHTML = "";
      templatesById = {};
      for (const t of list) {
        templatesById[t.id] = t;
        const opt = document.createElement("option");
        opt.value = t.id;
        opt.textContent = t.label;
        opt.title = t.description;
        templateSelect.appendChild(opt);
      }
      updateTemplateDescription();
    } catch (e) {
      setStatus("Impossible de charger les templates : " + e.message, "error");
    }
  };

  const loadModels = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/models`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const available = Array.isArray(data.available) ? data.available : [];
      const defaultId = data.default || (available[0] && available[0].id) || "";

      modelPicker.innerHTML = "";
      for (const m of available) {
        const opt = document.createElement("option");
        opt.value = m.id;
        opt.textContent = m.label;
        opt.title = m.description || m.id;
        modelPicker.appendChild(opt);
      }

      // Restore le choix utilisateur s'il est encore valide, sinon prendre le default
      const saved = localStorage.getItem(MODEL_KEY);
      const ids = available.map((m) => m.id);
      if (saved && ids.includes(saved)) {
        currentModel = saved;
      } else if (ids.includes(defaultId)) {
        currentModel = defaultId;
      } else if (ids.length > 0) {
        currentModel = ids[0];
      } else {
        currentModel = null;
      }
      if (currentModel) modelPicker.value = currentModel;
    } catch (e) {
      modelPicker.innerHTML = '<option value="">indisponible</option>';
      modelPicker.disabled = true;
    }
  };

  modelPicker.addEventListener("change", () => {
    currentModel = modelPicker.value || null;
    if (currentModel) {
      localStorage.setItem(MODEL_KEY, currentModel);
      setStatus(`Modèle actif : ${modelPicker.options[modelPicker.selectedIndex].textContent}`, "success");
    }
  });

  // ---------- Generation (SSE streaming) ----------

  const generate = async () => {
    const context = contextEl.value.trim();
    if (!context) {
      setStatus("Veuillez fournir un contexte avant de générer.", "error");
      contextEl.focus();
      return;
    }

    rawText = "";
    showPlaceholder();
    copyBtn.disabled = true;
    clearBtn.disabled = true;
    setStatus("Connexion au modèle…");
    setBusy(true);

    abortController = new AbortController();
    const started = performance.now();
    let firstTokenAt = null;
    let charCount = 0;
    let fatalError = null;

    const handleEvent = (rawEvent) => {
      let eventType = "message";
      const dataLines = [];
      for (const line of rawEvent.split("\n")) {
        if (!line || line.startsWith(":")) continue;
        if (line.startsWith("event:")) eventType = line.slice(6).trim();
        else if (line.startsWith("data:")) dataLines.push(line.slice(5).replace(/^ /, ""));
      }
      const data = dataLines.join("\n");
      if (!data) return;

      let parsed;
      try { parsed = JSON.parse(data); } catch { return; }

      if (eventType === "error") {
        fatalError = parsed.error || "Erreur inconnue";
        return;
      }
      if (eventType === "done") return;

      if (typeof parsed.delta === "string") {
        if (firstTokenAt === null) {
          firstTokenAt = performance.now();
          setStatus("Génération en cours…", "success");
        }
        rawText += parsed.delta;
        charCount += parsed.delta.length;
        renderResult(rawText, { streaming: true });
      }
    };

    try {
      const body = {
        template_id: templateSelect.value,
        context,
        tone: currentTone,
      };
      if (currentModel) body.model = currentModel;

      const res = await fetch(`${API_BASE}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: abortController.signal,
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status} — ${text}`);
      }
      if (!res.body) throw new Error("Streaming non supporté par ce navigateur.");

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let sepIdx;
        while ((sepIdx = buffer.indexOf("\n\n")) !== -1) {
          const evt = buffer.slice(0, sepIdx);
          buffer = buffer.slice(sepIdx + 2);
          handleEvent(evt);
        }
      }
      if (buffer.trim()) handleEvent(buffer);
    } catch (e) {
      if (e.name === "AbortError") setStatus("Génération interrompue.");
      else setStatus("Erreur : " + e.message, "error");
    } finally {
      setBusy(false);
      abortController = null;

      if (fatalError) {
        setStatus("Erreur du modèle : " + fatalError, "error");
      } else if (rawText.length > 0) {
        renderResult(rawText, { streaming: false });
        copyBtn.disabled = false;
        clearBtn.disabled = false;
        const elapsed = ((performance.now() - started) / 1000).toFixed(1);
        const ttft = firstTokenAt ? ((firstTokenAt - started) / 1000).toFixed(2) : "?";
        setStatus(`${charCount} caractères en ${elapsed}s — premier token : ${ttft}s`, "success");
      } else {
        showPlaceholder();
      }
    }
  };

  // ---------- Wiring ----------

  templateSelect.addEventListener("change", updateTemplateDescription);
  goBtn.addEventListener("click", generate);

  copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(rawText);
      setStatus("Copié dans le presse-papiers.", "success");
    } catch {
      setStatus("Copie impossible (autorisations navigateur).", "error");
    }
  });

  clearBtn.addEventListener("click", () => {
    rawText = "";
    showPlaceholder();
    copyBtn.disabled = true;
    clearBtn.disabled = true;
    setStatus("");
  });

  contextEl.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter" && !goBtn.disabled) {
      e.preventDefault();
      generate();
    }
  });

  initTheme();
  loadTemplates();
  loadModels();
})();
