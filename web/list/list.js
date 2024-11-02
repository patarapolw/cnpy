//@ts-check

import { api } from "../api.js";

const filename = new URL(location.href, location.origin).searchParams.get("f");
const elEditor = /** @type {HTMLOListElement} */ (
  document.getElementById("editor")
);

window.addEventListener("pywebviewready", async () => {
  if (!filename) return;

  let txt = await api.load_file(filename);
  /** @type {HTMLLIElement} */
  let lastLi;

  const makeLi = (t) => {
    const li = document.createElement("li");
    li.innerText = t;
    lastLi = li;
    return li;
  };

  elEditor.append(...txt.split("\n").map((t) => makeLi(t)));
  setTimeout(() => {
    const el = lastLi || elEditor;
    el.scrollIntoView();

    const range = document.createRange();
    const selection = window.getSelection();
    range.selectNodeContents(el);
    range.collapse(false); // <-- Set the cursor at the end of the selection
    selection.removeAllRanges();
    selection.addRange(range);
    el.focus();
  });

  function save() {
    if (elEditor.innerText !== txt) {
      txt = elEditor.innerText;
      api.save_file(
        filename,
        txt
          .split("\n")
          .map((s) => s.trim())
          .filter((s) => /^\p{sc=Han}+$/u.test(s))
          .join("\n")
      );
    }
  }

  let lastText = elEditor.innerText;
  elEditor.addEventListener("input", () => {
    lastText = elEditor.innerText;
    setTimeout(() => {
      if (elEditor.innerText === lastText) {
        save();
      }
    }, 1000);
  });

  elEditor.addEventListener("mouseleave", save);

  elEditor.addEventListener("paste", (ev) => {
    const { clipboardData } = ev;
    if (!clipboardData) return;

    setTimeout(() => {
      elEditor.querySelectorAll("li").forEach((li) => {
        if (!li.innerText.trim()) {
          li.remove();
        }
      });
    });

    const html = clipboardData.getData("text/html");

    const div = document.createElement("div");
    div.innerHTML = html;
    if (div.querySelector("li .pinyin")) {
      ev.preventDefault();
      div.querySelectorAll(".pinyin").forEach((el) => el.remove());
      elEditor.append(...div.querySelectorAll("li"));
    }
  });
});
