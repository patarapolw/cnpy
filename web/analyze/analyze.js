//@ts-check

import { api } from "../api.js";

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

elButtonSubmit.addEventListener("click", async (ev) => {
  ev.preventDefault();

  const { result } = await api.analyze(
    elAnalyzer.querySelector("textarea").value
  );

  const ol = elResult.querySelector("ol");
  ol.textContent = "";

  /**
   *
   * @param {(typeof result)[0]} r
   * @returns
   */
  const makeLI = (r) => {
    const li = document.createElement("li");

    const elPinyin = document.createElement("span");
    elPinyin.className = "pinyin";
    elPinyin.innerText = r.pinyin;

    li.append(r.v, elPinyin);

    return li;
  };

  ol.append(...result.map((r) => makeLI(r)));

  document
    .querySelectorAll("fieldset")
    .forEach((el) => el.classList.remove("active"));

  elResult.classList.add("active");
});

elButtonReset.addEventListener("click", (ev) => {
  ev.preventDefault();

  elAnalyzer.querySelector("textarea").value = "";

  document
    .querySelectorAll("fieldset")
    .forEach((el) => el.classList.remove("active"));

  elAnalyzer.classList.add("active");
});
