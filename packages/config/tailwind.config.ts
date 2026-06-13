import type { Config } from "tailwindcss";

export default {
  content: ["../../packages/ui/src/**/*.{ts,tsx}", "../../apps/desktop/src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        graphite: "#0f1114",
        matte: "#050607",
        surface: "#14171c",
        border: "#1e2329",
        accent: "#22d3ee",
        muted: "#6b7280",
      },
      fontFamily: {
        sans: ["Geist", "Inter", "system-ui", "sans-serif"],
        mono: ["Geist Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
