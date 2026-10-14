/** @type {import('tailwindcss').Config} */
// Same design tokens as the portal prototype: powder blue + warm off-white, deep-ink buttons and a
// high-contrast display serif. `brand` is remapped to the ink/teal scale so existing classes keep working.
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        // Latin glyphs come from Inter / Playfair; Tamil falls through to a system Tamil face.
        sans: ['"Inter Variable"', "Inter", "ui-sans-serif", "system-ui", "Segoe UI", "Noto Sans Tamil", "Nirmala UI", "Latha", "sans-serif"],
        display: ['"Playfair Display Variable"', '"Playfair Display"', "Georgia", "Noto Serif Tamil", "Noto Sans Tamil", "Nirmala UI", "Latha", "serif"],
      },
      colors: {
        ink: { DEFAULT: "#17293A", soft: "#3d4f60", mute: "#66788a" },
        navy: {
          DEFAULT: "#17293A", 50: "#f1f6f8", 100: "#e1ecf0", 200: "#c5d8df", 300: "#9dbcc8",
          400: "#6f9aab", 500: "#4a7a8d", 600: "#33596b", 700: "#233f50", 800: "#1b3040", 900: "#101c27",
        },
        brand: {
          50: "#f1f6f8", 100: "#e1ecf0", 200: "#c5d8df", 300: "#9dbcc8", 400: "#6f9aab",
          500: "#4a7a8d", 600: "#33596b", 700: "#17293A", 800: "#101c27", 900: "#0b141c",
        },
        sky: {
          DEFAULT: "#A9CDD7", 50: "#f0f7f9", 100: "#e0eef2", 200: "#cde4ea", 300: "#b9d9e1",
          400: "#A9CDD7", 500: "#8bb9c6", 600: "#6a9eae",
        },
        paper: "#F6F5F0",
      },
      boxShadow: {
        card: "0 1px 2px rgba(23,41,58,.04), 0 10px 30px -18px rgba(23,41,58,.22)",
        lift: "0 2px 6px rgba(23,41,58,.06), 0 22px 40px -22px rgba(23,41,58,.32)",
        glow: "0 8px 24px -10px rgba(23,41,58,.45)",
      },
      borderRadius: { "2xl": "1.25rem", "3xl": "1.75rem" },
      keyframes: {
        fadeUp: { "0%": { opacity: 0, transform: "translateY(8px)" }, "100%": { opacity: 1, transform: "none" } },
        shimmer: { "100%": { transform: "translateX(100%)" } },
        dot: { "0%,80%,100%": { transform: "scale(.6)", opacity: ".4" }, "40%": { transform: "scale(1)", opacity: "1" } },
      },
      animation: {
        "fade-up": "fadeUp .35s ease-out both",
        dot: "dot 1.2s infinite ease-in-out both",
      },
    },
  },
  plugins: [],
};
