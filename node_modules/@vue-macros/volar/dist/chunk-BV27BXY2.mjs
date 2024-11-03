// src/define-slots.ts
import { createFilter, DEFINE_SLOTS } from "@vue-macros/common";
import { replaceSourceRange } from "muggle-string";
function transform({
  codes,
  typeArg,
  vueVersion
}) {
  replaceSourceRange(
    codes,
    "scriptSetup",
    typeArg.pos,
    typeArg.pos,
    "__VLS_DefineSlots<"
  );
  replaceSourceRange(codes, "scriptSetup", typeArg.end, typeArg.end, ">");
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
    if (!(ts.isCallExpression(node) && ts.isIdentifier(node.expression) && node.expression.escapedText === DEFINE_SLOTS && node.typeArguments?.length === 1))
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
  const filter = createFilter(options);
  const {
    modules: { typescript: ts },
    vueCompilerOptions: { target }
  } = ctx;
  return {
    name: "vue-macros-define-slots",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName) || !["ts", "tsx"].includes(embeddedFile.lang) || !sfc.scriptSetup?.ast)
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

export {
  define_slots_default
};
