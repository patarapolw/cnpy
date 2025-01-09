//@ts-check

import { api } from "../api.js";

const elPinyinSelect = document.getElementById("pinyin-select");

window.addEventListener("pywebviewready", async () => {
  const v = new URL(location.href, location.origin).searchParams.get("v");
  if (!v) return;

  let {
    data: { pinyin: _chosenPinyin, mustPinyin = [], ...objSelect },
  } = await api.get_vocab(v);

  const r = await api.vocab_details(v);

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

        api.set_quiz_select(
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
        api.set_quiz_select(v, mustPinyin, "mustPinyin");
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

  const DATA_QUIZ_SELECT = "data-quiz-select";
  /** @type {HTMLDivElement} */
  const elOptionalMeanings = document.querySelector(
    `[${DATA_QUIZ_SELECT}="optional_meanings"]`
  );

  document.querySelectorAll(`[${DATA_QUIZ_SELECT}]`).forEach((el) => {
    const type =
      /** @type {'warnPinyin' | 'important_meanings' | 'optional_meanings'} */ (
        el.getAttribute(DATA_QUIZ_SELECT)
      );

    const elBtn = el.querySelector("button");
    const elItems = el.querySelector("small");

    let selections = objSelect[type] || [];

    const updateItemDisplay = () => {
      objSelect[type] = selections;
      elOptionalMeanings.style.display =
        objSelect.important_meanings?.length ||
        objSelect.optional_meanings?.length
          ? "block"
          : "none";

      elItems.innerText = selections.join("; ");
    };
    updateItemDisplay();

    elBtn.onclick = () => {
      const p = prompt(
        `${
          type === "warnPinyin"
            ? "Pinyin to warn"
            : (type[0].toLocaleUpperCase() + type.substring(1)).replace(
                "_",
                " "
              )
        }, separated by ; (comma)`,
        selections.join("; ")
      );
      if (typeof p === "string") {
        selections = p.split(";").map((s) => s.trim());

        if (type === "warnPinyin") {
          selections = selections
            .map((s) => s.replace(/[vü]/g, "u:").replace(/ +/g, " "))
            .filter((s) => /^([a-z:]+[1-5]($| ))+$/.test(s));
        }

        selections = selections.filter((s) => s);

        updateItemDisplay();
        api.set_quiz_select(v, selections, type);
      }
    };
  });
});
