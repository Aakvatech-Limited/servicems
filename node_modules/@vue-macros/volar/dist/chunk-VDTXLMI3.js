"use strict";Object.defineProperty(exports, "__esModule", {value: true}); function _optionalChain(ops) { let lastAccessLHS = undefined; let value = ops[0]; let i = 1; while (i < ops.length) { const op = ops[i]; const fn = ops[i + 1]; i += 2; if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) { return undefined; } if (op === 'access' || op === 'optionalAccess') { lastAccessLHS = value; value = fn(value); } else if (op === 'call' || op === 'optionalCall') { value = fn((...args) => value.call(lastAccessLHS, ...args)); lastAccessLHS = undefined; } } return value; }// src/define-slots.ts
var _common = require('@vue-macros/common');
var _mugglestring = require('muggle-string');
function transform({
  codes,
  typeArg,
  vueVersion
}) {
  _mugglestring.replaceSourceRange.call(void 0, 
    codes,
    "scriptSetup",
    typeArg.pos,
    typeArg.pos,
    "__VLS_DefineSlots<"
  );
  _mugglestring.replaceSourceRange.call(void 0, codes, "scriptSetup", typeArg.end, typeArg.end, ">");
  codes.push(
    `type __VLS_DefineSlots<T> = { [SlotName in keyof T]: T[SlotName] extends Function ? T[SlotName] : (_: T[SlotName]) => any };
`
  );
  if (vueVersion < 3) {
    codes.push(
      `declare function defineSlots<S extends Record<string, any> = Record<string, any>>(): S;
`
    );
  }
}
function getTypeArg(ts, sfc) {
  function getCallArg(node) {
    if (!(ts.isCallExpression(node) && ts.isIdentifier(node.expression) && node.expression.escapedText === _common.DEFINE_SLOTS && _optionalChain([node, 'access', _ => _.typeArguments, 'optionalAccess', _2 => _2.length]) === 1))
      return void 0;
    return node.typeArguments[0];
  }
  return ts.forEachChild(sfc.scriptSetup.ast, (node) => {
    if (ts.isExpressionStatement(node)) {
      return getCallArg(node.expression);
    } else if (ts.isVariableStatement(node)) {
      return ts.forEachChild(node.declarationList, (decl) => {
        if (ts.isVariableDeclaration(decl) && decl.initializer)
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
    vueCompilerOptions: { target }
  } = ctx;
  return {
    name: "vue-macros-define-slots",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName) || !["ts", "tsx"].includes(embeddedFile.lang) || !_optionalChain([sfc, 'access', _3 => _3.scriptSetup, 'optionalAccess', _4 => _4.ast]))
        return;
      const typeArg = getTypeArg(ts, sfc);
      if (!typeArg) return;
      transform({
        codes: embeddedFile.content,
        typeArg,
        vueVersion: target
      });
    }
  };
};
var define_slots_default = plugin;



exports.define_slots_default = define_slots_default;
