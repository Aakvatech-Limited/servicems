"use strict";Object.defineProperty(exports, "__esModule", {value: true});

var _chunkEGU4N6PXjs = require('./chunk-EGU4N6PX.js');


var _chunkVGFNHJYZjs = require('./chunk-VGFNHJYZ.js');


var _chunk3ODTIJIVjs = require('./chunk-3ODTIJIV.js');


var _chunk2KMP3HGMjs = require('./chunk-2KMP3HGM.js');


var _chunkHEQSPOZHjs = require('./chunk-HEQSPOZH.js');


var _chunkTIOHFKS7js = require('./chunk-TIOHFKS7.js');


var _chunk3J2VQLRKjs = require('./chunk-3J2VQLRK.js');


var _chunkVDTXLMI3js = require('./chunk-VDTXLMI3.js');


var _chunk7KGMYMRAjs = require('./chunk-7KGMYMRA.js');


var _chunk5RFEHGR4js = require('./chunk-5RFEHGR4.js');


var _chunkUSM4NAX2js = require('./chunk-USM4NAX2.js');


var _chunk37ZS65BEjs = require('./chunk-37ZS65BE.js');


var _chunkEC4K2XAMjs = require('./chunk-EC4K2XAM.js');


var _chunkSQNWMKHKjs = require('./chunk-SQNWMKHK.js');


var _chunkJVL567JRjs = require('./chunk-JVL567JR.js');


var _chunkAMTMEGOLjs = require('./chunk-AMTMEGOL.js');


var _chunkC6RK5E5Cjs = require('./chunk-C6RK5E5C.js');


var _chunkUVDVPLOEjs = require('./chunk-UVDVPLOE.js');


var _chunkSVFP3OLGjs = require('./chunk-SVFP3OLG.js');


var _chunkA7K2NBSOjs = require('./chunk-A7K2NBSO.js');


var _chunkPEB2SWHRjs = require('./chunk-PEB2SWHR.js');

// src/index.ts
var plugins = {
  defineOptions: _chunkUVDVPLOEjs.define_options_default,
  defineModels: _chunkC6RK5E5Cjs.define_models_default,
  defineProps: _chunk3J2VQLRKjs.define_props_default,
  definePropsRefs: _chunkPEB2SWHRjs.define_props_refs_default,
  shortBind: _chunkHEQSPOZHjs.short_bind_default,
  shortVmodel: _chunkTIOHFKS7js.short_vmodel_default,
  defineSlots: _chunkVDTXLMI3js.define_slots_default,
  jsxDirective: _chunk37ZS65BEjs.jsx_directive_default,
  booleanProp: _chunkSQNWMKHKjs.boolean_prop_default,
  exportRender: _chunkUSM4NAX2js.export_render_default,
  exportProps: _chunk5RFEHGR4js.export_props_default,
  exportExpose: _chunk7KGMYMRAjs.export_expose_default,
  defineProp: _chunkSVFP3OLGjs.define_prop_default,
  defineEmit: _chunkJVL567JRjs.define_emit_default,
  defineGeneric: _chunkAMTMEGOLjs.define_generic_default,
  setupJsdoc: _chunk3ODTIJIVjs.setup_jsdoc_default,
  setupSFC: _chunk2KMP3HGMjs.setup_sfc_default,
  scriptSFC: _chunkVGFNHJYZjs.script_sfc_default,
  scriptLang: _chunkEGU4N6PXjs.script_lang_default,
  jsxRef: _chunkEC4K2XAMjs.jsx_ref_default
};
var plugin = (ctx) => Object.entries(plugins).flatMap(([name, plugin2]) => {
  const options = _chunkA7K2NBSOjs.getVolarOptions.call(void 0, ctx, name);
  if (!options) return [];
  return plugin2(ctx, options);
});
var src_default = plugin;


exports.default = src_default;

module.exports = exports.default;
