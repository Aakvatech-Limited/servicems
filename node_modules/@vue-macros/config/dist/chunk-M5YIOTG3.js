import {
  loadConfig
} from "./chunk-F77RWMRU.js";

// src/options.ts
import process from "node:process";
import {
  detectVueVersion
} from "@vue-macros/common";
function resolveOptions(options, cwd = process.cwd()) {
  const config = loadConfig(cwd);
  let { isProduction, nuxtContext, plugins, root, version, ...subOptions } = {
    ...config,
    ...options
  };
  root = root || cwd;
  version = version || detectVueVersion(root);
  isProduction = isProduction ?? process.env.NODE_ENV === "production";
  const globalOptions = { isProduction, root, version };
  return {
    isProduction,
    nuxtContext: nuxtContext || {},
    plugins: plugins || {},
    root,
    version,
    betterDefine: resolveSubOptions("betterDefine"),
    booleanProp: resolveSubOptions("booleanProp", false),
    chainCall: resolveSubOptions("chainCall"),
    defineEmit: resolveSubOptions("defineEmit"),
    defineGeneric: resolveSubOptions("defineGeneric"),
    defineModels: resolveSubOptions("defineModels"),
    defineOptions: resolveSubOptions("defineOptions", 3.3),
    defineProp: resolveSubOptions("defineProp"),
    defineProps: resolveSubOptions("defineProps"),
    definePropsRefs: resolveSubOptions("definePropsRefs"),
    defineRender: resolveSubOptions("defineRender"),
    defineSlots: resolveSubOptions("defineSlots", 3.3),
    defineStyleX: resolveSubOptions("defineStyleX", false),
    exportExpose: resolveSubOptions("exportExpose", false),
    exportProps: resolveSubOptions("exportProps", false),
    exportRender: resolveSubOptions("exportRender", false),
    hoistStatic: resolveSubOptions("hoistStatic"),
    jsxDirective: resolveSubOptions("jsxDirective"),
    jsxRef: resolveSubOptions("jsxRef", false),
    namedTemplate: resolveSubOptions("namedTemplate"),
    reactivityTransform: resolveSubOptions("reactivityTransform"),
    scriptLang: resolveSubOptions("scriptLang", false),
    scriptSFC: resolveSubOptions("scriptSFC", false),
    setupBlock: resolveSubOptions("setupBlock", false),
    setupComponent: resolveSubOptions("setupComponent"),
    setupJsdoc: resolveSubOptions("setupJsdoc"),
    setupSFC: resolveSubOptions("setupSFC", false),
    shortBind: resolveSubOptions("shortBind", 3.4),
    shortEmits: resolveSubOptions("shortEmits", 3.3),
    shortVmodel: resolveSubOptions("shortVmodel")
  };
  function resolveSubOptions(name, belowVersion = true) {
    const defaultEnabled = typeof belowVersion === "boolean" ? belowVersion : version < belowVersion;
    const options2 = subOptions[name] ?? defaultEnabled;
    if (!options2) return false;
    return {
      ...globalOptions,
      ...options2 === true ? {} : options2
    };
  }
}

export {
  resolveOptions
};
