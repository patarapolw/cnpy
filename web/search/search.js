//@ts-check

import { api } from "../api.js";
import { openItem, searchPinyin, searchVoc, speak } from "../util.js";

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
  let obj = { v: "", c: "", p: "" };

  try {
    obj = JSON.parse(q);
  } catch (e) {}

  if (!obj.v && !obj.p) {
    if (/\p{sc=Han}/u.test(q)) {
      obj.v = q;
    } else {
      obj.p = q;
    }
  }

  if (obj.p) {
    if (obj.v || obj.c) {
      obj.p = `(^|.* )${obj.p}( .*|$)`;
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

    const elPinyin = document.createElement("span");
    elPinyin.className = "pinyin";
    elPinyin.innerText = r.pinyin || "";

    li.append(r.v, elPinyin);

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

  ol.append(...result.map((r) => makeLI(r)));
}
