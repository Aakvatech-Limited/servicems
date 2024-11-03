"use strict";Object.defineProperty(exports, "__esModule", {value: true}); function _optionalChain(ops) { let lastAccessLHS = undefined; let value = ops[0]; let i = 1; while (i < ops.length) { const op = ops[i]; const fn = ops[i + 1]; i += 2; if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) { return undefined; } if (op === 'access' || op === 'optionalAccess') { lastAccessLHS = value; value = fn(value); } else if (op === 'call' || op === 'optionalCall') { value = fn((...args) => value.call(lastAccessLHS, ...args)); lastAccessLHS = undefined; } } return value; }


var _chunkA7K2NBSOjs = require('./chunk-A7K2NBSO.js');

// src/define-emit.ts
var _common = require('@vue-macros/common');
function getEmitStrings(options) {
  const { ts, sfc } = options;
  const emitStrings = [];
  function walkNode(node, defaultName = "") {
    if (ts.isCallExpression(node) && ts.isIdentifier(node.expression) && _common.DEFINE_EMIT === node.expression.escapedText) {
      const name = node.arguments.length && ts.isStringLiteral(node.arguments[0]) ? node.arguments[0].text : defaultName;
      if (!name) return;
      const type = _optionalChain([node, 'access', _ => _.typeArguments, 'optionalAccess', _2 => _2.length]) === 1 ? ts.isFunctionTypeNode(node.typeArguments[0]) ? `Parameters<${_chunkA7K2NBSOjs.getText.call(void 0, node.typeArguments[0], options)}>` : _chunkA7K2NBSOjs.getText.call(void 0, node.typeArguments[0], options) : "[]";
      emitStrings.push(`'${name}': ${type}`);
    }
  }
  const sourceFile = sfc.scriptSetup.ast;
  ts.forEachChild(sourceFile, (node) => {
    if (ts.isExpressionStatement(node)) {
      walkNode(node.expression);
    } else if (ts.isVariableStatement(node)) {
      ts.forEachChild(node.declarationList, (decl) => {
        if (ts.isVariableDeclaration(decl) && decl.initializer && ts.isIdentifier(decl.name)) {
          walkNode(decl.initializer, decl.name.text);
        }
      });
    }
  });
  return emitStrings;
}
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  const filter = _common.createFilter.call(void 0, options);
  return {
    name: "vue-macros-define-emit",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName) || !["ts", "tsx"].includes(embeddedFile.lang) || !_optionalChain([sfc, 'access', _3 => _3.scriptSetup, 'optionalAccess', _4 => _4.ast]))
        return;
      const emitStrings = getEmitStrings({
        ts: ctx.modules.typescript,
        sfc
      });
      if (!emitStrings.length) return;
      _chunkA7K2NBSOjs.addEmits.call(void 0, embeddedFile.content, emitStrings, ctx.vueCompilerOptions.lib);
    }
  };
};
var define_emit_default = plugin;



exports.define_emit_default = define_emit_default;
