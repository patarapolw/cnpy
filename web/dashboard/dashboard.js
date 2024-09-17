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
    console.log(r);

    const hanziSet = new Set();

    [r.h5, r.lone, r.h3].forEach((s, i) => {
      const className = `hanzi tier-${i}`;

      for (const c of s) {
        if (!hanziSet.has(c)) {
          hanziSet.add(c);

          const el = document.createElement("span");
          el.innerText = c;
          el.className = className;

          elHanziList.append(el);
        }
      }
    });

    elLearnedCount.lang = "zh-CN";
    elLearnedCount.innerText = [
      `汉字: ${hanziSet.size}`,
      `生词: ${r.good} (${(r.accuracy * 100).toFixed(0)}%)`,
    ].join(", ");
  });
});
