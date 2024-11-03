"use strict";Object.defineProperty(exports, "__esModule", {value: true});// src/short-vmodel.ts
var _shortvmodel = require('@vue-macros/short-vmodel');
var plugin = (_, volarOptions = {}) => {
  if (!volarOptions) return [];
  return {
    name: "vue-macros-short-vmodel",
    version: 2.1,
    resolveTemplateCompilerOptions(options) {
      options.nodeTransforms ||= [];
      options.nodeTransforms.push(
        _shortvmodel.transformShortVmodel.call(void 0, {
          prefix: volarOptions.prefix || "$"
        })
      );
      return options;
    }
  };
};
var short_vmodel_default = plugin;



exports.short_vmodel_default = short_vmodel_default;
