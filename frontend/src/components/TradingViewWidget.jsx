import React, { useEffect, useRef, useState, memo } from "react";
import { getCompanySymbolAI } from "../ai_search_filter";
import { motion } from "framer-motion";

function TradingViewWidget() {
  const container = useRef();
  const [symbol, setSymbol] = useState("NASDAQ:GOOGL");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(false);

  // ✅ Load TradingView script dynamically
  const loadWidget = (symbolCode) => {
    if (!container.current) return;
    container.current.innerHTML = "";

    const script = document.createElement("script");
    script.src =
      "https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js";
    script.type = "text/javascript";
    script.async = true;

    script.innerHTML = JSON.stringify(
      {
        symbols: [[`${symbolCode}`, symbolCode.split(":")[1] || "GOOGL"]],
        chartOnly: false,
        autosize: true,
        colorTheme: "dark",
        backgroundColor: "#0a0a0a",
        isTransparent: false,
        locale: "en",
        showFloatingTooltip: true,
        width: "100%",
        height: "100%",
        lineWidth: 2,
        dateRanges: [
          "1d|1",
          "1m|30",
          "3m|60",
          "12m|1D",
          "60m|1W",
          "all|1M",
        ],
        fontFamily: "Poppins, sans-serif",
        fontColor: "#E0E0E0",
      },
      null,
      2
    );

    container.current.appendChild(script);
  };

  useEffect(() => {
    loadWidget(symbol);
  }, [symbol]);

  // ✅ Handle user search
  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchInput.trim()) return;

    try {
      setLoading(true);
      const filteredSymbol = await getCompanySymbolAI(searchInput);
      if (filteredSymbol && filteredSymbol.includes(":")) {
        setSymbol(filteredSymbol);
      } else {
        alert("Invalid or unknown symbol.");
      }
    } catch (err) {
      console.error("AI Filter Error:", err);
      alert("AI filter failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col w-screen h-screen bg-[#0a0a0a] text-white overflow-hidden">
      {/* ✅ Header */}
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="flex justify-between items-center px-8 py-4 bg-gradient-to-r from-[#004aad] via-[#0078d7] to-[#00bfa5] shadow-lg"
      >
        <h1
          className="text-3xl md:text-4xl font-extrabold tracking-wide select-none"
          style={{
            fontFamily: "'Orbitron', sans-serif",
            textShadow: "2px 2px 10px rgba(0,0,0,0.6)",
          }}
        >
          ⚡ Smart TradingView Assistant
        </h1>

        {/* ✅ Search Box */}
        <form
          onSubmit={handleSearch}
          className="flex items-center space-x-2 bg-white/10 rounded-xl px-4 py-2 backdrop-blur-md border border-white/20"
        >
          <input
            type="text"
            placeholder="Search company (e.g. Apple, Reliance)"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="bg-transparent outline-none text-sm md:text-base text-white placeholder-gray-300 w-56"
          />
          <button
            type="submit"
            disabled={loading}
            className={`px-4 py-1.5 rounded-md font-semibold text-sm md:text-base transition-transform ${
              loading
                ? "bg-gray-600 cursor-not-allowed"
                : "bg-gradient-to-r from-green-400 to-blue-500 hover:scale-105"
            }`}
          >
            {loading ? "Filtering..." : "Search"}
          </button>
        </form>
      </motion.header>

      {/* ✅ Fullscreen Chart */}
      <div
        ref={container}
        className="flex-1 tradingview-widget-container w-full h-full"
      >
        <div className="tradingview-widget-container__widget w-full h-full"></div>
      </div>

      {/* ✅ Footer */}
      <footer className="text-gray-400 text-xs text-center py-2 bg-black/40 border-t border-white/10">
        Data powered by{" "}
        <a
          href="https://www.tradingview.com/"
          target="_blank"
          rel="noopener noreferrer nofollow"
          className="text-blue-400 hover:underline"
        >
          TradingView
        </a>
      </footer>
    </div>
  );
}

export default memo(TradingViewWidget);
