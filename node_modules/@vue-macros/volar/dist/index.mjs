import {
  script_lang_default
} from "./chunk-WOKLXIO4.mjs";
import {
  script_sfc_default
} from "./chunk-32NDNMPQ.mjs";
import {
  setup_jsdoc_default
} from "./chunk-J27G74IZ.mjs";
import {
  setup_sfc_default
} from "./chunk-4XDJ367O.mjs";
import {
  short_bind_default
} from "./chunk-66K37HYT.mjs";
import {
  short_vmodel_default
} from "./chunk-3CSUT5BW.mjs";
import {
  define_props_default
} from "./chunk-NEMA6TM5.mjs";
import {
  define_slots_default
} from "./chunk-BV27BXY2.mjs";
import {
  export_expose_default
} from "./chunk-4YMA3RWS.mjs";
import {
  export_props_default
} from "./chunk-OX43ZSZG.mjs";
import {
  export_render_default
} from "./chunk-DRMYHP2S.mjs";
import {
  jsx_directive_default
} from "./chunk-NX5EPUW3.mjs";
import {
  jsx_ref_default
} from "./chunk-A7NKJ3TS.mjs";
import {
  boolean_prop_default
} from "./chunk-XJ6CSIJE.mjs";
import {
  define_emit_default
} from "./chunk-N2GLCFZH.mjs";
import {
  define_generic_default
} from "./chunk-3RH43H2U.mjs";
import {
  define_models_default
} from "./chunk-PMM3KO4G.mjs";
import {
  define_options_default
} from "./chunk-LS4APYX5.mjs";
import {
  define_prop_default
} from "./chunk-6LBWLHY2.mjs";
import {
  getVolarOptions
} from "./chunk-LMDKOHQF.mjs";
import {
  define_props_refs_default
} from "./chunk-UOEBTKEE.mjs";

// src/index.ts
var plugins = {
  defineOptions: define_options_default,
  defineModels: define_models_default,
  defineProps: define_props_default,
  definePropsRefs: define_props_refs_default,
  shortBind: short_bind_default,
  shortVmodel: short_vmodel_default,
  defineSlots: define_slots_default,
  jsxDirective: jsx_directive_default,
  booleanProp: boolean_prop_default,
  exportRender: export_render_default,
  exportProps: export_props_default,
  exportExpose: export_expose_default,
  defineProp: define_prop_default,
  defineEmit: define_emit_default,
  defineGeneric: define_generic_default,
  setupJsdoc: setup_jsdoc_default,
  setupSFC: setup_sfc_default,
  scriptSFC: script_sfc_default,
  scriptLang: script_lang_default,
  jsxRef: jsx_ref_default
};
var plugin = (ctx) => Object.entries(plugins).flatMap(([name, plugin2]) => {
  const options = getVolarOptions(ctx, name);
  if (!options) return [];
  return plugin2(ctx, options);
});
var src_default = plugin;
export {
  src_default as default
};
