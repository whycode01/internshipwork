chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "summarizeText") {
    (async () => {
      const { text, question } = request;
      // NOTE: Remember to replace this with a secure method like chrome.storage!
      const apiKey = "YOUR_GROQ_API_KEY";

      let finalPrompt;

      if (question) {
        // This is the final, most forceful and direct prompt.
        finalPrompt = `You are a direct answer engine. Your task is to answer the user's 'Question'.

**Instructions:**
1.  First, check if the answer to the 'Question' is available in the 'Page Content'. If it is, provide the answer directly from the text.
2.  If the answer is NOT in the 'Page Content', you MUST use your own general knowledge to provide a complete and direct answer.

**CRITICAL RULES:**
- **DO NOT** suggest where to find the answer.
- **DO NOT** explain that the answer isn't on the page.
- **DO NOT** apologize.
- **JUST PROVIDE THE ANSWER** directly. If you do not know the answer or it doesn't exist, say so concisely.

**Question:** "${question}"

**Page Content:**
---
${text}
---`;

      } else {
        // This is the original prompt for summarization when there is no question.
        finalPrompt = `Summarize the following page content in a concise and clear manner:\n\n${text}`;
      }

      const payload = {
        model: "llama3-8b-8192",
        messages: [{ role: "user", content: finalPrompt }]
      };

      try {
        const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${apiKey}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload)
        });

        const data = await response.json();
        sendResponse({ result: data.choices?.[0]?.message?.content || "No response." });
      } catch (error) {
        console.error("Groq API error:", error);
        sendResponse({ result: "Error connecting to Groq API." });
      }
    })();

    // Tell Chrome we're responding asynchronously
    return true;
  }
});