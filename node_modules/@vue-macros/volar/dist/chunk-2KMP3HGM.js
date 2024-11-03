"use strict";Object.defineProperty(exports, "__esModule", {value: true});

var _chunkA7K2NBSOjs = require('./chunk-A7K2NBSO.js');

// src/setup-sfc.ts




var _common = require('@vue-macros/common');
var _languagecore = require('@vue/language-core');
var plugin = (_, options = {}) => {
  if (!options) return [];
  const isValidFile = _common.createFilter.call(void 0, {
    ...options,
    include: options.include || _common.REGEX_SETUP_SFC,
    exclude: options.exclude || _common.REGEX_NODE_MODULES
  });
  return {
    name: "vue-macros-setup-sfc",
    version: 2.1,
    order: -1,
    isValidFile,
    parseSFC2(fileName, _2, content) {
      if (!isValidFile(fileName)) return;
      const lang = fileName.split(/\.[cm]?/).at(-1);
      const prefix = `<script setup lang="${lang}">`;
      const sfc = _languagecore.parse.call(void 0, `${prefix}${content}
</script>`);
      _chunkA7K2NBSOjs.patchSFC.call(void 0, sfc.descriptor.scriptSetup, prefix.length);
      return sfc;
    }
  };
};
var setup_sfc_default = plugin;



exports.setup_sfc_default = setup_sfc_default;
