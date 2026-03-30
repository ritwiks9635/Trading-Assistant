import React from "react";
import TradingViewWidget from "./components/TradingViewWidget";
import ChatBotWidget from "./components/ChatBotWidget";

function App() {
  return (
    <div className="relative h-screen w-full bg-[#0b0e13] overflow-hidden">
      <TradingViewWidget />
      <ChatBotWidget />
    </div>
  );
}

export default App;