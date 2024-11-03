// src/config.ts
import { makeSynchronized } from "make-synchronized";
function loadConfig(cwd) {
  const url = import.meta.url;
  const isDist = url.endsWith(".js");
  const filename = "config-worker.js";
  const workerPath = new URL(
    isDist ? `./${filename}` : `../dist/${filename}`,
    url
  );
  const { loadConfigAsync } = makeSynchronized(workerPath);
  return loadConfigAsync(cwd);
}

export {
  loadConfig
};
