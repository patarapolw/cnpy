//@ts-check

import { api } from "../api.js";
import { openItem, searchComponent, searchVoc, speak } from "../util.js";

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
    api.new_window(
      a.href,
      a.innerText,
      a.href.includes("levels.html") ? { maximized: true } : null
    );
  };
});

ctxmenu.attach(".nav", [
  {
    text: "Update CC-CEDICT",
    action: () => api.update_dict(),
  },
]);

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
  await api.update_custom_lists();

  await Promise.all([
    api.due_vocab_list().then((r) => {
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
    api.get_stats().then((r) => {
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
                {
                  text: "Search",
                  action: () => searchVoc(c),
                },
              ],
              {
                onShow: () => el.classList.add("hover"),
                onHide: () => el.classList.remove("hover"),
                attributes: { lang: "zh-CN" },
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

      api.decompose(Array.from(hanziSet)).then((result) => {
        Object.entries(result).map(([c, rs]) => {
          ctxmenu.update(`[data-hanzi="${c}"]`, [
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
            {
              text: "Search",
              action: () => searchVoc(c),
            },
            {
              text: "Build",
              action: () => searchComponent(c),
            },
            {
              text: "Decompose",
              subMenu: rs.map((r) => ({
                text: r,
                subMenu: [
                  {
                    text: "Open",
                    action: () => openItem(r),
                  },
                  {
                    text: "Build",
                    action: () => searchComponent(r),
                  },
                ],
              })),
            },
          ]);
        });
      });
    }),
  ]);

  reloadQueue = null;
}
