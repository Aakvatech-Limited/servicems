import {
  getStart
} from "./chunk-LMDKOHQF.mjs";

// src/export-render.ts
import { createFilter } from "@vue-macros/common";
import { replaceSourceRange } from "muggle-string";
function transform(options) {
  const { codes, sfc, ts } = options;
  for (const stmt of sfc.scriptSetup.ast.statements) {
    if (!ts.isExportAssignment(stmt)) continue;
    replaceSourceRange(
      codes,
      "scriptSetup",
      getStart(stmt, options),
      getStart(stmt.expression, options),
      "defineRender("
    );
    replaceSourceRange(
      codes,
      "scriptSetup",
      stmt.expression.end,
      stmt.expression.end,
      ")"
    );
  }
}
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  const filter = createFilter(options);
  return {
    name: "vue-macros-export-render",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName) || !sfc.scriptSetup?.ast) return;
      transform({
        codes: embeddedFile.content,
        sfc,
        ts: ctx.modules.typescript
      });
    }
  };
};
var export_render_default = plugin;

export {
  export_render_default
};
