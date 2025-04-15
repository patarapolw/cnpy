//@ts-check

import { api } from "../api.js";
import { openInModal } from "../modal.js";
import {
  comp_pinyin,
  openItem,
  searchPinyin,
  searchComponent,
  searchVoc,
  speak,
} from "../util.js";

/** @type {State} */
const state = {
  vocabList: [],
  i: 0,
  total: 20,
  max: 20,
  skip: 0,
  due: -1,
  new: 0,
  review_counter: 0,
  vocabDetails: { cedict: [], sentences: [], segments: [] },
  pendingList: [],
  lastIsRight: null,
  lastIsFuzzy: false,
  lastQuizTime: null,
  isRepeat: false,
};

/** @type {import("../../node_modules/ctxmenu/index").CTXMItem[][]} */
const oldVocabList = [];

const elRoot = document.getElementById("quiz");
const elStatus = document.getElementById("status");
const elVocab = /** @type {HTMLDivElement} */ (
  document.getElementById("vocab")
);
const elInput = /** @type {HTMLDivElement} */ (
  document.getElementById("type-input")
);
const elCompare = /** @type {HTMLAnchorElement} */ (
  document.getElementById("type-compare")
);
const elNotes = /** @type {HTMLDivElement} */ (
  document.getElementById("notes")
);
const elNotesTextarea = /** @type {HTMLTextAreaElement} */ (
  elNotes.querySelector("textarea")
);

elInput.addEventListener("keypress", (ev) => {
  switch (ev.key) {
    case "Enter":
      if (elInput.innerText) {
        doNext();
      }
      ev.preventDefault();
  }
});
elInput.addEventListener("paste", (ev) => {
  const { clipboardData } = ev;
  if (!clipboardData) return;

  if (clipboardData.getData("text/html")) {
    setTimeout(() => {
      const { innerText } = elInput;
      elInput.textContent = "";
      elInput.innerText = innerText;
    });
  }
});
elInput.focus();

elInput.addEventListener("keydown", (ev) => {
  switch (ev.key) {
    case "Enter":
      break;
    default:
      if (typeof state.lastIsRight === "boolean") {
        ev.preventDefault();

        if (ev.ctrlKey && ev.key === "z") {
          state.vocabList.push(...state.vocabList.splice(state.i, 1));
          state.i--;
          newVocab();
        }
      }
  }
});

document.querySelectorAll("#check-buttons-area button[name]").forEach((b) => {
  /** @type {HTMLButtonElement} */ (b).onclick = (ev) => {
    ev.preventDefault();
    const name = b.getAttribute("name");
    if (!name) return;
    mark(name);
  };
});

document.addEventListener("keydown", (ev) => {
  switch (ev.key) {
    case "Escape":
      if (state.mode === "show") return;
      if (state.isRepeat) {
        if (state.lastIsRight === true) {
          mark("repeat");
        }
      } else {
        if (typeof state.lastIsRight === "boolean") {
          mark("repeat");
        } else {
          state.skip++;

          const elTotal = /** @type {HTMLDivElement} */ (
            document.querySelector(".count[data-count-type='total']")
          );

          elTotal.innerText = (state.total - state.skip).toString();

          newVocab();
        }
      }
      break;
    case "F5":
    case "F1":
      if (state.mode === "show") return;
      if (!state.isRepeat) {
        state.review_counter -= state.max - state.i;
        newVocabList();
      }
  }
});

window.addEventListener("click", (ev) => {
  if (ev.target instanceof HTMLElement) {
    if (
      ["BUTTON", "SUMMARY", "A"].includes(ev.target.tagName.toLocaleUpperCase())
    ) {
      ev.target.blur();
    }
  }
});

ctxmenu.attach("#counter .right", [
  {
    text: "Add vocab list",
    action: () => openInModal("./list.html?f=vocab/vocab.txt", "Add"),
    style: "text-align: left",
  },
  {
    text: "Skip vocab list",
    action: () => openInModal("./list.html?f=skip/skip.txt", "Skip"),
    style: "text-align: left",
  },
  {
    text: "Update CC-CEDICT",
    action: () => api.update_dict(),
    style: "text-align: left",
  },
]);

