//@ts-check

const filename = new URL(location.href, location.origin).searchParams.get("f");
const elEditor = /** @type {HTMLOListElement} */ (
  document.getElementById("editor")
);

window.addEventListener("pywebviewready", async () => {
  if (!filename) return;

  let txt = await pywebview.api.load_file(filename);

  const makeLi = (t) => {
    const li = document.createElement("li");
    li.innerText = t;
    return li;
  };

  elEditor.append(...txt.split("\n").map((t) => makeLi(t)));

  function save() {
    if (elEditor.innerText !== txt) {
      txt = elEditor.innerText;
      pywebview.api.save_file(filename, txt);
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
});
