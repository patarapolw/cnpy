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
   * }>}
   */
  async due_vocab_list(review_counter = 0) {
    return fetchAPI(`/api/due_vocab_list/${review_counter}`).then((r) =>
      r.json()
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
   * @returns {Promise<{ ok: string | null }>}
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
   * @param {string} url
   * @param {string} title
   * @param {{ width: number, height: number} | { maximized: true } | null} [args]
   */
  async new_window(url, title, args) {
    url = new URL(url, location.origin).href;
    return fetchAPI("/api/new_window", { url, title, args });
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
   * @returns {Promise<{result: string}>}
   */
  async ai_translation(v) {
    return fetchAPI(`/api/ai_translation/${v}`).then((r) => r.json());
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