const converter = new showdown.Converter({
  parseImgDimensions: true,
  tables: true,
  strikethrough: true,
  // openLinksInNewWindow: true,
  emoji: true,
});

elNotesTextarea.addEventListener("paste", (ev) => {
  const { clipboardData } = ev;

  if (!clipboardData) return;

  const html = clipboardData.getData("text/html");
  if (!html) return;

  const selection = window.getSelection();
  if (!selection?.rangeCount) return;

  ev.preventDefault();

  const div = document.createElement("div");
  div.innerHTML = html
    .replace(/<!--.*?-->/g, "")
    .replace(/&[a-z]{2,4};/gi, (p) => p.toLocaleLowerCase());
  div.innerHTML = div.innerHTML.trim();

  while (div.childElementCount === 1) {
    const n = div.childNodes.item(0);
    if (n instanceof HTMLDivElement) {
      div.innerHTML = n.innerHTML;
    } else {
      break;
    }
  }

  div.querySelectorAll("span").forEach((el) => {
    const style = el.getAttribute("style") || "";
    if (
      !el.hasAttribute("lang") &&
      !style.replace(/font-size:\s*100%;/g, "").trim()
    ) {
      el.replaceWith(...el.childNodes);
    }
  });

  div.querySelectorAll("div").forEach((el) => {
    if (!el.hasAttribute("lang") && !el.hasAttribute("style")) {
      if (
        ![...el.childNodes].some(
          (n) => n.nodeType === Node.TEXT_NODE || n instanceof HTMLSpanElement
        )
      ) {
        el.replaceWith(...el.childNodes);
      }
    }
  });

  div.querySelectorAll("*").forEach((el) => {
    el.removeAttribute("id");
    el.removeAttribute("class");
  });

  const md = converter
    .makeMarkdown(div.innerHTML)
    .replace(/<!--.*?-->/g, "")
    .replace(/([\p{Ps}\p{Pi}／]+)\s+</gu, "$1<")
    .replace(/>\s+([\p{Pe}\p{Pf}.。,，、／]+)/gu, ">$1")
    .replace(/(\r?\n)+ {1,3}([^ ])/g, " $2")
    .replace(/^(\r?\n)+/, "")
    .replace(/(\r?\n)+$/, "");

  const target = elNotesTextarea;

  target.setRangeText(md);
  target.selectionStart += md.length;
  target.blur();
  target.focus();
});

function setNotesTextAreaHeight() {
  const el = elNotesTextarea;
  el.style.height = "auto";
  el.style.height = `${el.scrollHeight}px`;
}

elNotes.querySelectorAll("button").forEach((b) => {
  switch (b.innerText) {
    case "Save":
      b.onclick = (ev) => {
        ev.preventDefault();
        makeNotes();

        elNotes.setAttribute("data-has-notes", "1");
      };
      break;
    case "Edit":
      b.onclick = (ev) => {
        ev.preventDefault();
        elNotes.setAttribute("data-has-notes", "");
        setNotesTextAreaHeight();
      };
  }
});

document.addEventListener("DOMContentLoaded", () => {
  newVocab();
});

////////////////
/// Functions
////////////////

