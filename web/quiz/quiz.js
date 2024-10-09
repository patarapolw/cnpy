//@ts-check

/** @type {State} */
const state = {
  vocabList: [],
  i: 0,
  total: 20,
  max: 20,
  skip: 0,
  due: "-",
  vocabDetails: { cedict: [], sentences: [] },
  pendingList: [],
  lastIsRight: null,
  lastIsFuzzy: false,
  lastQuizTime: null,
  isRepeat: false,
};

const elVocab = /** @type {HTMLDivElement} */ (
  document.getElementById("vocab")
);

const elInput = /** @type {HTMLInputElement} */ (
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

elInput.parentElement.addEventListener("submit", doNext);
elInput.focus();

elInput.addEventListener("keydown", (ev) => {
  switch (ev.key) {
    case "Enter":
      break;
    default:
      if (typeof state.lastIsRight === "boolean") {
        ev.preventDefault();

        if (ev.key === "z") {
          state.vocabList.push(...state.vocabList.splice(state.i, 1));
          state.i--;
          newVocab();
        }
      }
  }
});

let isDialog = false;

document.addEventListener("keydown", (ev) => {
  switch (ev.key) {
    case "Escape":
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
      if (!state.isRepeat) {
        newVocabList();
      }
      break;
    case "Enter":
      if (!elInput.value) {
        ev.preventDefault();
      }
  }
});

window.addEventListener("focus", async () => {
  if (isDialog && elCompare.innerText) {
    isDialog = false;

    const { v } = state.vocabList[state.i];
    state.vocabList[state.i] = await pywebview.api.get_vocab(v);

    softCleanup();
    doNext();
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

const converter = new showdown.Converter({
  parseImgDimensions: true,
  // openLinksInNewWindow: true,
  emoji: true,
});

elNotesTextarea.addEventListener("paste", (ev) => {
  const { target, clipboardData } = ev;

  if (!clipboardData) return;
  if (!(target instanceof HTMLTextAreaElement)) return;

  const html = clipboardData.getData("text/html");
  if (!html) return;

  const selection = window.getSelection();
  if (!selection?.rangeCount) return;

  ev.preventDefault();

  const md = converter
    .makeMarkdown(html)
    .replace(/<!--.*?-->/g, "")
    .replace(/([\p{Ps}\p{Pi}]+)\s+</gu, "$1<")
    .replace(/>\s+([\p{Pe}\p{Pf}.。,，、]+)/gu, ">$1")
    .replace(/(\r?\n)+ {1,3}([^ ])/g, " $2")
    .replace(/^(\r?\n)+/, "")
    .replace(/(\r?\n)+$/, "");

  target.setRangeText(md);
  target.selectionStart += md.length;
  target.blur();
  target.focus();
});

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
      };
  }
});

