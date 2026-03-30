/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      backdropBlur: {
        xs: '2px',
      },
      colors: {
        "trading-dark": "#0b0f1a",
        "trading-glow": "#38bdf8",
      },
      boxShadow: {
        'neon': '0 0 25px rgba(56,189,248,0.6)',
      },
    },
  },
  plugins: [],
};