function doNext(ev) {
  if (ev) {
    ev.preventDefault();
  }

  if (elCompare.innerText) {
    if (state.mode === "show") return;
    if (typeof state.lastIsRight === "boolean") {
      mark();
    }

    newVocab();
  } else {
    const currentItem = state.vocabList[state.i];

    const { v } = currentItem;
    const { segments, cedict } = state.vocabDetails;

    /** @type {Map<string, Set<string>>} */
    const hs = new Map();

    const dictPinyin = cedict
      .map((v) => v.pinyin)
      .filter((v, i, a) => a.indexOf(v) === i);

    for (const v of cedict) {
      if (!dictPinyin.includes(v.pinyin)) {
        dictPinyin.push(v.pinyin);
      }

      const pinyin = v.pinyin.split(" ");

      Array.from(v.simp).map((c, i) => {
        const ps = hs.get(c) || new Set();
        ps.add(pinyin[i]);
        hs.set(c, ps);
      });

      if (!v.trad) continue;

      Array.from(v.trad).map((c, i) => {
        const ps = hs.get(c) || new Set();
        ps.add(pinyin[i]);
        hs.set(c, ps);
      });
    }

    /**
     *
     * @param {Record<string, string[]>} rad
     * @returns
     */
    const makeCTXDef = (rad = {}) => {
      return [
        {
          text: "🔊",
          action: () => speak(v),
        },
        ...(v.length > 1 || cedict.some((v) => v.trad)
          ? Array.from(hs.entries()).map(([k, pset]) => {
              const ps = Array.from(pset);

              /** @type {import("../../node_modules/ctxmenu/index").CTXMItem} */
              const m = {
                text: k,
                subMenu: [
                  {
                    text: "🔊",
                    action: () => speak(k),
                  },
                  {
                    text: "Open",
                    action: () => openItem(k),
                  },
                  {
                    text: `*${k}*`,
                    action: () => searchVoc(k, ps),
                  },
                  {
                    text: "Build",
                    action: () => searchComponent(k, ps),
                  },
                  ...(rad[k]
                    ? [
                        {
                          text: "Decompose",
                          subMenu: rad[k].map((r) => ({
                            text: r,
                            subMenu: [
                              {
                                text: "Open",
                                action: () => openItem(r),
                              },
                              {
                                text: `*${r}*`,
                                action: () => searchVoc(r, ps),
                              },
                              {
                                text: "Build",
                                action: () => searchComponent(r, ps),
                              },
                            ],
                          })),
                        },
                      ]
                    : []),
                  {
                    text: "Similar",
                    action: () => searchPinyin(k, ps),
                  },
                ],
              };
              return m;
            })
          : [
              {
                text: "Build",
                action: () => searchComponent(v, dictPinyin),
              },
              ...(rad[v]
                ? [
                    {
                      text: "Decompose",
                      subMenu: rad[v].map((r) => ({
                        text: r,
                        subMenu: [
                          {
                            text: "Open",
                            action: () => openItem(r),
                          },
                          {
                            text: `*${r}*`,
                            action: () => searchVoc(r, dictPinyin),
                          },
                          {
                            text: "Build",
                            action: () => searchComponent(r, dictPinyin),
                          },
                        ],
                      })),
                    },
                  ]
                : []),
            ]),
        ...segments.map((k) => {
          /** @type {import("../../node_modules/ctxmenu/index").CTXMItem} */
          const m = {
            text: k,
            subMenu: [
              {
                text: "🔊",
                action: () => speak(k),
              },
              {
                text: "Open",
                action: () => openItem(k),
              },
              {
                text: `*${k}*`,
                action: () => searchVoc(k),
              },
            ],
          };
          return m;
        }),
        {
          text: `*${v}*`,
          action: () => searchVoc(v),
        },
        {
          text: "Similar",
          action: () => searchPinyin(v, dictPinyin),
        },
      ];
    };

    api.decompose(Array.from(hs.keys())).then((r) => {
      if (state.vocabList[state.i]?.v !== v) return;

      ctxmenu.update("#vocab", makeCTXDef(r));
    });

    ctxmenu.update("#vocab", makeCTXDef(), {
      attributes: { lang: "zh-CN" },
    });

    let { pinyin, mustPinyin, warnPinyin } = currentItem.data;
    pinyin = pinyin || dictPinyin;
    const inputPinyin = elInput.innerText.split(";").map((v) => v.trim());

    if (warnPinyin?.length) {
      if (inputPinyin.some((v) => warnPinyin.some((p) => comp_pinyin(p, v)))) {
        const txt = elInput.innerText;

        if (typeof state.lastIsRight === "boolean") {
          state.i--;
          newVocab();
        }

        elInput.innerText = txt;
        const attrName = "data-checked";
        elInput.setAttribute(attrName, "warn");
        setTimeout(() => {
          if (elInput.getAttribute(attrName) === "warn") {
            elInput.setAttribute(attrName, "");
          }
        }, 1000);

        return;
      }
    }

    elCompare.setAttribute(
      "data-pinyin-count",
      (
        new Set(dictPinyin.map((p) => p.toLocaleLowerCase())).size +
        (mustPinyin?.length || 0) +
        (warnPinyin?.length || 0)
      ).toString()
    );
    elCompare.href = `./pinyin-select.html?v=${currentItem.v}`;
    elCompare.onclick = (ev) => {
      ev.preventDefault();
      const a = elCompare;
      if (!a.href) return;

      const iframe = document.createElement("iframe");
      iframe.className = "pinyin-select-iframe";
      iframe.src = a.href;

      const modal = document.createElement("div");
      modal.className = "pinyin-select-modal";
      iframe.onload = () => {
        const updateHeight = () => {
          const newHeight = `${iframe.contentWindow.document.documentElement.scrollHeight}px`;
          modal.style.height = newHeight;
        };

        const observer = new MutationObserver(updateHeight);
        observer.observe(iframe.contentWindow.document.documentElement, {
          childList: true,
          subtree: true,
        });

        iframe.contentWindow.addEventListener("resize", updateHeight);
        modal.addEventListener("DOMNodeRemoved", () => observer.disconnect());
        updateHeight();
      };

      async function onModalClose() {
        document.body.removeChild(modal);
        document.body.removeChild(overlay);

        if (elCompare.innerText) {
          const { v } = state.vocabList[state.i];
          state.vocabList[state.i] = await api.get_vocab(v);

          softCleanup();
          doNext();
        }
      }

      const overlay = document.createElement("div");
      overlay.className = "pinyin-select-overlay";
      overlay.addEventListener("click", () => {
        onModalClose();
      });

      document.body.appendChild(overlay);

      const closeButton = document.createElement("button");
      closeButton.className = "pinyin-select-close-button";
      closeButton.innerText = "×";
      closeButton.addEventListener("click", () => {
        onModalClose();
      });

      modal.appendChild(iframe);
      modal.appendChild(closeButton);
      document.body.appendChild(modal);
    };

    elCompare.textContent = "";

    if (mustPinyin?.length) {
      const b = document.createElement("b");
      b.innerText = mustPinyin.join("; ").replace(/u:/g, "ü");
      elCompare.append(b);

      const remaining = pinyin
        .filter((p) => !mustPinyin.some((s) => comp_pinyin(s, p)))
        .join("; ")
        .replace(/u:/g, "ü");
      if (remaining) {
        elCompare.append("; " + remaining);
      }
    } else {
      elCompare.innerText = pinyin.join("; ").replace(/u:/g, "ü");
    }

    const elDictEntries = /** @type {HTMLDivElement} */ (
      document.getElementById("dictionary-entries")
    );
    {
      const elTemplate = Array.from(elDictEntries.childNodes).find(
        (el) => el instanceof HTMLTemplateElement
      );

      if (elTemplate) {
        elDictEntries.append(
          ...state.vocabDetails.cedict.map((v) => {
            const el = /** @type {HTMLElement} */ (
              elTemplate.content.cloneNode(true)
            );

            /** @type {HTMLDivElement} */ (
              el.querySelector(".simp")
            ).innerText = v.simp;
            /** @type {HTMLDivElement} */ (
              el.querySelector(".trad")
            ).innerText = v.trad || "";
            /** @type {HTMLDivElement} */ (
              el.querySelector(".pinyin")
            ).innerText = v.pinyin.replace(/u:/g, "ü");
            /** @type {HTMLDivElement} */ (el.querySelector(".english")).append(
              ...v.english.map((ens) => {
                const li = document.createElement("li");
                li.innerText = ens.join("; ");
                return li;
              })
            );

            return el;
          })
        );
      }
    }

    const elSentences = /** @type {HTMLDivElement} */ (
      document.getElementById("sentences")
    );
    elSentences.setAttribute(
      "data-sentence-count",
      state.vocabDetails.sentences.length.toString()
    );
    {
      const elTemplate = Array.from(elSentences.childNodes).find(
        (el) => el instanceof HTMLTemplateElement
      );

      if (elTemplate) {
        const ul = document.createElement("ul");
        ul.className = "if-checked-details";
        elSentences.append(ul);

        ul.append(
          ...state.vocabDetails.sentences.map((v) => {
            const el = /** @type {HTMLElement} */ (
              elTemplate.content.cloneNode(true)
            );

            /** @type {HTMLDivElement} */ (
              el.querySelector(".simp")
            ).innerText = v.cmn;

            if (v.eng) {
              /** @type {HTMLDivElement} */ (
                el.querySelector(".english")
              ).innerText = v.eng;
            } else {
              /** @type {HTMLUListElement} */ (el.querySelector("ul")).remove();
            }

            return el;
          })
        );
      }
    }

    if (
      elDictEntries instanceof HTMLDetailsElement &&
      elSentences instanceof HTMLDetailsElement
    ) {
      elDictEntries.open = false;
      elSentences.open = false;

      if (state.vocabDetails.sentences.length) {
        elSentences.open = true;
      } else {
        elDictEntries.open = true;
      }
    }

    state.lastIsFuzzy = false;
    state.lastIsRight = inputPinyin.every((v) =>
      pinyin.some((p) => comp_pinyin(p, v))
    );

    if (mustPinyin?.length) {
      state.lastIsRight =
        state.lastIsRight &&
        mustPinyin.every((v) => inputPinyin.some((p) => comp_pinyin(p, v)));
    }

    if (!state.lastIsRight) {
      if (
        elInput.innerText
          .split(";")
          .every((v) => pinyin.some((p) => comp_pinyin(p, v.trim(), true)))
      ) {
        state.lastIsFuzzy = true;
      }
    }

    document.querySelectorAll("[data-checked]").forEach((el) => {
      el.setAttribute("data-checked", state.lastIsRight ? "right" : "wrong");
    });

    elInput.innerText = elInput.innerText
      .replace(/u:/g, "v")
      .replace(/v/g, "ü");
    elInput.oninput = (ev) => {
      ev.preventDefault();
      return false;
    };
  }

  return false;
}

