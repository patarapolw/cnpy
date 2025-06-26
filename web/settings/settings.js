//@ts-check

import { api } from "../api.js";

/** @type {(() => Promise<void>)[]} */
const saveRunners = [];

{
  /** @type {HTMLButtonElement} */
  const btnUpdateCedict = document.querySelector("button#update-cedict");

  btnUpdateCedict.onclick = async () => {
    btnUpdateCedict.disabled = true;
    await api.update_dict();
    btnUpdateCedict.disabled = false;
  };
}

////////////////////

{
  /** @type {HTMLFieldSetElement} */
  const fieldsetQuizSettings = document.querySelector("fieldset#quiz-settings");

  /** @type {HTMLInputElement} */
  const checkboxHasNew = fieldsetQuizSettings.querySelector("input#has-new");

  /** @type {HTMLInputElement} */
  const inputVoiceName = fieldsetQuizSettings.querySelector("input#voice-name");

  let ttsEngine = "";

  function checkTTSengine() {
    fieldsetQuizSettings.classList.toggle(
      "hide-options",
      ttsEngine !== "emoti"
    );
  }

  async function init() {
    checkboxHasNew.checked = (await api.get_env("CNPY_MAX_NEW")) !== "0";

    const ttsVoice = await api.get_env("TTS_VOICE");
    if (ttsVoice === "0") {
      ttsEngine = "";
    } else if (ttsVoice === "gtts" || ttsVoice === "") {
      ttsEngine = "gtts";
    } else {
      ttsEngine = "emoti";
      inputVoiceName.value = ttsVoice;
    }

    fieldsetQuizSettings.querySelectorAll("input").forEach((inp) => {
      if (inp.type !== "radio") return;
      if (inp.value === ttsEngine) {
        inp.checked = true;
      }

      inp.addEventListener("change", () => {
        if (inp.checked) {
          ttsEngine = inp.value;
          checkTTSengine();
        }
      });
    });

    checkTTSengine();
  }
  init();

  async function save() {
    await api.set_env("CNPY_MAX_NEW", checkboxHasNew.checked ? "10" : "0");

    if ((ttsEngine = "")) {
      await api.set_env("TTS_VOICE", "0");
    } else if (ttsEngine === "gtts") {
      await api.set_env("TTS_VOICE", "gtts");
    } else {
      await api.set_env("TTS_VOICE", inputVoiceName.value);
    }
  }
  saveRunners.push(save);
}

////////////////////

{
  /** @type {HTMLFieldSetElement} */
  const fieldsetOpenAI = document.querySelector("fieldset#llm-online");

  /** @type {HTMLInputElement} */
  const inputOpenAIapiKey = fieldsetOpenAI.querySelector(
    "input#openai-api-key"
  );

  /** @type {HTMLInputElement} */
  const inputOpenAImodel = fieldsetOpenAI.querySelector("input#openai-model");

  /** @type {HTMLInputElement} */
  const inputOpenAIserver = fieldsetOpenAI.querySelector("input#openai-server");

  function checkAPIkey() {
    fieldsetOpenAI.classList.toggle("hide-options", !inputOpenAIapiKey.value);
    console.log(fieldsetOpenAI.className);
  }

  async function init() {
    inputOpenAIapiKey.value = await api.get_env("OPENAI_API_KEY");
    inputOpenAIapiKey.addEventListener("input", () => {
      checkAPIkey();
    });

    if (inputOpenAIapiKey.value) {
      inputOpenAIserver.value = await api.get_env("OPENAI_API_BASE");
      inputOpenAImodel.value = await api.get_env("OPENAI_MODEL");
    }

    checkAPIkey();
  }
  init();

  async function save() {
    await api.set_env("OPENAI_API_KEY", inputOpenAIapiKey.value);
    if (inputOpenAIapiKey.value) {
      await api.set_env("OPENAI_API_BASE", inputOpenAIserver.value);
      await api.set_env("OPENAI_MODEL", inputOpenAImodel.value);
    }
  }
  saveRunners.push(save);
}

////////////////////

{
  /** @type {HTMLFieldSetElement} */
  const fieldsetLocalLLM = document.querySelector("fieldset#llm-local");

  /** @type {HTMLFormElement} */
  const radioLocalLLMengine = fieldsetLocalLLM.querySelector("form#llm-engine");

  /** @type {HTMLInputElement} */
  const inputLocalLLMmodel = fieldsetLocalLLM.querySelector("input#llm-model");

  /** @type {HTMLInputElement} */
  const inputLocalLLMhost = fieldsetLocalLLM.querySelector("input#llm-host");

  let llmEngine = "";

  function checkLocalLLM() {
    fieldsetLocalLLM.classList.toggle("hide-options", !llmEngine);
  }

  async function init() {
    const model = await api.get_env("OLLAMA_MODEL");
    if (model) {
      llmEngine = "ollama";
      inputLocalLLMmodel.value = model;

      inputLocalLLMhost.value = await api.get_env("OLLAMA_HOST");
    }

    radioLocalLLMengine.querySelectorAll("input").forEach((inp) => {
      if (inp.type !== "radio") return;
      if (inp.value === llmEngine) {
        inp.checked = true;
      }

      inp.addEventListener("change", () => {
        if (inp.checked) {
          llmEngine = inp.value;
          checkLocalLLM();
        }
      });
    });

    checkLocalLLM();
  }
  init();

  async function save() {
    if (llmEngine == "ollama") {
      await api.set_env("OLLAMA_MODEL", inputLocalLLMmodel.value);
      await api.set_env("OLLAMA_HOST", inputLocalLLMhost.value);
    } else {
      await api.set_env("OLLAMA_MODEL", "");
    }
  }
  saveRunners.push(save);
}

////////////////////

{
  /** @type {HTMLFieldSetElement} */
  const fieldSetSync = document.querySelector("fieldset#sync");

  /** @type {HTMLInputElement} */
  const inputSyncDatabase = fieldSetSync.querySelector(
    'input[name="sync-database"]'
  );
  /** @type {HTMLButtonElement} */
  const btnRestore = fieldSetSync.querySelector('button[name="restore"]');
  /** @type {HTMLButtonElement} */
  const btnRemove = fieldSetSync.querySelector('button[name="remove"]');

  function check() {
    btnRestore.disabled = !inputSyncDatabase.value;
    btnRemove.disabled = !inputSyncDatabase.value;
  }

  inputSyncDatabase.onclick = async () => {
    const db = await api.set_sync_db();
    inputSyncDatabase.value = db || inputSyncDatabase.value;
    check();
  };

  btnRemove.onclick = async () => {
    inputSyncDatabase.value = "";
    check();
  };

  async function init() {
    check();
  }
  init();
}

////////////////////

/** @type {HTMLButtonElement} */
const btnSave = document.querySelector("button#save");
btnSave.onclick = async () => {
  await Promise.all(saveRunners.map((fn) => fn()));
};
