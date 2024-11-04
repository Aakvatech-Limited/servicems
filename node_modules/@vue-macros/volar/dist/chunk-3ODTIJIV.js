"use strict";Object.defineProperty(exports, "__esModule", {value: true}); function _optionalChain(ops) { let lastAccessLHS = undefined; let value = ops[0]; let i = 1; while (i < ops.length) { const op = ops[i]; const fn = ops[i + 1]; i += 2; if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) { return undefined; } if (op === 'access' || op === 'optionalAccess') { lastAccessLHS = value; value = fn(value); } else if (op === 'call' || op === 'optionalCall') { value = fn((...args) => value.call(lastAccessLHS, ...args)); lastAccessLHS = undefined; } } return value; }// src/setup-jsdoc.ts
var _common = require('@vue-macros/common');
var _mugglestring = require('muggle-string');
function hasJSDocNodes(node) {
  if (!node) return false;
  const { jsDoc } = node;
  return !!jsDoc && jsDoc.length > 0;
}
function transform({
  codes,
  sfc,
  ts
}) {
  let jsDoc;
  if (hasJSDocNodes(sfc.scriptSetup.ast.statements[0])) {
    jsDoc = sfc.scriptSetup.ast.statements[0].jsDoc.at(-1);
  }
  for (const stmt of sfc.scriptSetup.ast.statements) {
    if (!ts.isExportAssignment(stmt)) continue;
    if (hasJSDocNodes(stmt)) jsDoc ??= stmt.jsDoc.at(-1);
  }
  if (jsDoc) {
    _mugglestring.replace.call(void 0, 
      codes,
      /(?=export\sdefault)/,
      `${_optionalChain([sfc, 'access', _ => _.scriptSetup, 'optionalAccess', _2 => _2.content, 'access', _3 => _3.slice, 'call', _4 => _4(jsDoc.pos, jsDoc.end)])}
`
    );
  }
}
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  const filter = _common.createFilter.call(void 0, options);
  return {
    name: "vue-macros-setup-jsdoc",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName) || !_optionalChain([sfc, 'access', _5 => _5.scriptSetup, 'optionalAccess', _6 => _6.ast])) return;
      transform({
        codes: embeddedFile.content,
        sfc,
        ts: ctx.modules.typescript
      });
    }
  };
};
var setup_jsdoc_default = plugin;



exports.setup_jsdoc_default = setup_jsdoc_default;
