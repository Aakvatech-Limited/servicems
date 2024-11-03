"use strict";Object.defineProperty(exports, "__esModule", {value: true});// src/boolean-prop.ts
var _api = require('@vue-macros/boolean-prop/api');
var plugin = (_, options = {}) => {
  if (!options) return [];
  return {
    name: "vue-macros-boolean-prop",
    version: 2.1,
    resolveTemplateCompilerOptions(options2) {
      options2.nodeTransforms ||= [];
      options2.nodeTransforms.push(
        _api.transformBooleanProp.call(void 0, {
          constType: 0
        })
      );
      return options2;
    }
  };
};
var boolean_prop_default = plugin;



exports.boolean_prop_default = boolean_prop_default;
