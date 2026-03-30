// ✅ test_ai_search_filter.js
import dotenv from "dotenv";
import { getCompanySymbolAI } from "./src/ai_search_filter.js";
import { fileURLToPath } from "url";
import { dirname, resolve } from "path";
import fs from "fs";

// ------------------------
// Path setup
// ------------------------
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const envPath = resolve(__dirname, ".env");

// ------------------------
// Debugging info
// ------------------------
console.log("🧭 Current Directory:", __dirname);
console.log("🔍 Checking .env at:", envPath);
console.log("📄 Exists:", fs.existsSync(envPath));

// ------------------------
// Load environment variables
// ------------------------
if (fs.existsSync(envPath)) {
  console.log("📂 .env contents:");
  console.log(fs.readFileSync(envPath, "utf8"));
}

dotenv.config({ path: envPath });

// ✅ Fallback (for Windows newline issues)
if (!process.env.GROQ_API_KEY && fs.existsSync(envPath)) {
  const envText = fs.readFileSync(envPath, "utf8").replace(/\r/g, "");
  for (const line of envText.split("\n")) {
    if (!line || line.startsWith("#")) continue;
    const [key, ...valueParts] = line.split("=");
    const value = valueParts.join("=").trim();
    process.env[key.trim()] = value;
  }
}

// ------------------------
// Check loaded values
// ------------------------
console.log("\n✅ Loaded Environment Variables:");
console.log({
  GROQ_API_KEY: process.env.GROQ_API_KEY ? "✓ Present" : "✗ Missing",
  GROQ_API_KEY: process.env.GROQ_API_KEY
    ? "✓ Present"
    : "✗ Missing",
});

// ------------------------
// Run AI Tests
// ------------------------
async function runTests() {
  console.log("\n🚀 Running AI Company Symbol Tests...\n");

  const companies = [
    "Apple",
    "Google",
    "Microsoft",
    "Reliance Industries",
    "HDFC Bank",
    "Adani Power",
    "Tesla",
    "gold",
    "Sony Group Tokyo",
    "RandomUnknownCompanyXYZ",
  ];

  for (const name of companies) {
    try {
      const result = await getCompanySymbolAI(name);
      console.log(`✅ ${name} → ${result}`);
    } catch (err) {
      console.error(`❌ ${name} → Error:`, err.message);
    }
  }

  console.log("\n🧾 All tests finished.");
}

runTests();
