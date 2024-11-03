import {
  patchSFC
} from "./chunk-LMDKOHQF.mjs";

// src/setup-sfc.ts
import {
  createFilter,
  REGEX_NODE_MODULES,
  REGEX_SETUP_SFC
} from "@vue-macros/common";
import { parse } from "@vue/language-core";
var plugin = (_, options = {}) => {
  if (!options) return [];
  const isValidFile = createFilter({
    ...options,
    include: options.include || REGEX_SETUP_SFC,
    exclude: options.exclude || REGEX_NODE_MODULES
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
      const sfc = parse(`${prefix}${content}
</script>`);
      patchSFC(sfc.descriptor.scriptSetup, prefix.length);
      return sfc;
    }
  };
};
var setup_sfc_default = plugin;

export {
  setup_sfc_default
};
