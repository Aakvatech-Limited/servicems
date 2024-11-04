"use strict";Object.defineProperty(exports, "__esModule", {value: true});// src/short-bind.ts
var _api = require('@vue-macros/short-bind/api');
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  return {
    name: "vue-macros-short-bind",
    version: 2.1,
    resolveTemplateCompilerOptions(options2) {
      options2.nodeTransforms ||= [];
      options2.nodeTransforms.push(
        _api.transformShortBind.call(void 0, { version: ctx.vueCompilerOptions.target })
      );
      return options2;
    }
  };
};
var short_bind_default = plugin;



exports.short_bind_default = short_bind_default;
