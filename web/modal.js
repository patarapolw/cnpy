/** @type {HTMLDivElement} */
let modalContainer = null;
/** @type {HTMLDivElement} */
let overlay = null;

/**
 * Opens a local URL in a modal with tabbed iframes.
 * If called from the main window, creates a new modal.
 * If called from within an iframe, adds a new tab to the modal in the parent window.
 *
 * @param {string} url - The local URL to open.
 * @param {string} title - The title for the tab.
 */
export function openInModal(url, title) {
  // Check if the function is called from within an iframe
  if (window.self !== window.top) {
    // Call the function in the parent window
    window.parent.openInModal(url, title);
    return;
  }

  // Check if the modal container exists
  if (!modalContainer) {
    // Create the overlay
    overlay = document.createElement("div");
    overlay.id = "modal-overlay";
    overlay.addEventListener("click", () => {
      // Close the modal when the overlay is clicked
      document.body.removeChild(modalContainer);
      document.body.removeChild(overlay);
      modalContainer = null;
      overlay = null;
    });
    document.body.appendChild(overlay);

    // Create the modal container
    modalContainer = document.createElement("div");
    modalContainer.id = "modal-container";

    // Create the tab bar
    const tabBar = document.createElement("div");
    tabBar.id = "tab-bar";

    // Create the iframe container
    const iframeContainer = document.createElement("div");
    iframeContainer.id = "iframe-container";

    // Add the tab bar and iframe container to the modal
    modalContainer.appendChild(tabBar);
    modalContainer.appendChild(iframeContainer);

    // Add the modal to the document body
    document.body.appendChild(modalContainer);

    // Add a close button for the modal
    const closeButton = document.createElement("button");
    closeButton.id = "modal-close-button";
    closeButton.innerText = "Close";
    closeButton.addEventListener("click", () => {
      document.body.removeChild(modalContainer);
      document.body.removeChild(overlay);
      modalContainer = null; // Reset the modal container
      overlay = null; // Reset the overlay
    });
    modalContainer.appendChild(closeButton);
  }

  // Add a new tab and iframe
  const tabBar = modalContainer.querySelector("#tab-bar");
  const iframeContainer = modalContainer.querySelector("#iframe-container");

  // Create a new tab
  const tab = document.createElement("div");
  tab.className = "tab";

  const tabTitle = document.createElement("span");
  tabTitle.lang = "zh-CN";
  tabTitle.innerText = title;
  tab.appendChild(tabTitle);

  if (tabBar.children.length > 0) {
    const closeTabButton = document.createElement("button");
    closeTabButton.className = "tab-close-button";
    closeTabButton.innerText = "×";
    closeTabButton.addEventListener("click", () => {
      let nextActiveTab = null;

      if (tab.classList.contains("active")) {
        // Find the previous tab
        const tabs = Array.from(tabBar.children);
        const index = tabs.indexOf(tab);
        nextActiveTab = tabs[index - 1] || tabs[index + 1];
      }

      if (!nextActiveTab) {
        nextActiveTab = Array.from(tabBar.children).find((t) =>
          t.classList.contains("active")
        );
      }

      if (nextActiveTab) {
        setTimeout(() => {
          nextActiveTab.clickTab();
        });
      }

      // Remove the tab and its corresponding iframe
      tabBar.removeChild(tab);
      iframeContainer.removeChild(iframe);

      // If no tabs are left, remove the modal and overlay
      if (tabBar.children.length === 0) {
        document.body.removeChild(modalContainer);
        document.body.removeChild(overlay);
        modalContainer = null;
        overlay = null;
      }
    });

    tab.appendChild(closeTabButton);
  }

  // Create a new iframe
  const iframe = document.createElement("iframe");
  iframe.src = url;
  iframe.className = "iframe";
  iframe.style.display = "none"; // Hide by default

  // Add the tab and iframe to the modal
  tabBar.appendChild(tab);
  iframeContainer.appendChild(iframe);

  // Show the new tab and iframe
  Array.from(tabBar.children).forEach((t) => {
    t.classList.remove("active");
  });
  tab.classList.add("active");

  Array.from(iframeContainer.children).forEach((f) => {
    f.style.display = "none";
  });
  iframe.style.display = "block";

  tab.clickTab = () => {
    // Simulate a click on the tab to show the iframe
    Array.from(tabBar.children).forEach((t) => {
      t.classList.remove("active");
    });
    tab.classList.add("active");

    Array.from(iframeContainer.children).forEach((f) => {
      f.style.display = "none";
    });
    iframe.style.display = "block";
  };

  // Add click event to switch tabs
  tab.addEventListener("click", () => {
    tab.clickTab();
  });
}

// Add styles to the document
const style = document.createElement("style");
style.textContent = /* css */ `
  #modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 999;
  }

  #modal-container {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 80vw;
    max-width: 800px;
    height: 100vh;
    background-color: #fff;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }

  #tab-bar {
    display: flex;
    background-color: #f9f9f9;
    border-bottom: 1px solid #ccc;
    overflow-x: scroll;
    padding-right: 80px;
  }

  #iframe-container {
    flex: 1;
    position: relative;
    background-color: #fff;
  }

  #modal-close-button {
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 1001;
    cursor: pointer;
  }

  .tab {
    display: flex;
    align-items: center;
    padding: 10px;
    border-right: 1px solid #ccc;
    cursor: pointer;
    background-color: #f0f0f0;
    word-break: keep-all;
    white-space: nowrap;
  }

  .tab:hover {
    background-color: #e0e0e0;
  }

  .tab.active {
    background-color: #ffffff;
  }

  .tab-close-button {
    margin-left: 10px;
    cursor: pointer;
  }

  .iframe {
    width: 100%;
    height: 100%;
    border: none;
  }
`;
document.head.appendChild(style);

window.openInModal = openInModal;
