/* =========================================================
   術語卡 Term Cards — 全站唯一程式（首頁與主題頁共用）
   - 只讀取 topics/*.json，不寫死任何術語內容。
   - 一律用 textContent 建立 DOM，不把 JSON 內容當 HTML 插入。
   ========================================================= */
(function () {
  "use strict";

  var SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  var ACCENTS = ["blue", "purple", "amber", "green", "rose", "teal"];
  var QUIZ_KEY = "term-cards:quiz";

  /* ---------- 共用小工具 ---------- */

  function $(id) { return document.getElementById(id); }

  // 建立元素：el("p", { class: "x", text: "內容" }, [子元素...])
  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (key) {
        var value = attrs[key];
        if (value === undefined || value === null || value === false) return;
        if (key === "text") node.textContent = value;
        else if (key === "class") node.className = value;
        else node.setAttribute(key, value === true ? "" : value);
      });
    }
    (children || []).forEach(function (child) {
      if (child === null || child === undefined || child === false) return;
      node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
    });
    return node;
  }

  function fetchJSON(path) {
    return fetch(path, { cache: "no-cache" }).then(function (res) {
      if (!res.ok) {
        var err = new Error("HTTP " + res.status + "：" + path);
        err.status = res.status;
        throw err;
      }
      return res.json();
    });
  }

  function setStatus(message, isError) {
    var node = $("status");
    if (!node) return;
    node.textContent = message || "";
    node.classList.toggle("status--error", !!isError);
  }

  // 讀取失敗時的說明：直接雙擊開檔（file://）是最常見原因
  function loadErrorMessage(err) {
    if (location.protocol === "file:") {
      return "讀不到資料：請不要直接雙擊開啟 HTML，改用本機伺服器（python3 -m http.server 8000），再開啟 http://localhost:8000/。";
    }
    return "讀取資料失敗（" + (err && err.message ? err.message : "未知錯誤") + "）。";
  }

  function safeAccent(value) {
    return ACCENTS.indexOf(value) >= 0 ? value : null;
  }

  function normalize(text) {
    return String(text || "").toLowerCase().normalize("NFKC").trim();
  }

  function escapeRegExp(text) {
    return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  // 卡片錨點 id：term-<小寫英數與連字號>
  function termId(term) {
    var base = normalize(term).replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    return "term-" + (base || "x");
  }

  function storageGet(key) {
    try { return window.localStorage.getItem(key); } catch (e) { return null; }
  }

  function storageSet(key, value) {
    try { window.localStorage.setItem(key, value); } catch (e) { /* 無痕模式等情況忽略 */ }
  }

  // 「/」快速聚焦搜尋框
  function bindSlashShortcut(input) {
    document.addEventListener("keydown", function (event) {
      if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey) return;
      var tag = (document.activeElement && document.activeElement.tagName) || "";
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      event.preventDefault();
      input.focus();
    });
  }

  // 把文字中符合 pattern 的部分包成 <mark>
  function highlight(text, pattern) {
    var frag = document.createDocumentFragment();
    if (!pattern) { frag.appendChild(document.createTextNode(text)); return frag; }
    var last = 0;
    String(text).replace(pattern, function (match, offset) {
      if (offset > last) frag.appendChild(document.createTextNode(text.slice(last, offset)));
      frag.appendChild(el("mark", { text: match }));
      last = offset + match.length;
      return match;
    });
    if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
    return frag;
  }

  // 例句中標示術語本身（可含複數形）
  function termPattern(term) {
    var t = escapeRegExp(String(term));
    var variants = [t + "(?:s|es)?"];
    if (/[^aeiou]y$/i.test(term)) variants.push(escapeRegExp(term.slice(0, -1)) + "ies");
    try {
      return new RegExp("(?<![A-Za-z0-9])(?:" + variants.join("|") + ")(?![A-Za-z0-9])", "gi");
    } catch (e) {
      return null; // 舊瀏覽器不支援 lookbehind 時就不標示，不影響顯示
    }
  }

  function searchText(term) {
    return normalize([term.term, term.full, term.zh, term.explain, term.note].join(" "));
  }

  function countLabel(topic) {
    var n = Array.isArray(topic.terms) ? topic.terms.length : 0;
    return n + " 張卡";
  }

  /* =========================================================
     首頁
     ========================================================= */
  function initHome() {
    var grid = $("topics");
    var results = $("results");
    var input = $("search");
    var loaded = []; // [{ slug, accent, data }]

    fetchJSON("topics/index.json")
      .then(function (list) {
        if (!Array.isArray(list)) throw new Error("topics/index.json 必須是陣列");
        var entries = list.filter(function (item) { return item && SLUG_RE.test(item.slug); });

        if (entries.length === 0) {
          setStatus("");
          grid.appendChild(el("div", { class: "empty" }, [
            el("p", { text: "還沒有任何主題。" }),
            el("p", {}, ["複製 ", el("code", { text: "templates/topic-template.json" }),
              " 到 ", el("code", { text: "topics/" }), "，並登記在 ",
              el("code", { text: "topics/index.json" }), "。"])
          ]));
          return;
        }

        return Promise.all(entries.map(function (item) {
          return fetchJSON("topics/" + item.slug + ".json")
            .then(function (data) { return { slug: item.slug, accent: safeAccent(item.accent), data: data }; })
            .catch(function (err) { return { slug: item.slug, accent: safeAccent(item.accent), error: err }; });
        })).then(function (topics) {
          setStatus("");
          topics.forEach(function (topic) {
            grid.appendChild(topicCard(topic));
            if (topic.data) loaded.push(topic);
          });
          input.disabled = false;
          bindSlashShortcut(input);
          input.addEventListener("input", function () { renderResults(input.value); });
        });
      })
      .catch(function (err) { setStatus(loadErrorMessage(err), true); });

    function topicCard(topic) {
      if (topic.error) {
        return el("div", { class: "topic-card topic-card--error", "data-accent": topic.accent }, [
          el("p", { class: "topic-card__en", text: topic.slug }),
          el("p", { class: "topic-card__desc", text: "這個主題讀取失敗：" + topic.error.message })
        ]);
      }
      var d = topic.data;
      return el("a", {
        class: "topic-card",
        href: "topic.html?t=" + encodeURIComponent(topic.slug),
        "data-accent": topic.accent
      }, [
        el("p", { class: "topic-card__en", text: d.title_en || topic.slug }),
        el("h2", { class: "topic-card__title", text: d.title_zh || topic.slug }),
        d.description ? el("p", { class: "topic-card__desc", text: d.description }) : null,
        el("p", { class: "topic-card__meta" }, [
          el("span", { text: countLabel(d) }),
          d.updated ? el("span", { text: "更新 " + d.updated }) : null
        ])
      ]);
    }

    function renderResults(rawQuery) {
      var q = normalize(rawQuery);
      results.textContent = "";
      if (!q) {
        results.hidden = true;
        grid.hidden = false;
        setStatus("");
        return;
      }
      var hits = [];
      loaded.forEach(function (topic) {
        (topic.data.terms || []).forEach(function (term) {
          if (searchText(term).indexOf(q) >= 0) hits.push({ topic: topic, term: term });
        });
      });

      grid.hidden = true;
      results.hidden = false;
      setStatus(hits.length ? "找到 " + hits.length + " 張卡" : "找不到符合「" + rawQuery.trim() + "」的術語。");

      hits.forEach(function (hit) {
        results.appendChild(el("a", {
          class: "result",
          href: "topic.html?t=" + encodeURIComponent(hit.topic.slug) + "#" + termId(hit.term.term),
          "data-accent": hit.topic.accent
        }, [
          el("span", {}, [
            el("span", { class: "result__term", text: hit.term.term }),
            hit.term.full ? el("span", { class: "result__full", text: hit.term.full }) : null
          ]),
          el("span", { class: "result__zh", text: hit.term.zh || "" }),
          el("span", { class: "result__topic", text: hit.topic.data.title_zh || hit.topic.slug })
        ]));
      });
    }
  }

  /* =========================================================
     主題頁：topic.html?t=<slug>
     ========================================================= */
  function initTopic() {
    var slug = new URLSearchParams(location.search).get("t") || "";
    var list = $("cards");
    var input = $("search");
    var quizBtn = $("quiz-toggle");
    var shuffleBtn = $("quiz-shuffle");
    var resetBtn = $("quiz-reset");
    var progress = $("quiz-progress");
    var cards = []; // [{ node, text, revealed }]

    if (!SLUG_RE.test(slug)) {
      setStatus(slug ? "主題代號「" + slug + "」格式不正確。" : "網址缺少主題代號，例如 topic.html?t=network。", true);
      return;
    }

    Promise.all([
      fetchJSON("topics/" + slug + ".json"),
      fetchJSON("topics/index.json").catch(function () { return []; })
    ]).then(function (pair) {
      var topic = pair[0];
      var index = Array.isArray(pair[1]) ? pair[1] : [];
      var entry = index.filter(function (item) { return item && item.slug === slug; })[0];
      var accent = entry ? safeAccent(entry.accent) : null;
      if (accent) document.body.setAttribute("data-accent", accent);

      renderHeader(topic);
      renderCards(topic);
      setStatus("");
      $("toolbar").hidden = false;
      setupSearch();
      setupQuiz();
      jumpToHash();
    }).catch(function (err) {
      if (err && err.status === 404) setStatus("找不到主題「" + slug + "」。", true);
      else setStatus(loadErrorMessage(err), true);
    });

    function renderHeader(topic) {
      document.title = (topic.title_zh || slug) + "｜術語卡 Term Cards";
      $("topic-en").textContent = topic.title_en || "";
      $("topic-zh").textContent = topic.title_zh || slug;
      $("topic-desc").textContent = topic.description || "";
      $("topic-meta").textContent = countLabel(topic) + (topic.updated ? "・更新 " + topic.updated : "");
      $("topic-header").hidden = false;
    }

    function renderCards(topic) {
      var terms = Array.isArray(topic.terms) ? topic.terms : [];
      if (terms.length === 0) {
        list.appendChild(el("div", { class: "empty" }, [el("p", { text: "這個主題還沒有術語卡。" })]));
        return;
      }

      // 建立 term → 錨點 id 的對照（related 用，大小寫不敏感）
      var idOf = {};
      var used = {};
      terms.forEach(function (t) {
        var id = termId(t.term);
        while (used[id]) id += "-2";
        used[id] = true;
        idOf[normalize(t.term)] = id;
      });

      terms.forEach(function (t) {
        var node = termCard(t, idOf[normalize(t.term)], idOf);
        list.appendChild(node);
        var entry = { node: node, text: searchText(t), revealed: false };
        cards.push(entry);
        node.addEventListener("click", function (event) {
          if (!document.body.classList.contains("is-quiz")) return;
          if (event.target.closest("a")) return; // 點 related 連結時不要翻卡
          toggleReveal(entry);
        });
      });
    }

    function termCard(t, id, idOf) {
      var related = Array.isArray(t.related) ? t.related : [];
      return el("article", { class: "card", id: id }, [
        el("header", { class: "card__head" }, [
          el("h2", { class: "card__term", lang: "en", text: t.term }),
          t.full ? el("p", { class: "card__full", lang: "en", text: t.full }) : null,
          el("p", { class: "card__zh", text: t.zh || "" })
        ]),
        el("div", { class: "card__body" }, [
          t.explain ? el("p", { class: "card__explain", text: t.explain }) : null,
          t.example ? el("div", { class: "card__example" }, [
            el("span", { class: "card__label", text: "例句" }),
            el("p", { class: "card__example-en", lang: "en" }, [highlight(t.example, termPattern(t.term))]),
            t.example_zh ? el("p", { class: "card__example-zh", text: t.example_zh }) : null
          ]) : null,
          t.note ? el("p", { class: "card__note", text: t.note }) : null,
          related.length ? el("div", { class: "card__related" }, [el("span", { class: "card__label", text: "相關" })]
            .concat(related.map(function (name) {
              var target = idOf[normalize(name)];
              return target
                ? el("a", { class: "chip", href: "#" + target, lang: "en", text: name })
                : el("span", { class: "chip", lang: "en", text: name });
            }))) : null
        ]),
        el("button", { class: "btn card__flip", type: "button", "aria-expanded": "false", text: "翻開" })
      ]);
    }

    function setupSearch() {
      bindSlashShortcut(input);
      input.addEventListener("input", function () {
        var q = normalize(input.value);
        var shown = 0;
        cards.forEach(function (c) {
          var match = !q || c.text.indexOf(q) >= 0;
          c.node.hidden = !match;
          if (match) shown++;
        });
        setStatus(q && shown === 0 ? "找不到符合「" + input.value.trim() + "」的術語。" : "");
        updateProgress();
      });
    }

    function setupQuiz() {
      quizBtn.addEventListener("click", function () {
        setQuiz(!document.body.classList.contains("is-quiz"));
      });
      resetBtn.addEventListener("click", function () {
        cards.forEach(function (c) { setRevealed(c, false); });
        updateProgress();
      });
      shuffleBtn.addEventListener("click", function () {
        var order = cards.slice();
        for (var i = order.length - 1; i > 0; i--) {
          var j = Math.floor(Math.random() * (i + 1));
          var tmp = order[i]; order[i] = order[j]; order[j] = tmp;
        }
        order.forEach(function (c) { setRevealed(c, false); list.appendChild(c.node); });
        updateProgress();
      });
      setQuiz(storageGet(QUIZ_KEY) === "1");
    }

    function setQuiz(on) {
      document.body.classList.toggle("is-quiz", on);
      quizBtn.setAttribute("aria-pressed", on ? "true" : "false");
      shuffleBtn.hidden = !on;
      resetBtn.hidden = !on;
      progress.hidden = !on;
      if (!on) {
        // 離開測驗模式時恢復原本順序
        cards.forEach(function (c) { setRevealed(c, false); list.appendChild(c.node); });
      }
      storageSet(QUIZ_KEY, on ? "1" : "0");
      updateProgress();
    }

    function setRevealed(c, value) {
      c.revealed = value;
      c.node.classList.toggle("is-revealed", value);
      var btn = c.node.querySelector(".card__flip");
      if (btn) {
        btn.textContent = value ? "蓋回" : "翻開";
        btn.setAttribute("aria-expanded", value ? "true" : "false");
      }
    }

    function toggleReveal(c) {
      setRevealed(c, !c.revealed);
      updateProgress();
    }

    function updateProgress() {
      if (!document.body.classList.contains("is-quiz")) return;
      var visible = cards.filter(function (c) { return !c.node.hidden; });
      var revealed = visible.filter(function (c) { return c.revealed; }).length;
      progress.textContent = "已翻開 " + revealed + " / " + visible.length + " 張。先想中文意思，再點卡片確認。";
    }

    // 從網址 #term-xxx 進來時，捲到那張卡並短暫標示
    function jumpToHash() {
      window.addEventListener("hashchange", flashTarget);
      flashTarget();
    }

    function flashTarget() {
      var id = decodeURIComponent(location.hash.slice(1));
      if (!id) return;
      var node = document.getElementById(id);
      if (!node || !node.classList.contains("card")) return;
      if (node.hidden) { input.value = ""; input.dispatchEvent(new Event("input")); }
      node.classList.remove("is-target");
      void node.offsetWidth; // 重新觸發動畫
      node.classList.add("is-target");
      node.scrollIntoView({ block: "start" });
    }
  }

  /* ---------- 進入點 ---------- */
  var page = document.body.getAttribute("data-page");
  if (page === "home") initHome();
  else if (page === "topic") initTopic();
})();
