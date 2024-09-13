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

const elInput = document.getElementById("type-input");
const elCompare = document.getElementById("type-compare");
const elNotes = document.getElementById("notes");
const elNotesTextarea = elNotes.querySelector("textarea");

elInput.parentElement.addEventListener("submit", onsubmit);
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

          document.querySelector(".count[data-count-type='total']").innerText =
            state.total - state.skip;

          newVocab();
        }
      }
      break;
    case "F5":
    case "F1":
      if (!state.isRepeat) {
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

/** @type {import('showdown').Converter} */
const converter = new showdown.Converter({
  parseImgDimensions: true,
  // openLinksInNewWindow: true,
  emoji: true,
});

elNotes.querySelector("textarea").addEventListener("paste", (ev) => {
  const { target, clipboardData } = ev;

  if (!clipboardData) return;
  if (!(target instanceof HTMLTextAreaElement)) return;

  const html = clipboardData.getData("text/html");
  if (!html) return;

  const selection = window.getSelection();
  if (!selection.rangeCount) return;

  ev.preventDefault();

  const md = converter
    .makeMarkdown(html)
    .replace(/<!--.*?-->/g, "")
    .replace(/^(\r?\n)+/, "")
    .replace(/(\r?\n)+$/, "");
  // .replace(/(\r?\n){2,}/g, "");

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

function onsubmit(ev) {
  if (ev) {
    ev.preventDefault();
  }

  if (elCompare.innerText) {
    if (typeof state.lastIsRight === "boolean") {
      mark();
    }

    newVocab();
  } else {
    fetch("/api/log", {
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      method: "POST",
      body: JSON.stringify(state.vocabDetails.cedict),
    });

    const pinyin = state.vocabDetails.cedict
      .map((v) => v.pinyin)
      .filter((v, i, a) => a.indexOf(v) === i);

    elCompare.innerText = pinyin.join("; ").replace(/u:/g, "ü");

    const elDictEntries = document.getElementById("dictionary-entries");
    {
      const elTemplate = Array.from(elDictEntries.childNodes).find(
        (el) => el instanceof HTMLTemplateElement
      );

      elDictEntries.append(
        ...state.vocabDetails.cedict.map((v) => {
          const el = elTemplate.content.cloneNode(true);

          el.querySelector(".simp").innerText = v.simp;
          el.querySelector(".trad").innerText = v.trad || "";
          el.querySelector(".pinyin").innerText = v.pinyin.replace(/u:/g, "ü");
          el.querySelector(".english").append(
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

    const elSentences = document.getElementById("sentences");
    elSentences.setAttribute(
      "data-sentence-count",
      state.vocabDetails.sentences.length
    );
    {
      const elTemplate = Array.from(elSentences.childNodes).find(
        (el) => el instanceof HTMLTemplateElement
      );

      const ul = document.createElement("ul");
      ul.className = "if-checked-details";
      elSentences.append(ul);

      ul.append(
        ...state.vocabDetails.sentences.map((v) => {
          const el = elTemplate.content.cloneNode(true);

          el.querySelector(".simp").innerText = v.cmn;

          if (v.eng) {
            el.querySelector(".english").innerText = v.eng;
          } else {
            el.querySelector("ul").remove();
          }

          return el;
        })
      );
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
  }

  return false;
}

function mark(type) {
  if (type) {
    setTimeout(onsubmit);
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

  const el = document.querySelector(`.count[data-count-type="${type}"]`);
  const markCount = parseInt(el.innerText) + 1;

  el.innerText = markCount;

  document.querySelector(
    `#progress [data-count-type="${type}"]`
  ).style.width = `${((markCount / (state.total - state.skip)) * 100).toFixed(
    1
  )}%`;

  const currentItem = state.vocabList[state.i];

  if (type !== "right") {
    state.pendingList.push(currentItem);
  }

  state.lastIsRight = null;

  if (!state.isRepeat) {
    fetch(`/api/mark?v=${currentItem.v}&t=${type}`, { method: "POST" });
  }
}

async function newVocab(v0 = "") {
  elInput.value = "";
  elInput.focus();

  elCompare.innerText = "";

  document.querySelectorAll(".if-checked-details").forEach((el) => el.remove());

  state.i++;
  state.lastIsRight = null;

  if (state.pendingList.length >= 10 || state.i >= state.vocabList.length) {
    await newVocabList(v0);
    return;
  }

  document.querySelectorAll("[data-checked]").forEach((el) => {
    el.setAttribute("data-checked", "");
  });

  const {
    data: { wordfreq, notes },
    v,
  } = state.vocabList[state.i];

  fetch("/api/log", {
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    method: "POST",
    body: JSON.stringify({ v, wordfreq }),
  });

  state.vocabDetails = await fetch(`/api/vocab_details?v=${v}`).then((r) =>
    r.json()
  );
  document.getElementById("vocab").innerText = v;

  elNotesTextarea.value = notes || "";
  makeNotes(true);

  elNotes.setAttribute("data-has-notes", notes ? "1" : "");

  document.querySelectorAll(".external-links a").forEach((a) => {
    let href = a.getAttribute("data-href");
    if (!href) {
      a.setAttribute("data-href", a.href);
      href = a.href;
    }
    a.href = href.replace("__voc__", v);
  });
}

async function newVocabList(v = "") {
  state.i = -1;
  state.skip = 0;

  state.isRepeat = false;

  if (state.pendingList.length > 0) {
    state.vocabList = state.pendingList;
    state.isRepeat = true;
  } else if (state.due) {
    const r = await fetch(`/api/due_vocab_list?limit=${state.max}&v=${v}`).then(
      (r) => r.json()
    );
    state.vocabList = r.result;
    state.due = r.count;

    // if (r.count < state.max / 2 && state.lastQuizTime) {
    //   const d = new Date();
    //   d.setMinutes(d.getMinutes() + 5);
    //   if (state.lastQuizTime < d) {
    //     state.due = 0;
    //   }
    // }

    if (!state.due) {
      await newVocabList();
      return;
    }

    // milliseconds
    state.lastQuizTime = new Date();
  } else {
    const r = await fetch(`/api/new_vocab_list?limit=${state.max}`).then((r) =>
      r.json()
    );
    state.vocabList = r.result;
  }

  if (
    state.vocabDetails[0] &&
    state.vocabDetails.cedict[0]?.simp === state.vocabList[0].v
  ) {
    state.vocabList.push(state.vocabList.shift());
  }

  state.total = state.vocabList.length;
  state.pendingList = [];

  document.querySelectorAll(".count[data-count-type]").forEach((el) => {
    const type = el.getAttribute("data-count-type");
    switch (type) {
      case "total":
        el.innerText = state.total;
        break;
      case "due":
        el.innerText = state.due || "-";
        break;
      default:
        el.innerText = 0;
    }
  });

  document.querySelectorAll("[data-repeat]").forEach((el) => {
    el.setAttribute("data-repeat", state.isRepeat ? "true" : "");
  });

  document.querySelectorAll("#progress [data-count-type]").forEach((el) => {
    el.style.width = "0";
  });

  await newVocab();
}

function makeNotes(skipSave) {
  const notesText = elNotesTextarea.value;
  const elDisplay = elNotes.querySelector("#notes-show .notes-display");

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
    item.data = item.data || {};
    item.data.notes = notesText;

    fetch(`/api/save_notes?v=${item.v}`, {
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      method: "POST",
      body: JSON.stringify({ notes: notesText }),
    });
  }
}

function normalize_pinyin(s, isFuzzy) {
  s = s.replace(/[vü]/g, "u:").replace(/ /g, "").toLocaleLowerCase();
  if (isFuzzy) {
    s = s.replace(/\d+/g, " ");
  }
  return s;
}

function comp_pinyin(a, b, isFuzzy) {
  return normalize_pinyin(a, isFuzzy) === normalize_pinyin(b, isFuzzy);
}
