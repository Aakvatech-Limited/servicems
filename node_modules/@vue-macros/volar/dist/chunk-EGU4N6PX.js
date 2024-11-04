"use strict";Object.defineProperty(exports, "__esModule", {value: true});// src/script-lang.ts
var _common = require('@vue-macros/common');
var _languagecore = require('@vue/language-core');
var plugin = (_, options = {}) => {
  if (!options) return [];
  const filter = _common.createFilter.call(void 0, options);
  return {
    name: "vue-macros-script-lang",
    version: 2.1,
    order: -1,
    parseSFC(fileName, content) {
      if (!filter(fileName)) return;
      const sfc = _languagecore.parse.call(void 0, content);
      const {
        descriptor: { script, scriptSetup }
      } = sfc;
      const lang = options.defaultLang || "ts";
      if (script && !script.attrs.lang) {
        script.lang = lang;
      }
      if (scriptSetup && !scriptSetup.attrs.lang) {
        scriptSetup.lang = lang;
      }
      return sfc;
    }
  };
};
var script_lang_default = plugin;



exports.script_lang_default = script_lang_default;
