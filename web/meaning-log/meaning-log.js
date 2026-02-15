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

const converter = new showdown.Converter({
  parseImgDimensions: true,
  tables: true,
  strikethrough: true,
  // openLinksInNewWindow: true,
  emoji: true,
});

async function loadHistory(start = liStart) {
  const r = await api.ai_revlog_meaning(start, liSize);

  if (r.result.length < liSize) {
    btnNext.disabled = true;
    return;
  }

  const now_millisec = +new Date();
  const timeHeaders = new Set();

  ol.querySelectorAll(".vocab, .time-group").forEach((el) => el.remove());
  ol.start = start + 1;

  r.result.map((obj) => {
    let header = "";

    const created_millisec = +new Date(obj.created);

    let days_elapsed = Math.floor(
      (now_millisec - created_millisec) / (1000 * 60 * 60 * 24),
    );
    if (days_elapsed < 7) {
      header = `${days_elapsed} days ago`;

      if (days_elapsed === 0) {
        header = "Today";
      } else if (days_elapsed === 1) {
        header = "Yesterday";
      }
    }

    if (!header) {
      const weeks_elapsed = Math.floor(days_elapsed / 7);
      if (weeks_elapsed < 4) {
        header = weeks_elapsed < 2 ? `Last week` : `${weeks_elapsed} weeks ago`;
      }
    }

    if (!header) {
      const months_elapsed = Math.floor(days_elapsed / 30);
      header =
        months_elapsed < 2 ? `Last month` : `${months_elapsed} months ago`;
    }

    if (!timeHeaders.has(header)) {
      timeHeaders.add(header);

      const h = document.createElement("h4");
      h.className = "time-group";
      h.textContent = header;
      ol.appendChild(h);
    }

    const li = document.importNode(templ.content, true);

    const elItem = li.querySelector(".item");
    elItem.textContent = obj.v;

    const elResult = li.querySelector(".result");
    elResult.textContent = obj.answer;
    elResult.className =
      obj.correct === null ? "maybe" : obj.correct ? "right" : "wrong";

    const elWhy = li.querySelector(".why");
    elWhy.innerHTML = converter.makeHtml(obj.explanation);

    // TODO: make LLM meaning check more permissive for at least giving explanation and correctness, even without valid cloze
    // TODO: when cloze generation fails, show error logs in UI

    obj.sentences.map((sent) => {
      const details = document.createElement("details");
      const summary = document.createElement("summary");
      summary.innerText = sent.question;

      const exp = document.createElement("div");
      exp.innerHTML = converter.makeHtml(sent.explanation);

      details.append(summary, exp);

      elWhy.append(details);
    });

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
