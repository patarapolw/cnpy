//@ts-ignore

const elLogging = /** @type {HTMLPreElement} */ (
  document.getElementById("logging")
);

function log(s) {
  elLogging.innerText += s + "\n";
}

function ready() {
  const elStartButton = /** @type {HTMLButtonElement} */ (
    document.querySelector("button#start")
  );
  elStartButton.disabled = false;
  elStartButton.onclick = start;
  elStartButton.innerText = "Start";

  if (!elLogging.innerText) start();
}

function start() {
  location.href = "./dashboard.html";
}
