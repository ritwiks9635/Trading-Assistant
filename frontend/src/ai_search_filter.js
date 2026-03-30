import Groq from "groq-sdk";

const groq = new Groq({
  apiKey: process.env.REACT_APP_GROQ_API_KEY,
  dangerouslyAllowBrowser: true,
});

/**
 * 🔍 getCompanySymbolAI(companyName)
 * ---------------------------------
 * Understands user queries for company names (aliases, abbreviations, subsidiaries, etc.)
 * and returns the *main stock ticker* in strict TradingView format: EXCHANGE:SYMBOL.
 */
export async function getCompanySymbolAI(companyName) {
  if (!companyName || companyName.trim() === "") {
    throw new Error("Company name is required.");
  }

  const query = companyName.trim();

  // ✅ Check browser cache
  const cached = localStorage.getItem(`ai_symbol:${query.toLowerCase()}`);
  if (cached) {
    console.log(`📦 Cached Symbol for "${query}" → ${cached}`);
    return cached;
  }

  // 🧠 Professional, expanded AI prompt
  const prompt = `
You are an expert financial data assistant specializing in *global equity mapping*.

Given a company name, abbreviation, alias, or search term from any country,
identify the **main publicly traded parent company** and return its **primary TradingView-compatible ticker**
in the strict format:

EXCHANGE:SYMBOL

✅ RULES:
- Output ONLY the valid ticker, no explanations or markdown.
- Always use the *primary listing* exchange:
  - US: NASDAQ / NYSE
  - India: NSE / BSE
  - Japan: TSE
  - South Korea: KRX
  - UK: LSE
  - Hong Kong: HKEX
  - Europe: EURONEXT / SIX / XETRA
- If the company is private, delisted, or unrecognized → return exactly: UNKNOWN:SYMBOL
- Ensure EXCHANGE and SYMBOL are both uppercase.
- If user input is a subsidiary, map to the parent’s main ticker (e.g., “YouTube” → “NASDAQ:GOOGL”).
- Avoid ETFs or unrelated assets unless query explicitly mentions them.

### Examples
Google → NASDAQ:GOOGL
Alphabet → NASDAQ:GOOGL
Apple → NASDAQ:AAPL
Microsoft → NASDAQ:MSFT
Amazon → NASDAQ:AMZN
Meta → NASDAQ:META
Netflix → NASDAQ:NFLX
Tesla → NASDAQ:TSLA
Nvidia → NASDAQ:NVDA
Intel → NASDAQ:INTC
IBM → NYSE:IBM
Adobe → NASDAQ:ADBE
Oracle → NYSE:ORCL

Tata Consultancy Services → NSE:TCS
TCS → NSE:TCS
Infosys → NSE:INFY
Reliance Industries → NSE:RELIANCE
HDFC Bank → NSE:HDFCBANK
ICICI Bank → NSE:ICICIBANK
State Bank of India → NSE:SBIN
Adani Power → NSE:ADANIPOWER
Bajaj Auto → NSE:BAJAJ-AUTO
Maruti Suzuki → NSE:MARUTI
Larsen & Toubro → NSE:LT
ONGC → NSE:ONGC
Coal India → NSE:COALINDIA
Wipro → NSE:WIPRO
ITC → NSE:ITC

Samsung Electronics → KRX:005930
LG Electronics → KRX:066570
Hyundai Motor → KRX:005380
Toyota → TSE:7203
Sony Group → TSE:6758
SoftBank → TSE:9984
Mitsubishi UFJ → TSE:8306
Hitachi → TSE:6501

BP → LSE:BP
Shell → LSE:SHEL
HSBC → LSE:HSBA
Unilever → LSE:ULVR
AstraZeneca → LSE:AZN

Nestle → SIX:NESN
Roche → SIX:ROG
Siemens → XETRA:SIE
Volkswagen → XETRA:VOW3
TotalEnergies → EURONEXT:TTE
Airbus → EURONEXT:AIR
Sanofi → EURONEXT:SAN

Tencent → HKEX:0700
Alibaba → NYSE:BABA
JD.com → NASDAQ:JD
Baidu → NASDAQ:BIDU
BYD → HKEX:1211

Gold → NYSEARCA:GC
Silver → NYSEARCA:SI
Bitcoin → CRYPTO:BTCUSD
Ethereum → CRYPTO:ETHUSD

Now, provide ONLY the correct TradingView ticker for:
"${companyName}"
`;

  try {
    const response = await groq.chat.completions.create({
      model: "llama-3.3-70b-versatile",
      messages: [{ role: "user", content: prompt }],
      temperature: 0.1,
      max_tokens: 60,
    });

    let output = response?.choices?.[0]?.message?.content?.trim() || "";
    output = output.replace(/[`*#]/g, "").trim();

    // ✅ Ensure strict "EXCHANGE:SYMBOL" format
    const match = output.match(/^[A-Z]+:[A-Z0-9.-]+$/i);
    const finalSymbol = match ? match[0].toUpperCase() : "UNKNOWN:SYMBOL";

    console.log(`🤖 AI resolved "${companyName}" → ${finalSymbol}`);

    localStorage.setItem(`ai_symbol:${query.toLowerCase()}`, finalSymbol);
    return finalSymbol;
  } catch (err) {
    console.error("❌ AI Symbol Resolution Error:", err);
    return "UNKNOWN:SYMBOL";
  }
}
