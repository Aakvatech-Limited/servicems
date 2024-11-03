"use strict";Object.defineProperty(exports, "__esModule", {value: true});

var _chunk76SQVUDRcjs = require('./chunk-76SQVUDR.cjs');

// src/config.ts
var _makesynchronized = require('make-synchronized');
function loadConfig(cwd) {
  const url = _chunk76SQVUDRcjs.importMetaUrl;
  const isDist = url.endsWith(".js");
  const filename = "config-worker.js";
  const workerPath = new URL(
    isDist ? `./${filename}` : `../dist/${filename}`,
    url
  );
  const { loadConfigAsync } = _makesynchronized.makeSynchronized.call(void 0, workerPath);
  return loadConfigAsync(cwd);
}



exports.loadConfig = loadConfig;
