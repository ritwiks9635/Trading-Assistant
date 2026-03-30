import Groq from "groq-sdk";

/**
 * ⚠️ Note: Using API keys client-side is insecure in production.
 * This is okay for private or demo environments only.
 */
const groq = new Groq({
  apiKey: process.env.REACT_APP_GROQ_API_KEY,
  dangerouslyAllowBrowser: true,
});

/**
 * 🔎 getCompanySymbol(companyName)
 * --------------------------------
 * Converts a human-readable company name into a proper TradingView stock symbol.
 * Example:
 *  - "Apple" → "NASDAQ:AAPL"
 *  - "apple" → "NASDAQ:AAPL"
 *  - "Reliance" → "NSE:RELIANCE"
 *  - "hdfc bank" → "NSE:HDFCBANK"
 *  - "tesla" → "NASDAQ:TSLA"
 *  - "sony" → "TSE:6758"
 *  - "hsbc" → "LSE:HSBA"
 *
 * The output strictly follows this format: "EXCHANGE:SYMBOL"
 *
 * @param {string} companyName - Raw user input (any case, format)
 * @returns {Promise<string>} - Properly formatted TradingView symbol
 */

export async function getCompanySymbol(companyName) {
  if (!companyName || companyName.trim() === "") {
    throw new Error("Company name is required for AI symbol filtering.");
  }

  const prompt = `
You are a highly accurate financial data assistant. 
Your job is to identify the correct stock ticker and exchange for a given company name, 
and output it in **TradingView format**: "EXCHANGE:SYMBOL".

### STRICT RULES:
1. Always respond with only one line in the format "EXCHANGE:SYMBOL"
2. Do not include any explanations, markdown, code blocks, or extra text.
3. Match company names accurately regardless of letter case, spacing, or variations.
4. Use the most common exchange where the company’s main stock trades.
5. Output must be compatible with TradingView.

### EXAMPLES:
Apple → NASDAQ:AAPL  
apple → NASDAQ:AAPL  
APPLE → NASDAQ:AAPL  
Google → NASDAQ:GOOGL  
Alphabet Inc → NASDAQ:GOOGL  
Microsoft → NASDAQ:MSFT  
intel → NASDAQ:INTC  
Tesla Motors → NASDAQ:TSLA  
Amazon → NASDAQ:AMZN  
Netflix → NASDAQ:NFLX  
NVIDIA → NASDAQ:NVDA  
Meta → NASDAQ:META  

Reliance → NSE:RELIANCE  
reliance industries → NSE:RELIANCE  
hdfc bank → NSE:HDFCBANK  
ICICI → NSE:ICICIBANK  
Tata Motors → NSE:TATAMOTORS  
Infosys → NSE:INFY  
Wipro → NSE:WIPRO  

Toyota → TSE:7203  
Sony → TSE:6758  
SoftBank → TSE:9984  
HSBC → LSE:HSBA  
OKLO → NYSE:OKLO  
Shell → LSE:SHEL  
Samsung → KRX:005930  
Alibaba → HKEX:9988  

Now convert this company name into the correct TradingView symbol:
"${companyName.trim()}"
`;

  try {
    const response = await groq.chat.completions.create({
      model: "llama3-8b-8192", // ✅ fast, accurate Groq model
      messages: [{ role: "user", content: prompt }],
      temperature: 0.2,
      max_tokens: 40,
    });

    const symbol =
      response?.choices?.[0]?.message?.content?.trim() || "UNKNOWN:SYMBOL";

    console.log(`🔹 AI Mapped "${companyName}" → ${symbol}`);
    return symbol;
  } catch (error) {
    console.error("❌ Groq Filter Error:", error);
    return "UNKNOWN:SYMBOL";
  }
}