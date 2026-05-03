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
  const exportPdfBtn = $("export-pdf");
  const exportMdBtn = $("export-md");
  const resultEl = $("result");
  const statusEl = $("status");
  const modelPicker = $("model-picker");
  const themeToggle = $("theme-toggle");
  const refineShortBtn = $("refine-short");
  const refineFormalBtn = $("refine-formal");

  const API_BASE = "";
  const THEME_KEY = "boostia.theme";
  const MODEL_KEY = "boostia.model.v2";
  const MARKDOWN_TEMPLATES = new Set(["compte_rendu"]);

  let abortController = null;
  let templatesById = {};
  let currentTone = "neutre";
  let currentModel = null;
  let rawText = "";
  let progressMessagesInterval = null;

  // Messages de progression contextués par modèle
  const PROGRESS_MESSAGES = {
    "qwen2.5:7b-instruct": [
      "🧠 Qwen 7B démarre…",
      "📝 Analyse du contexte…",
      "✨ Rédaction…",
      "🔍 Révision…",
      "🎯 Finalisation…",
    ],
    "qwen2.5:3b-instruct": [
      "⚡ Qwen accélère…",
      "📝 Structuration…",
      "✨ Affinage…",
      "🎯 Finalisation…",
      "💫 Prêt !",
    ],
    "phi4:latest": [
      "🧠 Phi 4 démarre…",
      "📚 Lecture contextuelle…",
      "🎨 Création…",
      "🔍 Révision…",
      "✅ Finalisation…",
      "💎 Optimisation…",
    ],
    default: [
      "⏳ Génération…",
      "📖 Traitement…",
      "💡 Création…",
      "🔄 Vérification…",
      "🌟 Finalisation…",
    ],
  };

  // Intervalles de progression par modèle (en ms) — BIEN PLUS LONG
  const PROGRESS_INTERVALS = {
    "qwen2.5:3b-instruct": 2200,
    "qwen2.5:7b-instruct": 3000,
    "phi4:latest": 3600,
    default: 2800,
  };

  const progressMessagesEl = $("progress-messages");
  let progressMessageIndex = 0;

  const startProgressMessages = () => {
    progressMessageIndex = 0;
    progressMessagesEl.classList.add("active");
    progressMessagesEl.innerHTML = "";

    const modelKey = currentModel && PROGRESS_MESSAGES[currentModel] ? currentModel : "default";
    const messages = PROGRESS_MESSAGES[modelKey];
    const interval = PROGRESS_INTERVALS[modelKey] || PROGRESS_INTERVALS.default;

    progressMessagesInterval = setInterval(() => {
      const msg = messages[progressMessageIndex];
      progressMessagesEl.innerHTML = `<div class="progress-message info">${msg}</div>`;
      progressMessageIndex = (progressMessageIndex + 1) % messages.length;
    }, interval);
  };

  const stopProgressMessages = () => {
    if (progressMessagesInterval) {
      clearInterval(progressMessagesInterval);
      progressMessagesInterval = null;
    }
    progressMessagesEl.classList.remove("active");
    progressMessagesEl.innerHTML = "";
  };

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
    refineShortBtn.disabled = busy || !rawText;
    refineFormalBtn.disabled = busy || !rawText;
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

  const showLoadingScreen = (modelName) => {
    resultEl.classList.remove("rendered", "streaming", "empty");
    resultEl.innerHTML = `
      <div class="loading-screen">
        <div class="loading-spinner"></div>
        <div class="loading-text">Connexion à <strong>${modelName}</strong>…</div>
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
      const saved = localStorage.getItem(MODEL_KEY);
      const ids = available.map((m) => m.id);
      if (saved && ids.includes(saved)) currentModel = saved;
      else if (ids.includes(defaultId)) currentModel = defaultId;
      else if (ids.length > 0) currentModel = ids[0];
      else currentModel = null;
      if (currentModel) modelPicker.value = currentModel;
    } catch {
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

  // ---------- SSE common reader ----------
  // onDelta(text) called for each text chunk.
  // Returns { fatalError, charCount, firstTokenAt } when stream ends.
  const consumeSseStream = async (response, onDelta) => {
    let fatalError = null;
    let charCount = 0;
    let firstTokenAt = null;

    if (!response.body) throw new Error("Streaming non supporté par ce navigateur.");
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

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
        if (firstTokenAt === null) firstTokenAt = performance.now();
        charCount += parsed.delta.length;
        onDelta(parsed.delta);
      }
    };

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

    return { fatalError, charCount, firstTokenAt };
  };

  // ---------- Generation (SSE) ----------
  const generate = async () => {
    const context = contextEl.value.trim();
    if (!context) {
      setStatus("Veuillez fournir un contexte avant de générer.", "error");
      contextEl.focus();
      return;
    }

    rawText = "";
    const modelLabel = modelPicker.selectedOptions[0]?.text || currentModel || "modèle";
    showLoadingScreen(modelLabel);
    copyBtn.disabled = true;
    clearBtn.disabled = true;
    exportPdfBtn.disabled = true;
    exportMdBtn.disabled = true;
    setStatus("Connexion au modèle…");
    setBusy(true);

    abortController = new AbortController();
    const started = performance.now();

    try {
      const body = { template_id: templateSelect.value, context, tone: currentTone };
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

      startProgressMessages();

      const onDelta = (delta) => {
        if (statusEl.textContent === "Connexion au modèle…") {
          setStatus("Génération en cours…", "success");
        }
        rawText += delta;
        renderResult(rawText, { streaming: true });
      };

      const { fatalError, charCount, firstTokenAt } = await consumeSseStream(res, onDelta);

      stopProgressMessages();

      if (fatalError) {
        setStatus("Erreur du modèle : " + fatalError, "error");
      } else if (rawText.length > 0) {
        renderResult(rawText, { streaming: false });
        copyBtn.disabled = false;
        clearBtn.disabled = false;
        exportPdfBtn.disabled = false;
        exportMdBtn.disabled = false;
        const elapsed = ((performance.now() - started) / 1000).toFixed(1);
        const ttft = firstTokenAt ? ((firstTokenAt - started) / 1000).toFixed(2) : "?";
        setStatus(`${charCount} car. en ${elapsed}s — premier token : ${ttft}s`, "success");
      } else {
        showPlaceholder();
      }
    } catch (e) {
      stopProgressMessages();
      if (e.name === "AbortError") setStatus("Génération interrompue.");
      else setStatus("Erreur : " + e.message, "error");
    } finally {
      setBusy(false);
      abortController = null;
    }
  };

  // ---------- Refine (SSE) — REMPLACE le texte au lieu d'ajouter ----------
  const refineOutput = async (instruction) => {
    if (!rawText) return;

    const previous = rawText;
    rawText = "";
    const modelLabel = modelPicker.selectedOptions[0]?.text || currentModel || "modèle";
    showLoadingScreen(modelLabel);
    setStatus("Reformulation en cours…");
    setBusy(true);

    abortController = new AbortController();
    const started = performance.now();

    try {
      const body = { output: previous, instruction };
      if (currentModel) body.model = currentModel;

      const res = await fetch(`${API_BASE}/api/refine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: abortController.signal,
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status} — ${text}`);
      }

      startProgressMessages();

      const onDelta = (delta) => {
        rawText += delta;
        renderResult(rawText, { streaming: true });
      };

      const { fatalError, charCount } = await consumeSseStream(res, onDelta);

      stopProgressMessages();

      if (fatalError) {
        // Restaure le texte précédent en cas d'erreur
        rawText = previous;
        renderResult(rawText, { streaming: false });
        setStatus("Erreur de reformulation : " + fatalError, "error");
      } else if (rawText.length > 0) {
        renderResult(rawText, { streaming: false });
        const elapsed = ((performance.now() - started) / 1000).toFixed(1);
        setStatus(`Reformulé : ${charCount} car. en ${elapsed}s`, "success");
      } else {
        // Aucun delta reçu : on remet l'original
        rawText = previous;
        renderResult(rawText, { streaming: false });
        setStatus("Reformulation vide, texte original conservé.", "error");
      }
    } catch (e) {
      stopProgressMessages();
      // Restaure en cas d'exception réseau
      rawText = previous;
      renderResult(rawText, { streaming: false });
      if (e.name === "AbortError") setStatus("Reformulation interrompue, texte original conservé.");
      else setStatus("Erreur : " + e.message, "error");
    } finally {
      setBusy(false);
      abortController = null;
    }
  };

  // ---------- Wiring ----------
  templateSelect.addEventListener("change", updateTemplateDescription);
  goBtn.addEventListener("click", generate);
  refineShortBtn.addEventListener("click", () => refineOutput("plus_court"));
  refineFormalBtn.addEventListener("click", () => refineOutput("plus_formel"));

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
    exportPdfBtn.disabled = true;
    exportMdBtn.disabled = true;
    refineShortBtn.disabled = true;
    refineFormalBtn.disabled = true;
    setStatus("");
  });

  const buildFilename = (ext) => {
    const id = templateSelect.value || "boostia";
    const stamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    return `boostia-${id}-${stamp}.${ext}`;
  };

  exportMdBtn.addEventListener("click", () => {
    if (!rawText) return;
    const blob = new Blob([rawText], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = buildFilename("md");
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setStatus("Markdown exporté.", "success");
  });

  const buildPdfWrapper = (text, templateId, templateLabel) => {
    const isMd = MARKDOWN_TEMPLATES.has(templateId) && window.marked;
    const bodyHtml = isMd
      ? window.marked.parse(text)
      : `<pre style="white-space:pre-wrap;font-family:inherit;margin:0;font-size:11pt;line-height:1.65;color:#0a1f12;">${text.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c])}</pre>`;

    const today = new Date().toLocaleDateString("fr-FR", {
      day: "numeric", month: "long", year: "numeric",
    });

    const wrapper = document.createElement("div");
    wrapper.style.cssText = "width:794px;background:#f1f8f3;font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#0a1f12;padding:0;margin:0;";

    wrapper.innerHTML = `
      <div style="padding:32px 36px 24px 36px;background:linear-gradient(135deg,#16a34a 0%,#15803d 100%);color:#ecfdf5;">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:16px;">
          <div>
            <div style="font-size:11pt;letter-spacing:2px;text-transform:uppercase;opacity:0.85;font-weight:500;">BoostIA</div>
            <div style="font-size:22pt;font-weight:700;margin-top:4px;letter-spacing:-0.5px;">${templateLabel}</div>
          </div>
          <div style="text-align:right;font-size:9.5pt;opacity:0.9;line-height:1.5;">
            <div style="font-weight:600;">${today}</div>
            <div style="opacity:0.75;margin-top:2px;">Genere localement</div>
          </div>
        </div>
      </div>

      <div style="padding:32px 36px 28px 36px;">
        <div style="background:#ffffff;border:1px solid rgba(22,163,74,0.16);border-radius:14px;box-shadow:0 4px 16px rgba(6,95,70,0.08);padding:32px 36px;position:relative;">
          <div style="position:absolute;top:0;left:24px;right:24px;height:3px;background:linear-gradient(90deg,#4ade80,#16a34a,#84cc16);border-radius:0 0 4px 4px;"></div>
          <div class="boostia-pdf-content" style="font-size:11.5pt;line-height:1.7;color:#0a1f12;">
            ${bodyHtml}
          </div>
        </div>

        <div style="margin-top:20px;padding:14px 20px;background:rgba(22,163,74,0.06);border-left:3px solid #16a34a;border-radius:6px;font-size:9pt;color:#4d6b58;line-height:1.5;">
          <strong style="color:#15803d;">Confidentialite :</strong> document genere localement par BoostIA.
          Aucune donnee n'a transite par un serveur externe.
        </div>
      </div>

      <div style="padding:16px 36px 24px 36px;text-align:center;font-size:8.5pt;color:#88a596;border-top:1px solid rgba(22,163,74,0.10);margin-top:8px;">
        BoostIA — Assistant de redaction professionnelle 100% local
      </div>
    `;

    const style = document.createElement("style");
    style.textContent = `
      .boostia-pdf-content h1 { font-size:18pt;color:#15803d;margin:0 0 16px 0;font-weight:700;letter-spacing:-0.3px;border-bottom:2px solid rgba(22,163,74,0.20);padding-bottom:8px; }
      .boostia-pdf-content h2 { font-size:13pt;color:#16a34a;margin:22px 0 10px 0;font-weight:600;text-transform:uppercase;letter-spacing:0.5px; }
      .boostia-pdf-content h3 { font-size:11.5pt;color:#15803d;margin:18px 0 8px 0;font-weight:600; }
      .boostia-pdf-content p { margin:0 0 12px 0; }
      .boostia-pdf-content ul, .boostia-pdf-content ol { margin:0 0 14px 0;padding-left:22px; }
      .boostia-pdf-content li { margin:4px 0; }
      .boostia-pdf-content strong { color:#15803d;font-weight:600; }
      .boostia-pdf-content em { color:#4d6b58; }
      .boostia-pdf-content code { background:rgba(22,163,74,0.08);padding:1px 6px;border-radius:4px;font-family:'JetBrains Mono',Consolas,monospace;font-size:10pt;color:#15803d; }
      .boostia-pdf-content blockquote { border-left:3px solid #4ade80;margin:0 0 14px 0;padding:4px 16px;color:#4d6b58;font-style:italic;background:rgba(74,222,128,0.06);border-radius:0 6px 6px 0; }
    `;
    wrapper.appendChild(style);
    return wrapper;
  };

  exportPdfBtn.addEventListener("click", async () => {
    if (!rawText) return;
    if (!window.html2pdf) {
      setStatus("html2pdf indisponible (vérifiez votre connexion CDN).", "error");
      return;
    }
    const id = templateSelect.value;
    const tpl = templatesById[id];
    const label = tpl ? tpl.label : "Document";

    const wrapper = buildPdfWrapper(rawText, id, label);
    // html2canvas a besoin d'un element rendu avec opacite normale.
    // Astuce : transform translate pour le sortir visuellement de l'ecran
    // sans toucher a l'opacite ni a la visibilite (qui casseraient le rendu).
    wrapper.style.position = "absolute";
    wrapper.style.top = "0";
    wrapper.style.left = "0";
    wrapper.style.transform = "translateX(-120%)";
    wrapper.style.zIndex = "-1";
    wrapper.style.pointerEvents = "none";
    document.body.appendChild(wrapper);

    setStatus("Génération du PDF…");
    // Laisser un tick au navigateur pour appliquer les styles
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));

    try {
      await window.html2pdf()
        .set({
          margin: 0,
          filename: buildFilename("pdf"),
          image: { type: "jpeg", quality: 0.95 },
          html2canvas: {
            scale: 2,
            useCORS: true,
            backgroundColor: "#f1f8f3",
            windowWidth: 794,
            scrollY: 0,
          },
          jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
          pagebreak: { mode: ["css", "legacy"] },
        })
        .from(wrapper)
        .save();
      setStatus("PDF exporté.", "success");
    } catch (e) {
      setStatus("Erreur PDF : " + e.message, "error");
    } finally {
      if (wrapper.parentNode) wrapper.parentNode.removeChild(wrapper);
    }
  });

  contextEl.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter" && !goBtn.disabled) {
      e.preventDefault();
      generate();
    }
  });

  // ---------- Hero : smooth scroll vers l'atelier ----------
  const heroCta = $("hero-cta");
  const atelier = $("atelier");
  if (heroCta && atelier) {
    heroCta.addEventListener("click", () => {
      atelier.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  // ---------- Parallax & reveal au scroll ----------
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (!prefersReducedMotion) {
    const heroInner = document.querySelector(".hero-inner");
    const heroHint = document.querySelector(".hero-scroll-hint");

    if (heroInner) {
      let ticking = false;
      const updateParallax = () => {
        const y = window.scrollY;
        const heroHeight = window.innerHeight;
        // Le contenu hero remonte (translate -y/3) et fade jusqu'a 70 % de sa hauteur
        const progress = Math.min(y / (heroHeight * 0.7), 1);
        heroInner.style.transform = `translateY(${-y / 3}px)`;
        heroInner.style.opacity = String(1 - progress);
        if (heroHint) heroHint.style.opacity = String(Math.max(0.5 - y / 200, 0));
        ticking = false;
      };
      window.addEventListener("scroll", () => {
        if (!ticking) {
          requestAnimationFrame(updateParallax);
          ticking = true;
        }
      }, { passive: true });
    }

    // Reveal au scroll (cards de l'atelier)
    const revealEls = document.querySelectorAll(".reveal-on-scroll");
    if (revealEls.length && "IntersectionObserver" in window) {
      const obs = new IntersectionObserver((entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            obs.unobserve(entry.target);
          }
        }
      }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });
      revealEls.forEach((el) => obs.observe(el));
    } else {
      // Fallback : tout visible direct
      revealEls.forEach((el) => el.classList.add("is-visible"));
    }
  } else {
    // Reduced motion : tout immediatement visible, pas de parallax
    document.querySelectorAll(".reveal-on-scroll").forEach((el) => el.classList.add("is-visible"));
  }

  initTheme();
  loadTemplates();
  loadModels();
})();