function mark(type) {
  if (type) {
    setTimeout(doNext);
  }
  elStatus.textContent = "";

  switch (type || state.lastIsRight) {
    case true:
      type = "right";
      break;
    case false:
      type = state.lastIsFuzzy ? "repeat" : "wrong";
      break;
  }
  type = type || "repeat";

  const el = /** @type {HTMLDivElement} */ (
    document.querySelector(`.count[data-count-type="${type}"]`)
  );
  const markCount = parseInt(el.innerText) + 1;

  el.innerText = markCount.toString();

  /** @type {HTMLDivElement} */ (
    document.querySelector(`#progress [data-count-type="${type}"]`)
  ).style.width = `${((markCount / (state.total - state.skip)) * 100).toFixed(
    1
  )}%`;

  const currentItem = state.vocabList[state.i];

  if (type !== "right") {
    state.pendingList.push(currentItem);
  }

  state.lastIsRight = null;

  if (!state.isRepeat) {
    api.mark(currentItem.v, type);
  }
}

function softCleanup() {
  elVocab.onclick = null;

  elCompare.innerText = "";
  elCompare.href = "";
  elCompare.onclick = () => false;

  document.querySelectorAll(".if-checked-details").forEach((el) => el.remove());
}

async function newVocab() {
  elInput.innerText = "";
  elInput.oninput = null;
  elInput.focus();

  softCleanup();

  state.i++;
  state.lastIsRight = null;

  if (state.pendingList.length >= 10 || state.i >= state.vocabList.length) {
    await newVocabList();
    return;
  }

  ctxmenu.update(
    "#counter .center",
    [
      ...state.vocabList
        .slice(0, state.i)
        .reverse()
        .map((s) => {
          /** @type {import("../../node_modules/ctxmenu/index").CTXMItem} */
          const m = {
            text: s.v,
            subMenu: [
              {
                text: "🔊",
                action: () => speak(s.v),
              },
              {
                text: "Open",
                action: () => openItem(s.v),
              },
              {
                text: `*${s.v}*`,
                action: () => searchVoc(s.v),
              },
            ],
          };
          return m;
        }),
      {
        text: "...",
        action: async () => {
          const v = prompt("Custom vocab:");
          if (!v) return;

          if (!/^\p{sc=Han}+$/u.test(v)) {
            alert(`Invalid vocab: ${v}`);
          }

          openItem(v);
        },
      },
      ...oldVocabList
        .map((ls, i) => ({
          text: `${i + 1}`,
          subMenu: ls,
        }))
        .reverse(),
    ],
    { attributes: { lang: "zh-CN" } }
  );
  ctxmenu.delete("#vocab");

  document.querySelectorAll("[data-checked]").forEach((el) => {
    el.setAttribute("data-checked", "");
  });

  const { v } = state.vocabList[state.i];

  state.vocabDetails = await api.vocab_details(v);
  elVocab.innerText = v;
  elVocab.onclick = null;

  document.querySelectorAll(".external-links a").forEach((a) => {
    if (!(a instanceof HTMLAnchorElement)) return;

    let href = a.getAttribute("data-href");
    if (!href) {
      a.setAttribute("data-href", a.href);
      href = a.href;
    }
    a.href = href.replace("__voc__", v);
  });

  elNotes.classList.remove("ready");

  const {
    data: { notes },
  } = await api.get_vocab(v);

  elNotesTextarea.value = notes || "";
  makeNotes({ skipSave: true });

  elNotes.setAttribute("data-has-notes", notes ? "1" : "");
  setNotesTextAreaHeight();

  elNotes.classList.add("ready");
}

