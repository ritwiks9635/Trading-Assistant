import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { sendChatMessage } from "../utils/chatApi";

export default function ChatBotWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { id: 1, sender: "bot", text: "👋 Welcome to your AI Trading Assistant." },
    { id: 2, sender: "bot", text: "📊 Market update: NASDAQ trending upward 1.4% today." },
  ]);
  const [input, setInput] = useState("");

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const isSending = useRef(false); 

  // ✅ Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ✅ Auto-focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [isOpen]);

  // ✅ Stable send handler
  const handleSend = async () => {
    if (isSending.current) return; // prevent rapid clicks
    const query = input.trim();
    if (!query) return;

    isSending.current = true;
    const userMessage = { id: Date.now(), sender: "user", text: query };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      const aiResponse = await sendChatMessage(query, "AAPL");
      const botMessage = {
        id: Date.now() + 1,
        sender: "bot",
        text: aiResponse || "⚠️ No response received from AI.",
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 2, sender: "bot", text: "⚠️ Error contacting AI backend." },
      ]);
    } finally {
      isSending.current = false;
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 font-sans select-none">
      {/* Floating Chat Button */}
      {!isOpen && (
        <motion.button
          onClick={() => setIsOpen(true)}
          whileHover={{ scale: 1.15, boxShadow: "0px 0px 25px rgba(56,189,248,0.8)" }}
          whileTap={{ scale: 0.9 }}
          className="p-5 rounded-full bg-gradient-to-br from-sky-500 via-emerald-500 to-teal-400 text-white text-2xl shadow-[0_0_25px_rgba(0,0,0,0.6)] border border-white/30 backdrop-blur-xl transition-all duration-300"
        >
          💬
        </motion.button>
      )}

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.9 }}
            transition={{ duration: 0.45, type: "spring" }}
            className="relative w-[400px] h-[520px] flex flex-col rounded-3xl border border-white/20 
              bg-gradient-to-br from-[#0b0f1a]/95 via-[#111827]/90 to-[#1f2937]/90 
              backdrop-blur-2xl shadow-[0_0_80px_rgba(0,0,0,0.8)] overflow-hidden"
          >
            {/* Floating Aura Lights - ✅ No click blocking */}
            <div className="absolute -top-16 -right-10 w-48 h-48 bg-sky-500/30 rounded-full blur-[90px] animate-pulse pointer-events-none" />
            <div className="absolute -bottom-16 -left-10 w-48 h-48 bg-emerald-400/30 rounded-full blur-[110px] animate-pulse pointer-events-none" />

            {/* Header */}
            <div className="relative flex items-center justify-between px-5 py-3.5 bg-gradient-to-r 
                from-sky-700/60 via-emerald-700/50 to-teal-600/50 
                backdrop-blur-2xl border-b border-white/10 shadow-[0_3px_15px_rgba(0,0,0,0.4)] z-20">
              <div className="flex items-center space-x-3">
                <motion.div
                  animate={{ rotate: [0, 360] }}
                  transition={{ repeat: Infinity, duration: 18, ease: "linear" }}
                  className="w-8 h-8 rounded-full bg-gradient-to-tr from-sky-400 to-emerald-400 
                  flex items-center justify-center shadow-md border border-white/30"
                >
                  <img
                    src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png"
                    alt="bot-logo"
                    className="w-5 h-5"
                  />
                </motion.div>
                <div>
                  <h2 className="text-base font-semibold text-white tracking-wide">
                    AI Trading Analyst
                  </h2>
                  <p className="text-[11px] text-gray-300/80 italic">
                    Real-time market intelligence
                  </p>
                </div>
              </div>
              <motion.button
                whileHover={{ rotate: 90, scale: 1.2 }}
                onClick={() => setIsOpen(false)}
                className="text-white text-lg hover:text-gray-300 transition-all"
              >
                ✕
              </motion.button>
            </div>

            {/* Messages */}
            <div
              className="flex-1 p-4 overflow-y-auto 
                bg-gradient-to-b from-transparent to-black/40 
                scrollbar-thin scrollbar-thumb-sky-700/50 
                scrollbar-track-transparent space-y-3 z-10"
            >
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25 }}
                  className={`flex ${
                    msg.sender === "bot" ? "justify-start" : "justify-end"
                  } items-end space-x-2`}
                >
                  {msg.sender === "bot" && (
                    <img
                      src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png"
                      alt="bot"
                      className="w-6 h-6 rounded-full border border-gray-700 shadow"
                    />
                  )}
                  <div
                    className={`px-3.5 py-2.5 rounded-2xl text-sm max-w-[75%] leading-relaxed 
                    whitespace-pre-wrap break-words backdrop-blur-xl transition-all duration-300 ${
                      msg.sender === "bot"
                        ? "bg-white/10 text-gray-100 border border-white/10 shadow-inner hover:shadow-sky-400/20"
                        : "bg-gradient-to-r from-sky-600 to-emerald-600 text-white shadow-[0_0_15px_rgba(56,189,248,0.4)] hover:shadow-emerald-400/40"
                    }`}
                  >
                    {msg.text}
                  </div>
                  {msg.sender === "user" && (
                    <img
                      src="https://cdn-icons-png.flaticon.com/512/1946/1946429.png"
                      alt="user"
                      className="w-6 h-6 rounded-full border border-gray-700 shadow"
                    />
                  )}
                </motion.div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input (fixed z-index, interaction-safe) */}
            <div className="flex items-center p-3.5 bg-black/40 backdrop-blur-2xl border-t border-white/10 z-30">
              <input
                ref={inputRef}
                type="text"
                placeholder="Type your trading query..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                className="flex-1 px-4 py-2 text-sm text-gray-100 bg-transparent border 
                border-white/20 rounded-full placeholder-gray-400 
                focus:outline-none focus:border-sky-400 transition cursor-text w-full relative z-40"
              />
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                type="button"
                onClick={handleSend}
                className="ml-3 p-3 rounded-full bg-gradient-to-r from-sky-500 to-emerald-500 
                text-white shadow-[0_0_20px_rgba(56,189,248,0.6)] hover:shadow-emerald-400/40 transition-all relative z-40"
              >
                ➤
              </motion.button>
            </div>

            {/* Floating glow ring (✅ no pointer blocking) */}
            <motion.div
              initial={{ opacity: 0.2, scale: 0.8 }}
              animate={{ opacity: [0.3, 0.6, 0.3], scale: [0.95, 1.05, 0.95] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
              className="absolute -bottom-20 -right-10 w-72 h-72 rounded-full bg-gradient-to-tr from-sky-500/20 to-emerald-400/20 blur-[120px] pointer-events-none"
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
