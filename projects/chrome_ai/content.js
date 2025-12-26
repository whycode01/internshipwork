chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "extractText") {
    const text = document.body.innerText || "";
    sendResponse({ text });
  }
});