window.addEventListener("pywebviewready", () => {
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
    if (typeof state.lastIsRight === "boolean") {
      mark();
    }

    newVocab();
  } else {
    pywebview.api.log(state.vocabDetails.cedict);

    const currentItem = state.vocabList[state.i];

    const dictPinyin = state.vocabDetails.cedict
      .map((v) => v.pinyin)
      .filter((v, i, a) => a.indexOf(v) === i);

    if (new Set(dictPinyin.map((p) => p.toLocaleLowerCase())).size > 1) {
      elCompare.href = `./pinyin-select.html?v=${currentItem.v}`;
      elCompare.onclick = (ev) => {
        ev.preventDefault();
        const a = /** @type {HTMLAnchorElement} */ (ev.target);
        if (!a.href) return;
        isDialog = true;
        pywebview.api.new_window(a.href, a.title || a.innerText, {
          width: 300,
          height: 300,
        });
      };
    }

    const pinyin = currentItem.data.pinyin || dictPinyin;

    elCompare.innerText = pinyin.join("; ").replace(/u:/g, "ü");

    elVocab.onclick = () => {
      const u = new SpeechSynthesisUtterance(currentItem.v);
      u.lang = "zh-CN";
      speechSynthesis.speak(u);
    };

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
    state.lastIsRight = elInput.value
      .split(";")
      .every((v) => pinyin.some((p) => comp_pinyin(p, v.trim())));

    if (!state.lastIsRight) {
      if (
        elInput.value
          .split(";")
          .every((v) => pinyin.some((p) => comp_pinyin(p, v.trim(), true)))
      ) {
        state.lastIsFuzzy = true;
      }
    }

    document.querySelectorAll("[data-checked]").forEach((el) => {
      el.setAttribute("data-checked", state.lastIsRight ? "right" : "wrong");
    });

    elInput.value = elInput.value.replace(/u:/g, "v").replace(/v/g, "ü");
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
    pywebview.api.mark(currentItem.v, type);
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
  elInput.value = "";
  elInput.oninput = null;
  elInput.focus();

  softCleanup();

  state.i++;
  state.lastIsRight = null;

  if (state.pendingList.length >= 10 || state.i >= state.vocabList.length) {
    await newVocabList();
    return;
  }

  document.querySelectorAll("[data-checked]").forEach((el) => {
    el.setAttribute("data-checked", "");
  });

  const {
    data: { wordfreq, notes },
    v,
  } = state.vocabList[state.i];
  // pywebview.api.log({ v, wordfreq });

  state.vocabDetails = await pywebview.api.vocab_details(v);
  elVocab.innerText = v;
  elVocab.onclick = null;

  elNotesTextarea.value = notes || "";
  makeNotes(true);

  elNotes.setAttribute("data-has-notes", notes ? "1" : "");

  document.querySelectorAll(".external-links a").forEach((a) => {
    if (!(a instanceof HTMLAnchorElement)) return;

    let href = a.getAttribute("data-href");
    if (!href) {
      a.setAttribute("data-href", a.href);
      href = a.href;
    }
    a.href = href.replace("__voc__", v);
  });
}

async function newVocabList() {
  state.i = -1;
  state.skip = 0;

  state.isRepeat = false;

  if (state.pendingList.length > 0) {
    state.vocabList = state.pendingList;
    state.isRepeat = true;
  } else if (state.due) {
    const r = await pywebview.api.due_vocab_list(state.max);
    state.vocabList = r.result;
    state.due = r.count;

    if (r.count < 5 && state.lastQuizTime) {
      const d = new Date();
      d.setMinutes(d.getMinutes() + 5);
      if (state.lastQuizTime < d) {
        state.due = 0;
      }
    }

    console.log(state);

    if (!state.due) {
      await newVocabList();
      return;
    }

    // milliseconds
    state.lastQuizTime = new Date();
  } else {
    const r = await pywebview.api.new_vocab_list(state.max);
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
        el.innerText = (state.due || "-").toString();
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
}

/**
 *
 * @param {boolean} [skipSave]
 * @returns
 */
function makeNotes(skipSave) {
  const notesText = elNotesTextarea.value;
  const elDisplay = /** @type {HTMLDivElement} */ (
    elNotes.querySelector("#notes-show .notes-display")
  );

  if (!notesText.trim() && !elDisplay.innerHTML.trim()) return;

  const newHTML = converter.makeHtml(notesText);
  if (newHTML === elDisplay.innerHTML) return;

  elDisplay.innerHTML = newHTML;

  elDisplay.querySelectorAll("a").forEach((el) => {
    el.target = "_blank";
    el.rel = "noopener noreferrer";
  });

  if (!skipSave) {
    const item = state.vocabList[state.i];
    item.data = item.data || {
      wordfreq: 0,
      notes: "",
    };
    item.data.notes = notesText;
    pywebview.api.save_notes(item.v, notesText);
  }
}

/**
 *
 * @param {string} s
 * @param {boolean} [isFuzzy]
 * @returns
 */
function normalize_pinyin(s, isFuzzy) {
  s = s.replace(/[vü]/g, "u:").replace(/ /g, "").toLocaleLowerCase();
  if (isFuzzy) {
    s = s.replace(/\d+/g, " ");
  }
  return s;
}

/**
 *
 * @param {string} a
 * @param {string} b
 * @param {boolean} [isFuzzy]
 * @returns
 */
function comp_pinyin(a, b, isFuzzy) {
  return normalize_pinyin(a, isFuzzy) === normalize_pinyin(b, isFuzzy);
}
