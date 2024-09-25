//@ts-check

const elTableBody = document.querySelector("tbody");
const elRowTemplate = elTableBody.querySelector("template");

window.addEventListener("pywebviewready", async () => {
  const levels = await pywebview.api.get_levels();

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

        const td = elRow.querySelector("td");
        td.append(...vs.flatMap((v) => [makeElVoc(v), "，"]));
        td.lastChild.remove();

        return elRow;
      })
  );

  const lvSet = new Set((await pywebview.api.get_settings()).levels);
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
      pywebview.api.set_level(lv, el.checked);
    });
  });

  if (elHighest) {
    const tr = elHighest.closest("tr");
    const el = tr.nextElementSibling || tr;
    el.scrollIntoView(false);
  }
});
