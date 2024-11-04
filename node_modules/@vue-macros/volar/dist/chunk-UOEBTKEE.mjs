// src/define-props-refs.ts
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  ctx.vueCompilerOptions.macros.defineProps.push("definePropsRefs");
  return {
    name: "vue-macros-define-props-refs",
    version: 2.1
  };
};
var define_props_refs_default = plugin;

export {
  define_props_refs_default
};
