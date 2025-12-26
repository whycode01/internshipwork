document.getElementById("run").addEventListener("click", () => {
  const question = document.getElementById("question").value;

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tabId = tabs[0].id;

    chrome.scripting.executeScript(
      { target: { tabId }, files: ["content.js"] },
      () => {
        if (chrome.runtime.lastError) {
          document.getElementById("output").textContent =
            "⚠️ Script injection failed. Try refreshing the page.";
          return;
        }

        chrome.tabs.sendMessage(tabId, { action: "extractText" }, (response) => {
          if (!response || !response.text) {
            document.getElementById("output").textContent =
              "⚠️ Failed to read tab content. Try refreshing the page.";
            return;
          }

          chrome.runtime.sendMessage(
            { action: "summarizeText", text: response.text, question },
            (reply) => {
              if (chrome.runtime.lastError) {
                document.getElementById("output").textContent =
                  "⚠️ Background script error: " + chrome.runtime.lastError.message;
                return;
              }

              if (!reply || !reply.result) {
                document.getElementById("output").textContent =
                  "⚠️ No response from Groq. Try again later.";
                return;
              }

              document.getElementById("output").textContent = reply.result;
            }
          );
        });
      }
    );
  });
});
