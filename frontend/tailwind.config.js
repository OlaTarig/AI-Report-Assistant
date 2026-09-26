/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          orange: "#FF971D",        // vibrant — logo/small accents only
          "orange-muted": "#D9730D", // toned-down version for buttons/bubbles/large fills
          "orange-dark": "#B85C0A",  // hover state for orange-muted
          peach: "#FFE8D6",          // light accent — ALWAYS pair with dark text
          offwhite: "#F9F6F7",
          white: "#FFFFFF",
          text: "#3A2E2A",           // dark text for use on peach/light-orange backgrounds
        },
      },
    },
  },
  plugins: [],
};