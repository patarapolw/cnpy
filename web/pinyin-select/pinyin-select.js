//@ts-check

const elPinyinSelect = document.getElementById("pinyin-select");
const elExceptions = document.getElementById("exceptions");

window.addEventListener("pywebviewready", async () => {
  const v = new URL(location.href, location.origin).searchParams.get("v");
  if (!v) return;

  const {
    data: { pinyin: _chosenPinyin, mustPinyin, warnPinyin },
  } = await pywebview.api.get_vocab(v);

  const r = await pywebview.api.vocab_details(v);

  const lowercasePinyin = r.cedict.map((v) => v.pinyin.toLocaleLowerCase());
  const allPinyin = r.cedict
    .map((v) => v.pinyin)
    .filter((v, i) => lowercasePinyin.indexOf(v.toLocaleLowerCase()) === i);

  elPinyinSelect.setAttribute("data-pinyin-count", allPinyin.length.toString());

  const chosenPinyinSet = new Set(_chosenPinyin || allPinyin);

  elPinyinSelect.append(
    ...allPinyin.map((p) => {
      const elField = document.createElement("span");
      elField.className = "checkbox";

      const elCheck = document.createElement("input");
      elCheck.type = "checkbox";
      elCheck.checked = chosenPinyinSet.has(p);

      elCheck.oninput = () => {
        if (elCheck.checked) {
          chosenPinyinSet.add(p);
        } else {
          if (chosenPinyinSet.size > 1) {
            chosenPinyinSet.delete(p);
          } else {
            elCheck.checked = !elCheck.checked;
            return;
          }
        }

        pywebview.api.set_pinyin(
          v,
          chosenPinyinSet.size < allPinyin.length
            ? allPinyin.filter((p) => chosenPinyinSet.has(p))
            : null
        );
      };

      elField.append(elCheck);

      const elImportant = document.createElement("input");
      elImportant.type = "checkbox";

      elField.append(elImportant);

      const elLabel = document.createElement("label");
      elLabel.innerText = p;

      const div = document.createElement("div");
      div.append(elField, elLabel);

      return div;
    })
  );

  elExceptions.onclick = () => {
    const p = prompt("Pinyin to warn, separated by ; (comma)");
  };
});
