"use strict";Object.defineProperty(exports, "__esModule", {value: true}); function _nullishCoalesce(lhs, rhsFn) { if (lhs != null) { return lhs; } else { return rhsFn(); } } function _optionalChain(ops) { let lastAccessLHS = undefined; let value = ops[0]; let i = 1; while (i < ops.length) { const op = ops[i]; const fn = ops[i + 1]; i += 2; if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) { return undefined; } if (op === 'access' || op === 'optionalAccess') { lastAccessLHS = value; value = fn(value); } else if (op === 'call' || op === 'optionalCall') { value = fn((...args) => value.call(lastAccessLHS, ...args)); lastAccessLHS = undefined; } } return value; }



var _chunkA7K2NBSOjs = require('./chunk-A7K2NBSO.js');

// src/define-models.ts




var _common = require('@vue-macros/common');
function transformDefineModels(options) {
  const { codes, typeArg, unified, vueLibName, ts } = options;
  const propStrings = [];
  const emitStrings = [];
  if (ts.isTypeLiteralNode(typeArg) && typeArg.members) {
    for (const member of typeArg.members) {
      if (ts.isPropertySignature(member) && member.type) {
        const type = _chunkA7K2NBSOjs.getText.call(void 0, member.type, options);
        let name = _chunkA7K2NBSOjs.getText.call(void 0, member.name, options);
        if (unified && name === "modelValue") {
          name = "value";
          emitStrings.push(`input: [value: ${type}]`);
        } else {
          emitStrings.push(`'update:${name}': [${name}: ${type}]`);
        }
        propStrings.push(`${name}${member.questionToken ? "?" : ""}: ${type}`);
      }
    }
  }
  _chunkA7K2NBSOjs.addProps.call(void 0, codes, propStrings, vueLibName);
  _chunkA7K2NBSOjs.addEmits.call(void 0, codes, emitStrings, vueLibName);
}
function getTypeArg(ts, sfc) {
  function getCallArg(node) {
    if (!(ts.isCallExpression(node) && ts.isIdentifier(node.expression) && [_common.DEFINE_MODELS, _common.DEFINE_MODELS_DOLLAR].includes(
      node.expression.escapedText
    ) && _optionalChain([node, 'access', _ => _.typeArguments, 'optionalAccess', _2 => _2.length]) === 1))
      return void 0;
    return node.typeArguments[0];
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
  const {
    modules: { typescript: ts },
    vueCompilerOptions: { target, lib }
  } = ctx;
  return {
    name: "vue-macros-define-models",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName) || !["ts", "tsx"].includes(embeddedFile.lang) || !_optionalChain([sfc, 'access', _3 => _3.scriptSetup, 'optionalAccess', _4 => _4.ast]))
        return;
      const typeArg = getTypeArg(ts, sfc);
      if (!typeArg) return;
      const unified = target < 3 && (_nullishCoalesce(_optionalChain([options, 'optionalAccess', _5 => _5.unified]), () => ( true)));
      transformDefineModels({
        codes: embeddedFile.content,
        sfc,
        typeArg,
        vueLibName: lib,
        unified,
        ts
      });
    }
  };
};
var define_models_default = plugin;



exports.define_models_default = define_models_default;
