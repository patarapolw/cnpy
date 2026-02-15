//@ts-check

import { api } from "../api.js";

let liStart = 0;
const liSize = 10;

const ol = document.querySelector("ol");
const templ = ol.querySelector("template");

/** @type {HTMLButtonElement} */
const btnPrev = document.querySelector("button#prev");
/** @type {HTMLButtonElement} */
const btnNext = document.querySelector("button#next");

async function loadHistory(start = liStart) {
  const r = await api.ai_revlog_meaning(start, liSize);

  if (r.result.length < liSize) {
    btnNext.disabled = true;
    return;
  }

  ol.querySelectorAll("li").forEach((li) => li.remove());
  ol.start = start + 1;

  r.result.map((obj) => {
    const li = document.importNode(templ.content, true);

    li.querySelector(".vocab").textContent = obj.v;
    li.querySelector(".result").textContent = obj.answer;
    li.querySelector(".result").className =
      obj.correct === null ? "maybe" : obj.correct ? "right" : "wrong";
    li.querySelector(".why").textContent = obj.explanation;

    ol.appendChild(li);
  });

  liStart = start;
  btnPrev.disabled = !(start > 0);
}

btnPrev.onclick = (ev) => {
  ev.preventDefault();
  loadHistory(liStart - liSize);
};

btnNext.onclick = (ev) => {
  ev.preventDefault();
  loadHistory(liStart + liSize);
};

loadHistory();
