"use strict";Object.defineProperty(exports, "__esModule", {value: true});

var _chunk7VQRVCWMcjs = require('./chunk-7VQRVCWM.cjs');

// src/index.ts
var _common = require('@vue-macros/common');
var name = "unplugin-vue-short-bind";
function rollup(options = {}) {
  let api;
  return {
    name,
    enforce: "pre",
    configResolved(config) {
      try {
        api = _common.getVuePluginApi.call(void 0, config.plugins);
      } catch (e) {
      }
    },
    buildStart(rollupOpts) {
      if (api === void 0)
        try {
          api = _common.getVuePluginApi.call(void 0, rollupOpts.plugins);
        } catch (error) {
          this.warn(error);
          return;
        }
      if (!api) return;
      api.options.template ||= {};
      api.options.template.compilerOptions ||= {};
      api.options.template.compilerOptions.nodeTransforms ||= [];
      api.options.template.compilerOptions.nodeTransforms.push(
        _chunk7VQRVCWMcjs.transformShortBind.call(void 0, options)
      );
    }
  };
}
var plugin = {
  rollup,
  rolldown: rollup,
  vite: rollup
};
var src_default = plugin;



exports.src_default = src_default;
