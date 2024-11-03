"use strict";Object.defineProperty(exports, "__esModule", {value: true}); function _optionalChain(ops) { let lastAccessLHS = undefined; let value = ops[0]; let i = 1; while (i < ops.length) { const op = ops[i]; const fn = ops[i + 1]; i += 2; if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) { return undefined; } if (op === 'access' || op === 'optionalAccess') { lastAccessLHS = value; value = fn(value); } else if (op === 'call' || op === 'optionalCall') { value = fn((...args) => value.call(lastAccessLHS, ...args)); lastAccessLHS = undefined; } } return value; }

var _chunkA7K2NBSOjs = require('./chunk-A7K2NBSO.js');

// src/export-render.ts
var _common = require('@vue-macros/common');
var _mugglestring = require('muggle-string');
function transform(options) {
  const { codes, sfc, ts } = options;
  for (const stmt of sfc.scriptSetup.ast.statements) {
    if (!ts.isExportAssignment(stmt)) continue;
    _mugglestring.replaceSourceRange.call(void 0, 
      codes,
      "scriptSetup",
      _chunkA7K2NBSOjs.getStart.call(void 0, stmt, options),
      _chunkA7K2NBSOjs.getStart.call(void 0, stmt.expression, options),
      "defineRender("
    );
    _mugglestring.replaceSourceRange.call(void 0, 
      codes,
      "scriptSetup",
      stmt.expression.end,
      stmt.expression.end,
      ")"
    );
  }
}
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  const filter = _common.createFilter.call(void 0, options);
  return {
    name: "vue-macros-export-render",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName) || !_optionalChain([sfc, 'access', _ => _.scriptSetup, 'optionalAccess', _2 => _2.ast])) return;
      transform({
        codes: embeddedFile.content,
        sfc,
        ts: ctx.modules.typescript
      });
    }
  };
};
var export_render_default = plugin;



exports.export_render_default = export_render_default;
