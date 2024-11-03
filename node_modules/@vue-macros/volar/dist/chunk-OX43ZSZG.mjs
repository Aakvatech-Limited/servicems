import {
  addProps,
  getStart
} from "./chunk-LMDKOHQF.mjs";

// src/export-props.ts
import { createFilter } from "@vue-macros/common";
import { replaceSourceRange } from "muggle-string";
function transform(options) {
  const { codes, sfc, ts, vueLibName } = options;
  const props = /* @__PURE__ */ Object.create(null);
  let changed = false;
  for (const stmt of sfc.scriptSetup.ast.statements) {
    if (!ts.isVariableStatement(stmt)) continue;
    const exportModifier = stmt.modifiers?.find(
      (m) => m.kind === ts.SyntaxKind.ExportKeyword
    );
    if (!exportModifier) continue;
    replaceSourceRange(
      codes,
      "scriptSetup",
      getStart(exportModifier, options),
      exportModifier.end
    );
    changed = true;
    for (const decl of stmt.declarationList.declarations) {
      if (!ts.isIdentifier(decl.name)) continue;
      props[decl.name.escapedText] = !!decl.initializer;
    }
  }
  if (changed) {
    addProps(
      codes,
      Object.entries(props).map(
        ([prop, optional]) => `${prop}${optional ? "?" : ""}: typeof ${prop}`
      ),
      vueLibName
    );
  }
}
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  const filter = createFilter(options);
  return {
    name: "vue-macros-export-props",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName) || !sfc.scriptSetup?.ast) return;
      transform({
        codes: embeddedFile.content,
        sfc,
        vueLibName: ctx.vueCompilerOptions.lib,
        ts: ctx.modules.typescript
      });
    }
  };
};
var export_props_default = plugin;

export {
  export_props_default
};
