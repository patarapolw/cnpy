//@ts-check

import { api } from "../api.js";

const elTableBody = document.querySelector("tbody");
const elRowTemplate = elTableBody.querySelector("template");

window.addEventListener("pywebviewready", async () => {
  const levels = await api.get_levels();

  elTableBody.append(
    ...Object.entries(levels)
      .sort()
      .map(([k, vs]) => {
        const elRow = /** @type {HTMLElement} */ (
          elRowTemplate.content.cloneNode(true)
        );

        const lvText = Number(k.split("/").pop().split(".")[0]).toString();

        elRow.querySelector(".level").innerHTML = lvText;

        const elCheckbox = elRow.querySelector("input");
        elCheckbox.setAttribute("data-level", lvText);

        const makeElVoc = (v) => {
          const el = document.createElement("span");
          el.className = "voc";
          el.innerText = v;
          return el;
        };

        const td = elRow.querySelector(".voc-container");
        td.append(...vs.map((v) => makeElVoc(v)));

        return elRow;
      })
  );

  const lvSet = new Set((await api.get_settings()).levels);
  /** @type {HTMLInputElement} */
  let elHighest;

  document.querySelectorAll("input").forEach((el) => {
    const lv = Number(el.getAttribute("data-level") || "0");
    if (!lv) return;

    if (lvSet.has(lv)) {
      el.checked = true;
      elHighest = el;
    }

    el.addEventListener("change", () => {
      api.set_level(lv, el.checked ? "add" : "remove");
    });
  });

  if (elHighest) {
    const tr = elHighest.closest("tr");
    const el = tr.nextElementSibling || tr;
    el.scrollIntoView(false);
  }
});
