// src/boolean-prop.ts
import { transformBooleanProp } from "@vue-macros/boolean-prop/api";
var plugin = (_, options = {}) => {
  if (!options) return [];
  return {
    name: "vue-macros-boolean-prop",
    version: 2.1,
    resolveTemplateCompilerOptions(options2) {
      options2.nodeTransforms ||= [];
      options2.nodeTransforms.push(
        transformBooleanProp({
          constType: 0
        })
      );
      return options2;
    }
  };
};
var boolean_prop_default = plugin;

export {
  boolean_prop_default
};
