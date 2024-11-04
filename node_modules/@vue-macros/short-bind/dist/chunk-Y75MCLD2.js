import {
  transformShortBind
} from "./chunk-MJAG5KRU.js";

// src/index.ts
import { getVuePluginApi } from "@vue-macros/common";
var name = "unplugin-vue-short-bind";
function rollup(options = {}) {
  let api;
  return {
    name,
    enforce: "pre",
    configResolved(config) {
      try {
        api = getVuePluginApi(config.plugins);
      } catch {
      }
    },
    buildStart(rollupOpts) {
      if (api === void 0)
        try {
          api = getVuePluginApi(rollupOpts.plugins);
        } catch (error) {
          this.warn(error);
          return;
        }
      if (!api) return;
      api.options.template ||= {};
      api.options.template.compilerOptions ||= {};
      api.options.template.compilerOptions.nodeTransforms ||= [];
      api.options.template.compilerOptions.nodeTransforms.push(
        transformShortBind(options)
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

export {
  src_default
};
