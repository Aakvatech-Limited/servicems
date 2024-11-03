// src/short-bind.ts
import { transformShortBind } from "@vue-macros/short-bind/api";
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  return {
    name: "vue-macros-short-bind",
    version: 2.1,
    resolveTemplateCompilerOptions(options2) {
      options2.nodeTransforms ||= [];
      options2.nodeTransforms.push(
        transformShortBind({ version: ctx.vueCompilerOptions.target })
      );
      return options2;
    }
  };
};
var short_bind_default = plugin;

export {
  short_bind_default
};