async function newVocabList() {
  if (!state.isRepeat && state.vocabList.length > 0) {
    oldVocabList.push(
      state.vocabList
        .slice(0, state.i)
        .reverse()
        .map((s) => {
          /** @type {import("../../node_modules/ctxmenu/index").CTXMItem} */
          const m = {
            text: s.v,
            subMenu: [
              {
                text: "🔊",
                action: () => speak(s.v),
              },
              {
                text: "Open",
                action: () => openItem(s.v),
              },
              {
                text: `*${s.v}*`,
                action: () => searchVoc(s.v),
              },
            ],
          };
          return m;
        })
    );
  }

  state.i = -1;
  state.skip = 0;
  state.isRepeat = state.pendingList.length > 0;

  let customItemSRS;

  if (state.isRepeat) {
    state.vocabList = state.pendingList;
    state.pendingList = [];
  } else if (state.due) {
    const r = await api.due_vocab_list(state.review_counter);
    state.vocabList = r.result;
    state.due = r.count;
    state.new = r.new;
    state.review_counter += r.result.length;

    if (!state.mode) {
      customItemSRS = r.customItemSRS;

      state.mode = customItemSRS === undefined ? "standard" : "show";
      elRoot.setAttribute("data-type", state.mode);
    }

    if (r.count < 5 && state.lastQuizTime) {
      const d = new Date();
      d.setMinutes(d.getMinutes() + 5);
      if (state.lastQuizTime < d) {
        state.due = 0;
      }
    }

    if (!state.due) {
      state.new = 0;
      await newVocabList();
      return;
    }

    // milliseconds
    state.lastQuizTime = new Date();
  } else {
    const r = await api.new_vocab_list();
    state.vocabList = r.result;
  }

  if (state.vocabDetails.cedict[0]?.simp === state.vocabList[0].v) {
    const v0 = state.vocabList.shift();
    if (v0) {
      state.vocabList.push(v0);
    }
  }

  state.total = state.vocabList.length;
  state.pendingList = [];

  document.querySelectorAll(".count[data-count-type]").forEach((el) => {
    if (!(el instanceof HTMLElement)) return;
    const type = el.getAttribute("data-count-type");
    switch (type) {
      case "total":
        el.innerText = state.total.toString();
        break;
      case "due":
        if (!state.due) {
          el.innerText = "-";
        } else {
          el.textContent = "";
          el.append(document.createTextNode(`${state.due - state.new || ""}`));
          if (state.new) {
            const s = document.createElement("small");
            s.innerText = `+${state.new}`;
            el.append(s);
          }
        }
        break;
      default:
        el.innerText = "0";
    }
  });

  document.querySelectorAll("[data-repeat]").forEach((el) => {
    el.setAttribute("data-repeat", state.isRepeat ? "true" : "");
  });

  document.querySelectorAll("#progress [data-count-type]").forEach((el) => {
    if (!(el instanceof HTMLElement)) return;
    el.style.width = "0";
  });

  await newVocab();

  if (customItemSRS !== undefined) {
    let showDetails = true;

    const i = document.createElement("i");
    i.innerText = (() => {
      if (!customItemSRS?.due) return "";
      showDetails = false;

      const due = new Date(customItemSRS.due);
      let untilDue = +due - +new Date();
      if (untilDue < 0) {
        showDetails = false;
        return "(past due)";
      }

      untilDue /= 1000 * 60; // minutes
      if (untilDue < 1) {
        return "(due soon)";
      }

      if (untilDue > 10) {
        showDetails = true;
      }

      if (untilDue < 60) {
        const n = Math.floor(untilDue);
        return `(due in ${n} minute${n > 1 ? "s" : ""})`;
      }

      untilDue /= 60; // hours
      if (untilDue < 24) {
        const n = Math.floor(untilDue);
        return `(due in ${n} hour${n > 1 ? "s" : ""})`;
      }

      untilDue /= 24; // days
      if (untilDue < 30) {
        const n = Math.floor(untilDue);
        return `(due in ${n} day${n > 1 ? "s" : ""})`;
      }

      return `(due ${due.toLocaleDateString()})`;
    })();

    if (showDetails) {
      state.isRepeat = true;
      mark("repeat");
    } else {
      elRoot.setAttribute("data-type", "due");
    }

    elStatus.append(i);
  }
}

