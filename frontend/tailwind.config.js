/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: "#090D16",
          card: "#121826",
          border: "#1F293D",
          hover: "#1A2333",
          accent: "#3B82F6",
        },
        severity: {
          low: "#10B981",       // emerald green
          medium: "#F59E0B",    // amber yellow
          high: "#EF4444",      // red
          critical: "#D946EF",  // fuchsia purple
        }
      },
      fontFamily: {
        sans: ["Outfit", "Inter", "sans-serif"],
      }
    },
  },
  plugins: [],
}
