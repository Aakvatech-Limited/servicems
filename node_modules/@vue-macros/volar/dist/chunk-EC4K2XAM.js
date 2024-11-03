"use strict";Object.defineProperty(exports, "__esModule", {value: true}); function _optionalChain(ops) { let lastAccessLHS = undefined; let value = ops[0]; let i = 1; while (i < ops.length) { const op = ops[i]; const fn = ops[i + 1]; i += 2; if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) { return undefined; } if (op === 'access' || op === 'optionalAccess') { lastAccessLHS = value; value = fn(value); } else if (op === 'call' || op === 'optionalCall') { value = fn((...args) => value.call(lastAccessLHS, ...args)); lastAccessLHS = undefined; } } return value; }// src/jsx-ref.ts
var _common = require('@vue-macros/common');
var _mugglestring = require('muggle-string');
function transformRef({
  nodes,
  codes,
  ts,
  source
}) {
  for (const { name, initializer } of nodes) {
    if (ts.isCallExpression(initializer)) {
      _mugglestring.replaceSourceRange.call(void 0, 
        codes,
        source,
        initializer.expression.end,
        initializer.expression.end,
        `<Parameters<NonNullable<typeof __VLS_ctx_${name.text}['expose']>>[0] | null>`
      );
    }
  }
}
function getRefNodes(ts, sourceFile, alias) {
  function isRefCall(node) {
    return ts.isCallExpression(node) && ts.isIdentifier(node.expression) && !_optionalChain([node, 'access', _ => _.typeArguments, 'optionalAccess', _2 => _2.length]) && alias.includes(node.expression.escapedText);
  }
  const result = [];
  function walk(node) {
    if (ts.isVariableStatement(node)) {
      return ts.forEachChild(node.declarationList, (decl) => {
        if (ts.isVariableDeclaration(decl) && ts.isIdentifier(decl.name) && decl.initializer && ts.isCallExpression(decl.initializer) && ts.isIdentifier(decl.initializer.expression)) {
          const initializer = decl.initializer.expression.escapedText === "$" ? decl.initializer.arguments[0] : decl.initializer;
          if (isRefCall(initializer))
            result.push({ name: decl.name, initializer });
        }
      });
    }
    ts.forEachChild(node, walk);
  }
  ts.forEachChild(sourceFile, walk);
  return result;
}
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  const filter = _common.createFilter.call(void 0, options);
  return {
    name: "vue-macros-jsx-ref",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName)) return;
      const ts = ctx.modules.typescript;
      const alias = options.alias || ["useRef"];
      for (const source of ["script", "scriptSetup"]) {
        if (!sfc[source]) continue;
        const nodes = getRefNodes(ts, sfc[source].ast, alias);
        if (nodes.length) {
          transformRef({
            nodes,
            codes: embeddedFile.content,
            ts,
            source
          });
        }
      }
    }
  };
};
var jsx_ref_default = plugin;



exports.jsx_ref_default = jsx_ref_default;
