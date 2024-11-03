import {
  patchSFC
} from "./chunk-LMDKOHQF.mjs";

// src/script-sfc.ts
import { createFilter, REGEX_NODE_MODULES } from "@vue-macros/common";
import { parse } from "@vue/language-core";
var plugin = (_, options = {}) => {
  if (!options) return [];
  const isValidFile = createFilter({
    ...options,
    include: options.include || /\.[cm]?tsx?$/,
    exclude: options.exclude || REGEX_NODE_MODULES
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
      const sfc = parse(`${prefix}${content}
</script>`);
      patchSFC(sfc.descriptor.script, prefix.length);
      return sfc;
    }
  };
};
var script_sfc_default = plugin;

export {
  script_sfc_default
};
