"use strict";Object.defineProperty(exports, "__esModule", {value: true}); function _optionalChain(ops) { let lastAccessLHS = undefined; let value = ops[0]; let i = 1; while (i < ops.length) { const op = ops[i]; const fn = ops[i + 1]; i += 2; if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) { return undefined; } if (op === 'access' || op === 'optionalAccess') { lastAccessLHS = value; value = fn(value); } else if (op === 'call' || op === 'optionalCall') { value = fn((...args) => value.call(lastAccessLHS, ...args)); lastAccessLHS = undefined; } } return value; }

var _chunkA7K2NBSOjs = require('./chunk-A7K2NBSO.js');

// src/define-options.ts
var _common = require('@vue-macros/common');
var _languagecore = require('@vue/language-core');
var _mugglestring = require('muggle-string');
function transformDefineOptions({
  codes,
  sfc,
  arg
}) {
  const source = sfc.scriptSetup.content.slice(arg.pos, arg.end);
  const seg = [source, "scriptSetup", arg.pos, _languagecore.allCodeFeatures];
  _mugglestring.replaceAll.call(void 0, codes, _chunkA7K2NBSOjs.REGEX_DEFINE_COMPONENT, "...", seg, ",\n");
}
function getArg(ts, sfc) {
  function getCallArg(node) {
    if (!(ts.isCallExpression(node) && ts.isIdentifier(node.expression) && node.expression.escapedText === _common.DEFINE_OPTIONS))
      return void 0;
    return node.arguments[0];
  }
  const sourceFile = sfc.scriptSetup.ast;
  return ts.forEachChild(sourceFile, (node) => {
    if (ts.isExpressionStatement(node)) {
      return getCallArg(node.expression);
    } else if (ts.isVariableStatement(node)) {
      return ts.forEachChild(node.declarationList, (decl) => {
        if (!ts.isVariableDeclaration(decl) || !decl.initializer) return;
        return getCallArg(decl.initializer);
      });
    }
  });
}
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  const filter = _common.createFilter.call(void 0, options);
  return {
    name: "vue-macros-define-options",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName) || !_optionalChain([sfc, 'access', _ => _.scriptSetup, 'optionalAccess', _2 => _2.ast])) return;
      const arg = getArg(ctx.modules.typescript, sfc);
      if (!arg) return;
      transformDefineOptions({
        codes: embeddedFile.content,
        sfc,
        arg
      });
    }
  };
};
var define_options_default = plugin;



exports.define_options_default = define_options_default;
