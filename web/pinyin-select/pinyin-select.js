//@ts-check

window.addEventListener("pywebviewready", async () => {
  const v = new URL(location.href, location.origin).searchParams.get("v");
  if (!v) return;

  const {
    data: { pinyin: _chosenPinyin },
  } = await pywebview.api.get_vocab(v);

  const r = await pywebview.api.vocab_details(v);
  const allPinyin = r.cedict
    .map((v) => v.pinyin)
    .filter((v, i, a) => a.indexOf(v) === i);

  const chosenPinyinSet = new Set(_chosenPinyin || allPinyin);

  document.body.append(
    ...allPinyin.map((p) => {
      const elLabel = document.createElement("label");

      const elCheck = document.createElement("input");
      elCheck.type = "checkbox";
      elCheck.checked = chosenPinyinSet.has(p);
      elCheck.style.marginRight = "1em";

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

      elLabel.append(elCheck, p);

      const div = document.createElement("div");
      div.append(elLabel);

      return div;
    })
  );
});
