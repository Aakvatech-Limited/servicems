"use strict";Object.defineProperty(exports, "__esModule", {value: true});

var _chunkA7K2NBSOjs = require('./chunk-A7K2NBSO.js');

// src/script-sfc.ts
var _common = require('@vue-macros/common');
var _languagecore = require('@vue/language-core');
var plugin = (_, options = {}) => {
  if (!options) return [];
  const isValidFile = _common.createFilter.call(void 0, {
    ...options,
    include: options.include || /\.[cm]?tsx?$/,
    exclude: options.exclude || _common.REGEX_NODE_MODULES
  });
  return {
    name: "vue-macros-script-sfc",
    version: 2.1,
    order: -1,
    isValidFile,
    parseSFC2(fileName, _2, content) {
      if (!isValidFile(fileName)) return;
      const lang = fileName.split(/\.[cm]?/).at(-1);
      const prefix = `<script lang="${lang}">`;
      const sfc = _languagecore.parse.call(void 0, `${prefix}${content}
</script>`);
      _chunkA7K2NBSOjs.patchSFC.call(void 0, sfc.descriptor.script, prefix.length);
      return sfc;
    }
  };
};
var script_sfc_default = plugin;



exports.script_sfc_default = script_sfc_default;
