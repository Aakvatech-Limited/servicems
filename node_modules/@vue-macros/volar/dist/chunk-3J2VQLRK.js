"use strict";Object.defineProperty(exports, "__esModule", {value: true});// src/define-props.ts
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  ctx.vueCompilerOptions.macros.defineProps.push("$defineProps");
  return {
    name: "vue-macros-define-props",
    version: 2.1
  };
};
var define_props_default = plugin;



exports.define_props_default = define_props_default;
