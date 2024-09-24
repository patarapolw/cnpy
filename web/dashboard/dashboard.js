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

document.querySelectorAll('a[target="new_window"]').forEach((a) => {
  if (!(a instanceof HTMLAnchorElement)) return;
  a.onclick = (ev) => {
    ev.preventDefault();
    const u = new URL(a.href, location.origin);
    pywebview.api.new_window(a.href, u.searchParams.get("f") || a.innerText);
  };
});

window.addEventListener("focus", init);
window.addEventListener("pywebviewready", init);

async function init() {
  await pywebview.api.update_custom_lists();

  pywebview.api.due_vocab_list().then((r) => {
    if (r.count) {
      elDueCount.innerText = ` (${r.count})`;
    }
  });

  pywebview.api.get_stats().then((r) => {
    console.log(r);

    elHanziList.textContent = "";

    const hanziSet = new Set();

    [r.h5, r.lone, r.h3].forEach((s, i) => {
      if (!s) return;
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
      `生词: ${r.good}` +
        (r.accuracy ? ` (${(r.accuracy * 100).toFixed(0)}%)` : ""),
    ].join(", ");
  });
}
