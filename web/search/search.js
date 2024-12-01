//@ts-check

import { api } from "../api.js";
import { openItem, searchPinyin, speak } from "../util.js";

const elForm = document.querySelector("form");
const elInput = elForm.querySelector("input");
const ol = document.querySelector("ol");

elForm.addEventListener("submit", (ev) => {
  ev.preventDefault();
  parseInput();
});

const u = new URL(location.href);
const q = u.searchParams.get("q");
if (q) {
  elInput.value = q;
  parseInput();
}

async function parseInput() {
  const q = elInput.value;
  let obj = { voc: "", pinyin: q };

  try {
    obj = JSON.parse(q);
  } catch (e) {}

  if (obj.pinyin) {
    obj.pinyin = obj.pinyin.replace(/([a-z:])( [^ ]|$)/gi, "$1\\d$2");

    if (obj.voc) {
      obj.pinyin = `(^|.* )${obj.pinyin}( .*|$)`;
    }
  }

  ol.textContent = "";

  const { result } = await api.search(obj);

  if (!result.length) {
    ol.textContent = "No results";
  }

  /**
   *
   * @param {(typeof result)[0]} r
   * @returns
   */
  const makeLI = (r) => {
    const li = document.createElement("li");
    li.lang = "zh-CN";
    li.setAttribute("data-v", r.v);

    li.append(r.v);

    if (!/\p{sc=Han}/u.test(r.v)) {
      return li;
    }

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

  ol.append(...result.map((r) => makeLI(r)));
}
