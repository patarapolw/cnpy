//@ts-check

const elPinyinSelect = document.getElementById("pinyin-select");
const elWarnings = document.getElementById("warnings");
const elWarningItems = document.getElementById("warning-items");

window.addEventListener("pywebviewready", async () => {
  const v = new URL(location.href, location.origin).searchParams.get("v");
  if (!v) return;

  let {
    data: { pinyin: _chosenPinyin, mustPinyin = [], warnPinyin = [] },
  } = await pywebview.api.get_vocab(v);

  const r = await pywebview.api.vocab_details(v);

  const lowercasePinyin = r.cedict.map((v) => v.pinyin.toLocaleLowerCase());
  const allPinyin = r.cedict
    .map((v) => v.pinyin)
    .filter((v, i) => lowercasePinyin.indexOf(v.toLocaleLowerCase()) === i);

  const chosenPinyinSet = new Set(_chosenPinyin || allPinyin);
  elPinyinSelect.setAttribute(
    "data-pinyin-count",
    chosenPinyinSet.size.toString()
  );

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
            if (elImportant.checked) {
              elImportant.checked = false;
              parseElImportant();
            }
          } else {
            elCheck.checked = !elCheck.checked;
            return;
          }
        }

        elPinyinSelect.setAttribute(
          "data-pinyin-count",
          chosenPinyinSet.size.toString()
        );

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
      elImportant.checked = mustPinyin.includes(p);

      const parseElImportant = () => {
        if (elImportant.checked) {
          mustPinyin.push(p);
        } else {
          mustPinyin = mustPinyin.filter((s) => s !== p);
        }
        pywebview.api.set_pinyin(v, mustPinyin, "mustPinyin");
      };

      elImportant.oninput = parseElImportant;

      elField.append(elImportant);

      const elLabel = document.createElement("label");
      elLabel.innerText = p;

      const div = document.createElement("div");
      div.append(elField, elLabel);

      return div;
    })
  );

  elWarningItems.innerText = warnPinyin.join("; ");

  elWarnings.onclick = () => {
    const p = prompt(
      "Pinyin to warn, separated by ; (comma)",
      warnPinyin.join("; ")
    );
    if (typeof p === "string") {
      warnPinyin = p
        .split(";")
        .map((s) => s.trim().replace(/[vü]/g, "u:").replace(/ +/g, " "))
        .filter((s) => /^([a-z:]+[1-5]($| ))+$/.test(s));

      elWarningItems.innerText = warnPinyin.join("; ");
      pywebview.api.set_pinyin(v, warnPinyin, "warnPinyin");
    }
  };
});
