const path = require("node:path");
const { defineConfig } = require("vitest/config");

module.exports = defineConfig({
  resolve: {
    alias: {
      "@js": path.resolve(__dirname, "openprescribing/web/static/js"),
    },
  },
  test: {
    environment: "jsdom",
  },
});
