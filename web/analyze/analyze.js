//@ts-check

const elButtonSubmit = /** @type {HTMLButtonElement} */ (
  document.querySelector('button[type="submit"]')
);
const elButtonReset = /** @type {HTMLButtonElement} */ (
  document.querySelector('button[type="reset"]')
);

const elAnalyzer = /** @type {HTMLElement} */ (
  document.querySelector("#analyzer")
);
const elResult = /** @type {HTMLElement} */ (document.querySelector("#result"));

elButtonSubmit.addEventListener("click", (ev) => {
  ev.preventDefault();

  document
    .querySelectorAll("fieldset")
    .forEach((el) => el.classList.remove("active"));

  elResult.classList.add("active");
});

elButtonReset.addEventListener("click", (ev) => {
  ev.preventDefault();

  document
    .querySelectorAll("fieldset")
    .forEach((el) => el.classList.remove("active"));

  elAnalyzer.classList.add("active");
});
