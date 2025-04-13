//@ts-check

import { api } from "../api.js";
import { openInModal } from "../modal.js";
import { openItem, searchPinyin, searchVoc, speak } from "../util.js";

const elButtonSubmit = /** @type {HTMLButtonElement} */ (
  document.querySelector('button[type="submit"]')
);
const elButtonReset = /** @type {HTMLButtonElement} */ (
  document.querySelector('button[type="reset"]')
);

const elAnalyzer = /** @type {HTMLElement} */ (
  document.querySelector("#analyzer")
);
const elResult = /** @type {HTMLElement} */ (document.querySelector("#result"));

const elFilter = /** @type {HTMLInputElement} */ (
  document.querySelector("#filter")
);
const elIsShowPinyin = /** @type {HTMLInputElement} */ (
  document.querySelector("#show-pinyin")
);
const elIsExcludeKnownHanzi = /** @type {HTMLInputElement} */ (
  document.querySelector("#exclude-known-hanzi")
);
const elIsNamesOnly = /** @type {HTMLInputElement} */ (
  document.querySelector("#names-only")
);

document.querySelectorAll('a[target="modal"]').forEach((a) => {
  if (!(a instanceof HTMLAnchorElement)) return;
  a.onclick = (ev) => {
    ev.preventDefault();
    openInModal(a.href, a.innerText.split(" ")[0]);
  };
});

/** @type {{ v: string; pinyin: string }[]} */
let allItems = [];

elButtonSubmit.addEventListener("click", async (ev) => {
  ev.preventDefault();

  const { result } = await api.analyze(
    elAnalyzer.querySelector("textarea").value
  );
  allItems = result;
  elFilter.value = "";

  document
    .querySelectorAll("fieldset")
    .forEach((el) => el.classList.remove("active"));

  elResult.classList.add("active");

  filterItems();
});

elButtonReset.addEventListener("click", (ev) => {
  ev.preventDefault();

  elAnalyzer.querySelector("textarea").value = "";

  document
    .querySelectorAll("fieldset")
    .forEach((el) => el.classList.remove("active"));

  elAnalyzer.classList.add("active");
});

elFilter.addEventListener("input", (ev) => {
  ev.preventDefault();
  if (!/^\p{sc=Han}*$/u.test(elFilter.value)) return;
  filterItems();
});

/** @type {Set<string>} */
let knownHanzi = null;
elIsExcludeKnownHanzi.addEventListener("change", async (ev) => {
  if (!knownHanzi) {
    const stats = await api.get_stats();
    knownHanzi = new Set(stats.all);
  }
  filterItems();
});

elIsShowPinyin.addEventListener("change", (ev) => {
  const ol = elResult.querySelector("ol");
  ol.classList.toggle("hide-pinyin", !elIsShowPinyin.checked);
});

elIsNamesOnly.addEventListener("change", (ev) => {
  filterItems();
});

async function filterItems() {
  const ol = elResult.querySelector("ol");
  ol.textContent = "";

  /**
   *
   * @param {(typeof allItems)[0]} r
   * @returns
   */
  const makeLI = (r) => {
    const li = document.createElement("li");
    li.lang = "zh-CN";
    li.setAttribute("data-v", r.v);

    const elPinyin = document.createElement("span");
    elPinyin.className = "pinyin";
    elPinyin.innerText = r.pinyin;

    li.append(r.v, elPinyin);

    setTimeout(() => {
      ctxmenu.update(
        `[data-v="${r.v}"]`,
        [
          {
            text: "🔊",
            action: (ev) => {
              ev.stopImmediatePropagation();
              speak(r.v);
            },
          },
          {
            text: "Open",
            action: () => openItem(r.v),
          },
          {
            text: `*${r.v}*`,
            action: () => searchVoc(r.v),
          },
          {
            text: "Similar",
            action: () => searchPinyin(r.v, r.pinyin.split("; ")),
          },
        ],
        {
          attributes: { lang: "zh-CN" },
        }
      );
    });

    return li;
  };

  let items = elFilter.value.trim()
    ? allItems.filter((r) => r.v.includes(elFilter.value))
    : allItems;

  if (elIsExcludeKnownHanzi.checked) {
    items = items.filter((r) => {
      return Array.from(r.v).some((c) => !knownHanzi.has(c));
    });
  }

  if (elIsNamesOnly.checked) {
    items = items.filter((r) => /^[A-Z]/.test(r.pinyin));
  }

  ol.append(...items.map((r) => makeLI(r)));
}
