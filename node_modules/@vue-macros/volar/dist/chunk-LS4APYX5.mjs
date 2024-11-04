import {
  REGEX_DEFINE_COMPONENT
} from "./chunk-LMDKOHQF.mjs";

// src/define-options.ts
import { createFilter, DEFINE_OPTIONS } from "@vue-macros/common";
import { allCodeFeatures } from "@vue/language-core";
import { replaceAll } from "muggle-string";
function transformDefineOptions({
  codes,
  sfc,
  arg
}) {
  const source = sfc.scriptSetup.content.slice(arg.pos, arg.end);
  const seg = [source, "scriptSetup", arg.pos, allCodeFeatures];
  replaceAll(codes, REGEX_DEFINE_COMPONENT, "...", seg, ",\n");
}
function getArg(ts, sfc) {
  function getCallArg(node) {
    if (!(ts.isCallExpression(node) && ts.isIdentifier(node.expression) && node.expression.escapedText === DEFINE_OPTIONS))
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
  const filter = createFilter(options);
  return {
    name: "vue-macros-define-options",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName) || !sfc.scriptSetup?.ast) return;
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

export {
  define_options_default
};
