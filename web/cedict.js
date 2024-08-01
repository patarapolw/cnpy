const state = {
  vocabList: [],
  i: 0,
  total: 20,
  max: 20,
  skip: 0,
  due: "-",
  vocabDetails: [],
  pendingList: [],
  lastIsRight: null,
};

const elInput = document.getElementById("type-input");
const elCompare = document.getElementById("type-compare");

elInput.parentElement.addEventListener("submit", onsubmit);
elInput.focus();

document.addEventListener("keydown", (ev) => {
  if (ev.key === "Escape") {
    if (typeof state.lastIsRight === "boolean") {
      mark("repeat");
    } else {
      state.skip++;

      document.querySelector(".count[data-count-type='total']").innerText =
        state.total - state.skip;

      newVocab();
    }
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
    pywebview.api.log(state.vocabDetails);
    const pinyin = state.vocabDetails
      .map((v) => v.pinyin)
      .filter((v, i, a) => a.indexOf(v) === i)
      .sort();

    elCompare.innerText = pinyin.join("; ");

    if (
      elInput.value
        .split(";")
        .every((v) => pinyin.some((p) => comp_pinyin(p, v.trim())))
    ) {
      state.lastIsRight = true;

      document.querySelectorAll("[data-checked]").forEach((el) => {
        el.setAttribute("data-checked", "right");
      });
    } else {
      state.lastIsRight = false;

      document.querySelectorAll("[data-checked]").forEach((el) => {
        el.setAttribute("data-checked", "wrong");
      });
    }
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
      type = "wrong";
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

  if (state.vocabList.length === state.due || state.max) {
    pywebview.api.mark(currentItem.v, type);
  }
}

async function newVocab() {
  elInput.value = "";
  elInput.focus();

  elCompare.innerText = "";

  state.i++;

  if (state.i >= state.vocabList.length) {
    await newVocabList();
    return;
  }

  document.querySelectorAll("[data-checked]").forEach((el) => {
    el.setAttribute("data-checked", "");
  });

  const quizItem = state.vocabList[state.i];
  pywebview.api.log(quizItem.data);

  state.vocabDetails = await pywebview.api.vocab_details(quizItem.v);
  document.getElementById("vocab").innerText = quizItem.v;
}

async function newVocabList() {
  state.i = -1;
  state.skip = 0;

  let isRepeat = false;

  if (state.pendingList.length > 1) {
    state.vocabList = state.pendingList;
    isRepeat = true;
  } else if (state.due) {
    const r = await pywebview.api.due_vocab_list(state.max);
    state.vocabList = r.result;
    state.due = r.count;

    if (!r.count) {
      newVocabList();
      return;
    }
  } else {
    const r = await pywebview.api.new_vocab_list(state.max);
    state.vocabList = r.result;
  }

  state.total = state.vocabList.length;
  state.pendingList = [];

  document.querySelectorAll(".count[data-count-type]").forEach((el) => {
    const type = el.getAttribute("data-count-type");
    switch (type) {
      case "total":
        el.innerText = state.total;
        isRepeat
          ? el.classList.add("is-repeat")
          : el.classList.remove("is-repeat");
        break;
      case "due":
        el.innerText = state.due || "-";
        break;
      default:
        el.innerText = 0;
    }
  });

  document.querySelectorAll("#progress [data-count-type]").forEach((el) => {
    el.style.width = "0";
  });

  await newVocab();
}

function normalize_pinyin(s) {
  return s.replace(/ /g, "").toLocaleLowerCase();
}

function comp_pinyin(a, b) {
  return normalize_pinyin(a) === normalize_pinyin(b);
}
