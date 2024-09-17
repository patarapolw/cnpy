//@ts-check

const elDueCount = /** @type {HTMLSpanElement} */ (
  document.getElementById("due-count")
);

const elLearnedCount = /** @type {HTMLSpanElement} */ (
  document.getElementById("learned-count")
);

const elHanziList = /** @type {HTMLDivElement} */ (
  document.getElementById("hanzi-list")
);

window.addEventListener("pywebviewready", () => {
  pywebview.api.due_vocab_list().then((r) => {
    if (r.count) {
      elDueCount.innerText = ` (${r.count})`;
    }
  });

  pywebview.api.get_stats().then((r) => {
    const lone = [...r.lone];
    const h5 = [...r.h5].filter((c) => !lone.includes(c));
    const h3 = [...r.h3.substring(r.h5.length)].filter((c) => !h5.includes(c));

    elLearnedCount.innerText = [
      `汉字: ${lone.length + h5.length + h3.length}`,
      `生词: ${r.good}`,
    ].join(", ");

    const makeEl = (txt, cls) => {
      const el = document.createElement("span");
      el.innerText = txt;
      el.className = `hanzi ${cls}`;

      return el;
    };

    elHanziList.append(
      ...lone.map((c) => makeEl(c, "lone")),
      ...h5.map((c) => makeEl(c, "h5")),
      ...h3.map((c) => makeEl(c, "h3"))
    );
  });
});
