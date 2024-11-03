// src/config-worker.ts
import { loadConfig } from "unconfig";
async function loadConfigAsync(cwd) {
  const { config } = await loadConfig({
    sources: [
      {
        files: "vue-macros.config",
        extensions: ["mts", "cts", "ts", "mjs", "cjs", "js", "json", ""],
        loader: "jiti"
      },
      {
        files: "package.json",
        extensions: [],
        rewrite: (config2) => config2?.vueMacros
      }
    ],
    defaults: {},
    cwd
  });
  delete config.plugins;
  return config;
}

export {
  loadConfigAsync
};