/**
 *
 * @param {{skipSave?: boolean}} [opts={}]
 * @returns
 */
function makeNotes({ skipSave } = {}) {
  const elDisplay = /** @type {HTMLDivElement} */ (
    elNotes.querySelector("#notes-show .notes-display")
  );
  const item = state.vocabList[state.i];

  const AI_TRANSLATION_STRING = "<!-- AI translation -->";
  const NEW_AI_TRANSLATION_STRING = "<!-- AI translation (new) -->";

  let isAITranslation = !elNotesTextarea.value.trim();
  let reset = false;

  if (elNotesTextarea.value.endsWith(NEW_AI_TRANSLATION_STRING)) {
    reset = true;
    elNotesTextarea.value = elNotesTextarea.value.slice(
      0,
      elNotesTextarea.value.length - NEW_AI_TRANSLATION_STRING.length
    );
    elNotesTextarea.value += AI_TRANSLATION_STRING;
  }

  if (elNotesTextarea.value.endsWith(AI_TRANSLATION_STRING)) {
    isAITranslation = true;
  }

  // Use a flag to prevent repeated AI translation calls for the same item
  if (!makeNotes.aiTranslationTriggeredSet.has(item.v) && isAITranslation) {
    makeNotes.aiTranslationTriggeredSet.add(item.v); // Add the item to the set

    api.ai_translation(item.v, { reset }).then(async (r) => {
      const checkSameItem = () => state.vocabList[state.i]?.v === item.v;

      // Polling until the result is available
      while (!r.result) {
        await new Promise((resolve) => setTimeout(resolve, 1000));

        // Do not get the result if the item has changed
        if (!checkSameItem()) break;
        r = await api.ai_translation(item.v, { result_only: true });
      }

      // Do not update the notes if the item has changed
      if (!checkSameItem()) return;

      // Get the current notes
      let notes = elNotesTextarea.value;

      if (notes.endsWith(AI_TRANSLATION_STRING)) {
        notes = notes.slice(0, notes.length - AI_TRANSLATION_STRING.length);
      }

      if (!notes.includes(AI_TRANSLATION_STRING)) {
        if (notes) {
          notes += "\n\n";
        }

        notes += AI_TRANSLATION_STRING + "\n" + r.result;
        item.data.notes = notes;

        elNotesTextarea.value = notes;
        makeNotes({ skipSave: false });
        // Toggle the notes display to show the new notes
        elNotes.setAttribute("data-has-notes", "1");
      }
      makeNotes.aiTranslationTriggeredSet.delete(item.v); // Remove the item from the set
    });
  }

  const notesText = elNotesTextarea.value;
  const newHTML = notesText.trim() ? converter.makeHtml(notesText) : "";
  elDisplay.innerHTML = newHTML;

  elDisplay.querySelectorAll("a").forEach((el) => {
    el.target = "_blank";
    el.rel = "noopener noreferrer";
  });

  if (!skipSave) {
    item.data = item.data || {
      wordfreq: 0,
      notes: "",
    };
    item.data.notes = notesText;
    api.save_notes(item.v, notesText);
  }
}

// Initialize the flag for AI translation
makeNotes.aiTranslationTriggeredSet = /** @type {Set<string>} */ (new Set());
