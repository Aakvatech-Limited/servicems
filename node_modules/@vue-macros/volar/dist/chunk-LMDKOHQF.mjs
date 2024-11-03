// src/common.ts
import path from "node:path";
import process from "node:process";
import {
  resolveOptions
} from "@vue-macros/config";
import { replace, replaceAll } from "muggle-string";
var REGEX_DEFINE_COMPONENT = /(?<=(?:__VLS_|\(await import\(\S+\)\)\.)defineComponent\(\{\n)/g;
function addProps(codes, decl, vueLibName) {
  if (!decl.length || codes.toString().includes("{} as __VLS_TypePropsToOption<"))
    return;
  replace(
    codes,
    /(?<=type __VLS_PublicProps = )/,
    `{
${decl.join(",\n")}
} & `
  );
  replaceAll(
    codes,
    REGEX_DEFINE_COMPONENT,
    "props: {} as __VLS_TypePropsToOption<__VLS_PublicProps>,\n"
  );
  codes.push(
    `type __VLS_NonUndefinedable<T> = T extends undefined ? never : T;
`,
    `type __VLS_TypePropsToOption<T> = { [K in keyof T]-?: {} extends Pick<T, K> ? { type: import('${vueLibName}').PropType<__VLS_NonUndefinedable<T[K]>> } : { type: import('${vueLibName}').PropType<T[K]>, required: true } };
`
  );
  return true;
}
function addEmits(codes, decl, vueLibName) {
  if (!decl.length || codes.toString().includes("{} as __VLS_NormalizeEmits<"))
    return;
  let index = codes.findIndex(
    (code) => code.toString().startsWith("const __VLS_modelEmitsType = ")
  );
  if (index < 0) {
    index = codes.findIndex(
      (code) => code.toString().includes("type __VLS_PublicProps = ")
    );
    codes.splice(
      index,
      0,
      `const __VLS_modelEmitsType = (await import('${vueLibName}')).defineEmits<{
${decl.join(",\n")}
}>();
`,
      `type __VLS_ModelEmitsType = typeof __VLS_modelEmitsType;
`
    );
  } else {
    codes.splice(index + 4, 0, `${decl.join(",\n")}
`);
  }
  replaceAll(
    codes,
    REGEX_DEFINE_COMPONENT,
    "emits: {} as __VLS_NormalizeEmits<__VLS_ModelEmitsType>,\n"
  );
  return true;
}
function addCode(codes, ...args) {
  const index = codes.findIndex(
    (code) => code.includes("__VLS_setup = (async () => {")
  );
  codes.splice(index !== -1 ? index + 1 : codes.length, 0, ...args);
}
var resolvedOptions = /* @__PURE__ */ new Map();
function getVolarOptions(context, key) {
  const configPath = context.compilerOptions.configFilePath;
  const root = typeof configPath === "string" ? path.dirname(configPath) : process.cwd();
  let resolved;
  if (!resolvedOptions.has(root)) {
    resolved = resolveOptions(context.vueCompilerOptions.vueMacros, root);
    resolvedOptions.set(root, resolved);
  }
  return (resolved || resolvedOptions.get(root))[key];
}
function getImportNames(ts, sfc) {
  const names = [];
  const sourceFile = sfc.scriptSetup.ast;
  ts.forEachChild(sourceFile, (node) => {
    if (ts.isImportDeclaration(node) && node.attributes?.elements.some(
      (el) => getText(el.name, { ts, sfc, source: "scriptSetup" }) === "type" && ts.isStringLiteral(el.value) && getText(el.value, { ts, sfc, source: "scriptSetup" }) === "macro"
    )) {
      const name = node.importClause?.name?.escapedText;
      if (name) names.push(name);
      if (node.importClause?.namedBindings) {
        const bindings = node.importClause.namedBindings;
        if (ts.isNamespaceImport(bindings)) {
          names.push(bindings.name.escapedText);
        } else {
          for (const el of bindings.elements) names.push(el.name.escapedText);
        }
      }
    }
  });
  return names;
}
function getStart(node, { ts, sfc, source = "scriptSetup" }) {
  return ts.getTokenPosOfNode(node, sfc[source].ast);
}
function getText(node, context) {
  const { sfc, source = "scriptSetup" } = context;
  return sfc[source].content.slice(getStart(node, context), node.end);
}
function isJsxExpression(node) {
  return node?.kind === 294;
}
function patchSFC(block, offset) {
  if (block) {
    block.loc.start.column -= offset;
    block.loc.start.offset -= offset;
    block.loc.end.offset -= offset;
    if (block.loc.end.line === block.loc.start.line) {
      block.loc.end.column -= offset;
    }
  }
}

export {
  REGEX_DEFINE_COMPONENT,
  addProps,
  addEmits,
  addCode,
  getVolarOptions,
  getImportNames,
  getStart,
  getText,
  isJsxExpression,
  patchSFC
};
