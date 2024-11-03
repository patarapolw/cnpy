//@ts-check

import { api } from "./api.js";

const utterance = new SpeechSynthesisUtterance();
utterance.lang = "zh-CN";

/**
 *
 * @param {string} s
 */
export function speak(s) {
  utterance.text = s;
  speechSynthesis.speak(utterance);
}

/**
 *
 * @param {string} s
 * @param {boolean} [isFuzzy]
 * @returns
 */
export function normalize_pinyin(s, isFuzzy) {
  s = s.replace(/[vü]/g, "u:").replace(/ /g, "").toLocaleLowerCase();
  if (isFuzzy) {
    s = s.replace(/\d+/g, " ");
  }
  return s;
}

/**
 *
 * @param {string} a
 * @param {string} b
 * @param {boolean} [isFuzzy]
 * @returns
 */
export function comp_pinyin(a, b, isFuzzy) {
  return normalize_pinyin(a, isFuzzy) === normalize_pinyin(b, isFuzzy);
}

/**
 *
 * @param {string} v
 */
export async function openItem(v) {
  const r = await api.set_vocab_for_quiz(v);
  if (r.ok) {
    api.new_window("./quiz.html", v);
  } else {
    alert(`Invalid vocab: ${v}`);
  }
}
