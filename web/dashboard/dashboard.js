//@ts-check

const elDueCount = /** @type {HTMLSpanElement} */ (
  document.getElementById("due-count")
);

const elLearnedCount = /** @type {HTMLSpanElement} */ (
  document.getElementById("learned-count")
);

const elHanziList = /** @type {HTMLDivElement} */ (
  document.getElementById("hanzi-list")
);

document.querySelectorAll('a[target="new_window"]').forEach((a) => {
  if (!(a instanceof HTMLAnchorElement)) return;
  a.onclick = (ev) => {
    ev.preventDefault();
    pywebview.api.new_window(
      a.href,
      a.innerText,
      a.href.includes("levels.html") ? { maximized: true } : null
    );
  };
});

let reloadQueue = null;

window.addEventListener("focus", () => {
  if (!reloadQueue) {
    reloadQueue = doLoading();
  }
});
window.addEventListener("pywebviewready", () => {
  reloadQueue = doLoading();
});

async function doLoading() {
  await pywebview.api.update_custom_lists();

  await Promise.all([
    pywebview.api.due_vocab_list().then((r) => {
      elDueCount.textContent = "";

      if (r.count) {
        const due = r.count - r.new;
        elDueCount.append(document.createTextNode(` (${due || ""}`));

        if (r.new) {
          const s = document.createElement("small");
          s.innerText = `+${r.new}`;
          elDueCount.append(s);
        }

        elDueCount.append(document.createTextNode(")"));
      }
    }),
    pywebview.api.get_stats().then((r) => {
      elHanziList.textContent = "";

      const hanziSet = new Set();

      [r.h5, r.lone, r.h3].forEach((s, i) => {
        if (!s) return;
        const className = `hanzi tier-${i}`;

        for (const c of s) {
          if (!hanziSet.has(c)) {
            hanziSet.add(c);

            const el = document.createElement("span");
            el.innerText = c;
            el.className = className;
            el.setAttribute("data-hanzi", c);
            el.addEventListener("mouseenter", () => {
              ctxmenu.hide();
            });

            elHanziList.append(el);

            ctxmenu.update(
              `[data-hanzi="${c}"]`,
              [
                {
                  text: "🔊",
                  action: (ev) => {
                    ev.stopImmediatePropagation();
                    speak(c);
                  },
                },
                {
                  text: "Open",
                  action: () => openItem(c),
                },
              ],
              {
                onShow: () => el.classList.add("hover"),
                onHide: () => el.classList.remove("hover"),
              }
            );
          }
        }
      });

      elLearnedCount.lang = "zh-CN";
      elLearnedCount.innerText = [
        `汉字: ${hanziSet.size}`,
        `生词: ${r.good}` +
          (r.accuracy ? ` (${(r.accuracy * 100).toFixed(0)}%)` : ""),
      ].join(", ");
    }),
  ]);

  reloadQueue = null;
}

const utterance = new SpeechSynthesisUtterance();
utterance.lang = "zh-CN";

/**
 *
 * @param {string} s
 */
function speak(s) {
  utterance.text = s;
  speechSynthesis.speak(utterance);
}

/**
 *
 * @param {string} v
 */
async function openItem(v) {
  const r = await pywebview.api.set_vocab(v);
  if (r) {
    pywebview.api.new_window("./quiz.html", v);
  } else {
    alert(`Cannot open vocab: ${v}`);
  }
}
