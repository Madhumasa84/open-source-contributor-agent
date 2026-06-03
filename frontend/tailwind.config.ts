import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#18212f",
        panel: "#f8faf9",
        line: "#d7ddd8",
        pine: "#146356",
        mint: "#d7f4e8",
        amber: "#a15c00",
        steel: "#31516d",
        danger: "#a83f3f"
      },
      boxShadow: {
        focus: "0 0 0 3px rgba(20, 99, 86, 0.18)"
      }
    }
  },
  plugins: []
};

export default config;
