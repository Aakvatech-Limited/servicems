"use strict";Object.defineProperty(exports, "__esModule", {value: true}); function _optionalChain(ops) { let lastAccessLHS = undefined; let value = ops[0]; let i = 1; while (i < ops.length) { const op = ops[i]; const fn = ops[i + 1]; i += 2; if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) { return undefined; } if (op === 'access' || op === 'optionalAccess') { lastAccessLHS = value; value = fn(value); } else if (op === 'call' || op === 'optionalCall') { value = fn((...args) => value.call(lastAccessLHS, ...args)); lastAccessLHS = undefined; } } return value; }// src/config-worker.ts
var _unconfig = require('unconfig');
async function loadConfigAsync(cwd) {
  const { config } = await _unconfig.loadConfig.call(void 0, {
    sources: [
      {
        files: "vue-macros.config",
        extensions: ["mts", "cts", "ts", "mjs", "cjs", "js", "json", ""],
        loader: "jiti"
      },
      {
        files: "package.json",
        extensions: [],
        rewrite: (config2) => _optionalChain([config2, 'optionalAccess', _ => _.vueMacros])
      }
    ],
    defaults: {},
    cwd
  });
  delete config.plugins;
  return config;
}



exports.loadConfigAsync = loadConfigAsync;
