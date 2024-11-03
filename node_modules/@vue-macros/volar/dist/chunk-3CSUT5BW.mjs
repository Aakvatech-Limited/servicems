// src/short-vmodel.ts
import { transformShortVmodel } from "@vue-macros/short-vmodel";
var plugin = (_, volarOptions = {}) => {
  if (!volarOptions) return [];
  return {
    name: "vue-macros-short-vmodel",
    version: 2.1,
    resolveTemplateCompilerOptions(options) {
      options.nodeTransforms ||= [];
      options.nodeTransforms.push(
        transformShortVmodel({
          prefix: volarOptions.prefix || "$"
        })
      );
      return options;
    }
  };
};
var short_vmodel_default = plugin;

export {
  short_vmodel_default
};
