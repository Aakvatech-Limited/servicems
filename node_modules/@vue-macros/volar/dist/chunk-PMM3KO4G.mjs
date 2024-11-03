import {
  addEmits,
  addProps,
  getText
} from "./chunk-LMDKOHQF.mjs";

// src/define-models.ts
import {
  createFilter,
  DEFINE_MODELS,
  DEFINE_MODELS_DOLLAR
} from "@vue-macros/common";
function transformDefineModels(options) {
  const { codes, typeArg, unified, vueLibName, ts } = options;
  const propStrings = [];
  const emitStrings = [];
  if (ts.isTypeLiteralNode(typeArg) && typeArg.members) {
    for (const member of typeArg.members) {
      if (ts.isPropertySignature(member) && member.type) {
        const type = getText(member.type, options);
        let name = getText(member.name, options);
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
  addProps(codes, propStrings, vueLibName);
  addEmits(codes, emitStrings, vueLibName);
}
function getTypeArg(ts, sfc) {
  function getCallArg(node) {
    if (!(ts.isCallExpression(node) && ts.isIdentifier(node.expression) && [DEFINE_MODELS, DEFINE_MODELS_DOLLAR].includes(
      node.expression.escapedText
    ) && node.typeArguments?.length === 1))
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
  const filter = createFilter(options);
  const {
    modules: { typescript: ts },
    vueCompilerOptions: { target, lib }
  } = ctx;
  return {
    name: "vue-macros-define-models",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName) || !["ts", "tsx"].includes(embeddedFile.lang) || !sfc.scriptSetup?.ast)
        return;
      const typeArg = getTypeArg(ts, sfc);
      if (!typeArg) return;
      const unified = target < 3 && (options?.unified ?? true);
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

export {
  define_models_default
};
