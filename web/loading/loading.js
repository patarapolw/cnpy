//@ts-ignore

const elLogging = /** @type {HTMLPreElement} */ (
  document.getElementById("logging")
);

function log(s) {
  elLogging.innerText += s + "\n";
}
