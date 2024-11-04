"use strict";Object.defineProperty(exports, "__esModule", {value: true}); function _optionalChain(ops) { let lastAccessLHS = undefined; let value = ops[0]; let i = 1; while (i < ops.length) { const op = ops[i]; const fn = ops[i + 1]; i += 2; if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) { return undefined; } if (op === 'access' || op === 'optionalAccess') { lastAccessLHS = value; value = fn(value); } else if (op === 'call' || op === 'optionalCall') { value = fn((...args) => value.call(lastAccessLHS, ...args)); lastAccessLHS = undefined; } } return value; }


var _chunkA7K2NBSOjs = require('./chunk-A7K2NBSO.js');

// src/export-props.ts
var _common = require('@vue-macros/common');
var _mugglestring = require('muggle-string');
function transform(options) {
  const { codes, sfc, ts, vueLibName } = options;
  const props = /* @__PURE__ */ Object.create(null);
  let changed = false;
  for (const stmt of sfc.scriptSetup.ast.statements) {
    if (!ts.isVariableStatement(stmt)) continue;
    const exportModifier = _optionalChain([stmt, 'access', _ => _.modifiers, 'optionalAccess', _2 => _2.find, 'call', _3 => _3(
      (m) => m.kind === ts.SyntaxKind.ExportKeyword
    )]);
    if (!exportModifier) continue;
    _mugglestring.replaceSourceRange.call(void 0, 
      codes,
      "scriptSetup",
      _chunkA7K2NBSOjs.getStart.call(void 0, exportModifier, options),
      exportModifier.end
    );
    changed = true;
    for (const decl of stmt.declarationList.declarations) {
      if (!ts.isIdentifier(decl.name)) continue;
      props[decl.name.escapedText] = !!decl.initializer;
    }
  }
  if (changed) {
    _chunkA7K2NBSOjs.addProps.call(void 0, 
      codes,
      Object.entries(props).map(
        ([prop, optional]) => `${prop}${optional ? "?" : ""}: typeof ${prop}`
      ),
      vueLibName
    );
  }
}
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  const filter = _common.createFilter.call(void 0, options);
  return {
    name: "vue-macros-export-props",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName) || !_optionalChain([sfc, 'access', _4 => _4.scriptSetup, 'optionalAccess', _5 => _5.ast])) return;
      transform({
        codes: embeddedFile.content,
        sfc,
        vueLibName: ctx.vueCompilerOptions.lib,
        ts: ctx.modules.typescript
      });
    }
  };
};
var export_props_default = plugin;



exports.export_props_default = export_props_default;
