export async function sendChatMessage(query, symbol = "AAPL") {
  try {
    const response = await fetch("http://127.0.0.1:8000/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query, symbol }),
  });

  if (!response.ok) {
    throw new Error("Failed to fetch from backend");
  }

  const data = await response.json();
  return data.response;
  } catch (error) {
    console.error("❌ Chat API Error:", error);
    return "⚠️ Sorry, something went wrong while contacting the AI.";
  }
}
