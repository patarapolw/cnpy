//@ts-check

import { api } from "../api.js";

{
  /** @type {HTMLButtonElement} */
  const btnUpdateCedict = document.querySelector("button#update-cedict");

  btnUpdateCedict.onclick = async () => {
    await api.update_dict();
  };
}

////////////////////

{
  /** @type {HTMLFieldSetElement} */
  const fieldsetQuizSettings = document.querySelector("fieldset#quiz-settings");

  let ttsEngine = "";

  fieldsetQuizSettings.querySelectorAll("input").forEach((inp) => {
    if (inp.type !== "radio") return;
    if (inp.checked) {
      ttsEngine = inp.value;
    }

    inp.addEventListener("change", () => {
      if (inp.checked) {
        ttsEngine = inp.value;
        checkTTSengine();
      }
    });
  });

  function checkTTSengine() {
    fieldsetQuizSettings.classList.toggle(
      "hide-options",
      ttsEngine !== "emoti"
    );
  }
  checkTTSengine();
}

////////////////////

{
  /** @type {HTMLFieldSetElement} */
  const fieldsetOpenAI = document.querySelector("fieldset#llm-online");

  /** @type {HTMLInputElement} */
  const inputOpenAIapiKey = fieldsetOpenAI.querySelector(
    'input[type="text"]#openai-api-key'
  );

  inputOpenAIapiKey.addEventListener("input", () => {
    checkAPIkey();
  });

  function checkAPIkey() {
    fieldsetOpenAI.classList.toggle("hide-options", !inputOpenAIapiKey.value);
    console.log(fieldsetOpenAI.className);
  }
  checkAPIkey();
}

////////////////////

{
  /** @type {HTMLFieldSetElement} */
  const fieldsetLocalLLM = document.querySelector("fieldset#llm-local");

  /** @type {HTMLFormElement} */
  const radioLocalLLMengine = fieldsetLocalLLM.querySelector("form#llm-engine");

  let llmEngine = "";

  radioLocalLLMengine.querySelectorAll("input").forEach((inp) => {
    if (inp.type !== "radio") return;
    if (inp.checked) {
      llmEngine = inp.value;
    }

    inp.addEventListener("change", () => {
      if (inp.checked) {
        llmEngine = inp.value;
        checkLocalLLM();
      }
    });
  });

  function checkLocalLLM() {
    fieldsetLocalLLM.classList.toggle("hide-options", !llmEngine);
  }
  checkLocalLLM();
}
