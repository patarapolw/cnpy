//@ts-check

export const api = {
  /**
   *
   * @returns {Promise<Settings>}
   */
  async get_settings() {
    return fetchAPI("/api/get_settings").then((r) => r.json());
  },
  /**
   *
   * @param {{ c?: string, v?: string, p?: string }} obj
   * @returns {Promise<{
   *  result: {
   *    v: string;
   *    pinyin: string;
   *  }[];
   * }>}
   */
  async search(obj) {
    return fetchAPI("/api/search", obj).then((r) => r.json());
  },
  /**
   *
   * @param {string} txt
   * @returns {Promise<{
   *  result: {
   *    v: string;
   *    pinyin: string;
   *  }[];
   * }>}
   */
  async analyze(txt) {
    return fetchAPI("/api/analyze", { txt }).then((r) => r.json());
  },
  async update_custom_lists() {
    return fetchAPI("/api/update_custom_lists");
  },
  /**
   *
   * @returns {Promise<{
   *  lone: string;
   *  h3: string;
   *  h5: string;
   *  good: number;
   *  accuracy: number;
   *  all: string;
   * }>}
   */
  async get_stats() {
    return fetchAPI("/api/get_stats").then((r) => r.json());
  },
  /**
   *
   * @param {string} v
   * @param {string[] | null} pinyin
   * @param {string} t
   */
  async set_pinyin(v, pinyin, t = "pinyin") {
    return fetchAPI(`/api/set_pinyin/${v}/${t}`, { pinyin });
  },
  /**
   *
   * @param {number} review_counter
   * @returns {Promise<{
   *  result: IQuizEntry[];
   *  count: number;
   *  new: number;
   *  customItemSRS?: any;
   *  isAIenabled?: boolean;
   * }>}
   */
  async due_vocab_list(review_counter = 0) {
    return fetchAPI(`/api/due_vocab_list/${review_counter}`).then((r) =>
      r.json(),
    );
  },
  /**
   *
   * @param {string} v
   * @returns {Promise<IQuizEntry>}
   */
  async get_vocab(v) {
    return fetchAPI(`/api/get_vocab/${v}`).then((r) => r.json());
  },
  /**
   *
   * @param {string} v
   * @returns {Promise<{ v: string | null }>}
   */
  async set_vocab_for_quiz(v) {
    return fetchAPI(`/api/set_vocab_for_quiz/${v}`).then((r) => r.json());
  },
  /**
   *
   * @returns {Promise<{ result: IQuizEntry[] }>}
   */
  async new_vocab_list() {
    return fetchAPI("/api/new_vocab_list").then((r) => r.json());
  },
  /**
   *
   * @param {string} v
   * @returns {Promise<{
   *  cedict: ICedict[];
   *  sentences: ISentence[];
   *  segments: string[];
   *  cloze: string | null;
   * }>}
   */
  async vocab_details(v) {
    return fetchAPI(`/api/vocab_details/${v}`).then((r) => r.json());
  },
  async update_dict() {
    return fetchAPI("/api/update_dict");
  },
  /**
   *
   * @param {string} v
   * @param {string} t
   */
  async mark(v, t) {
    return fetchAPI(`/api/mark/${v}/${t}`);
  },
  /**
   *
   * @param {string} v
   * @param {string} notes
   */
  async save_notes(v, notes) {
    return fetchAPI(`/api/save_notes/${v}`, { notes });
  },
  /**
   *
   * @param {string} f
   */
  async load_file(f) {
    return fetchAPI(`/api/load_file/${f}`).then((r) => r.text());
  },
  /**
   *
   * @param {string} f
   * @param {string} txt
   */
  async save_file(f, txt) {
    return fetchAPI(`/api/save_file/${f}`, { txt });
  },
  /**
   *
   * @returns {Promise<Record<string, string[]>>}
   */
  async get_levels() {
    return fetchAPI("/api/get_levels").then((r) => r.json());
  },
  /**
   *
   * @param {number} lv
   * @param {'add' | 'remove'} state
   */
  async set_level(lv, state = "add") {
    return fetchAPI(`/api/set_level/${lv}/${state}`);
  },
  /**
   *
   * @param {string[]} ks
   * @returns {Promise<Record<string, string[]>>}
   */
  async decompose(ks) {
    return fetchAPI(`/api/decompose`, { ks }).then((r) => r.json());
  },
  /**
   *
   * @param {string} v
   * @param {{
   *  reset?: boolean;
   *  result_only?: boolean;
   *  meaning?: string;
   *  cloze?: string;
   * }} opts
   * @returns {Promise<{result: string}>}
   */
  async ai_translation(v, opts = {}) {
    return fetchAPI(`/api/ai_translation/${v}`, opts).then((r) => r.json());
  },
  /**
   *
   * @param {string} v
   * @returns
   */
  async ai_cloze_delete(v) {
    return fetchAPI(`/api/ai_cloze/delete/${v}`);
  },
  /**
   *
   * @param {number} start
   * @param {number} [limit]
   * @returns {Promise<{
   *   result: {
   *     v: string;
   *     created: string;
   *     correct: boolean | null;
   *     explanation: string;
   *     answer: string;
   *     cloze: string; // can be ''
   *     sentences: {
   *       question: string;
   *       alt: string[];
   *       explanation: string;
   *     }[];
   *   }[]
   * }>}
   */
  async ai_revlog_meaning(start, limit) {
    return fetchAPI("/api/ai_revlog_meaning", { start, limit }).then((r) =>
      r.json(),
    );
  },
  /**
   * @typedef {'OPENAI_API_KEY'
   * | 'OPENAI_BASE_URL'
   * | 'OPENAI_MODEL'
   * | 'CNPY_MAX_NEW'
   * | 'CNPY_LOCAL_OLLAMA_MODEL'
   * | 'CNPY_LOCAL_OLLAMA_HOST'
   * | 'CNPY_LOCAL_WAIT_FOR_AI_RESULTS'
   * | 'CNPY_LOCAL_TTS_VOICE'
   * | 'CNPY_LOCAL_SYNC_DATABASE'
   * | 'IS_ANKI_CONNECT'
   * | 'ANKI_CONNECT_URL'
   * } EnvKey
   *
   * @param {EnvKey} k
   * @returns {Promise<string>}
   */
  async get_env(k) {
    return fetchAPI(`/api/env/get/${k}`)
      .then((r) => r.json())
      .then((r) => r.v || "");
  },
  /**
   *
   * @param {EnvKey} k
   * @param {string} v
   */
  async set_env(k, v) {
    return fetchAPI(`/api/env/set/${k}`, { v });
  },
  /**
   *
   * @returns {Promise<string | null>}
   */
  async set_sync_db() {
    return fetchAPI("/api/sync/setup")
      .then((r) => r.json())
      .then((r) => r.db);
  },
  async sync_restore() {
    return fetchAPI("/api/sync/restore");
  },
  /**
   * Forward API request to AnkiConnect
   * @see https://git.sr.ht/~foosoft/anki-connect/
   *
   * @param {string} action
   * @param {Record<string, any>} [params]
   * @returns {Promise<{ result: any | null; error: string | null }>}
   */
  async anki(action, params) {
    return fetchAPI("/api/anki", { action, params, version: 6 }).then((r) =>
      r.json(),
    );
  },
};

/**
 *
 * @param {string} url
 * @param {Record<string, any> | null} payload
 * @param {string} method
 * @returns
 */
async function fetchAPI(url, payload = null, method = "POST") {
  const r = await fetch(url, {
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    method,
    body: payload ? JSON.stringify(payload) : null,
  });
  if (!r.ok) {
    throw r;
  }
  return r;
}
