import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          900: "#0f172a",
        },
        accent: {
          500: "#8b5cf6",
          600: "#7c3aed",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        "indigo-glow": "0 4px 14px 0 rgba(79, 70, 229, 0.3)",
      },
      backgroundImage: {
        "hero-gradient": "linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%)",
      },
    },
  },
  plugins: [],
} satisfies Config;
