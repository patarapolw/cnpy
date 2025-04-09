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
    overlay.style.position = "fixed";
    overlay.style.top = "0";
    overlay.style.left = "0";
    overlay.style.width = "100vw";
    overlay.style.height = "100vh";
    overlay.style.backgroundColor = "rgba(0, 0, 0, 0.5)";
    overlay.style.zIndex = "999";
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
    modalContainer.style.position = "fixed";
    modalContainer.style.top = "50%";
    modalContainer.style.left = "50%";
    modalContainer.style.transform = "translate(-50%, -50%)";
    modalContainer.style.width = "80vw";
    modalContainer.style.maxWidth = "800px";
    modalContainer.style.height = "100vh";
    modalContainer.style.backgroundColor = "#fff";
    modalContainer.style.zIndex = "1000";
    modalContainer.style.display = "flex";
    modalContainer.style.flexDirection = "column";
    modalContainer.style.borderRadius = "8px";
    modalContainer.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.2)";

    // Create the tab bar
    const tabBar = document.createElement("div");
    tabBar.id = "tab-bar";
    tabBar.style.display = "flex";
    tabBar.style.backgroundColor = "#f9f9f9";
    tabBar.style.borderBottom = "1px solid #ccc";

    // Create the iframe container
    const iframeContainer = document.createElement("div");
    iframeContainer.id = "iframe-container";
    iframeContainer.style.flex = "1";
    iframeContainer.style.position = "relative";
    iframeContainer.style.backgroundColor = "#fff";

    // Add the tab bar and iframe container to the modal
    modalContainer.appendChild(tabBar);
    modalContainer.appendChild(iframeContainer);

    // Add the modal to the document body
    document.body.appendChild(modalContainer);

    // Add a close button for the modal
    const closeButton = document.createElement("button");
    closeButton.innerText = "Close";
    closeButton.style.position = "absolute";
    closeButton.style.top = "10px";
    closeButton.style.right = "10px";
    closeButton.style.zIndex = "1001";
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
  tab.style.display = "flex";
  tab.style.alignItems = "center";
  tab.style.padding = "10px";
  tab.style.borderRight = "1px solid #ccc";
  tab.style.cursor = "pointer";
  tab.style.backgroundColor = "#f0f0f0";

  const tabTitle = document.createElement("span");
  tabTitle.innerText = title;
  tabTitle.style.flex = "1";

  const closeTabButton = document.createElement("button");
  closeTabButton.innerText = "×";
  closeTabButton.style.marginLeft = "10px";
  closeTabButton.style.cursor = "pointer";
  closeTabButton.addEventListener("click", () => {
    const isTabActive = tab.style.backgroundColor === "#fff";

    // Remove the tab and its corresponding iframe
    tabBar.removeChild(tab);
    iframeContainer.removeChild(iframe);

    // If no tabs are left, remove the modal and overlay
    if (tabBar.children.length === 0) {
      document.body.removeChild(modalContainer);
      document.body.removeChild(overlay);
      modalContainer = null;
      overlay = null;
    } else if (isTabActive) {
      // If the current tab was active, show the last tab
      const lastTab = tabBar.children[tabBar.children.length - 1];
      lastTab.clickTab();
    }
  });

  tab.appendChild(tabTitle);
  tab.appendChild(closeTabButton);

  // Create a new iframe
  const iframe = document.createElement("iframe");
  iframe.src = url;
  iframe.style.width = "100%";
  iframe.style.height = "100%";
  iframe.style.border = "none";
  iframe.style.display = "none"; // Hide by default

  // Add the tab and iframe to the modal
  tabBar.appendChild(tab);
  iframeContainer.appendChild(iframe);

  // Show the new tab and iframe
  Array.from(tabBar.children).forEach((t) => {
    t.style.backgroundColor = "#f0f0f0";
  });
  tab.style.backgroundColor = "#fff";
  Array.from(iframeContainer.children).forEach((f) => {
    f.style.display = "none";
  });
  iframe.style.display = "block";

  tab.clickTab = () => {
    // Simulate a click on the tab to show the iframe
    Array.from(tabBar.children).forEach((t) => {
      t.style.backgroundColor = "#f0f0f0";
    });
    tab.style.backgroundColor = "#fff";

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

window.openInModal = openInModal;
