// src/setup-jsdoc.ts
import { createFilter } from "@vue-macros/common";
import { replace } from "muggle-string";
function hasJSDocNodes(node) {
  if (!node) return false;
  const { jsDoc } = node;
  return !!jsDoc && jsDoc.length > 0;
}
function transform({
  codes,
  sfc,
  ts
}) {
  let jsDoc;
  if (hasJSDocNodes(sfc.scriptSetup.ast.statements[0])) {
    jsDoc = sfc.scriptSetup.ast.statements[0].jsDoc.at(-1);
  }
  for (const stmt of sfc.scriptSetup.ast.statements) {
    if (!ts.isExportAssignment(stmt)) continue;
    if (hasJSDocNodes(stmt)) jsDoc ??= stmt.jsDoc.at(-1);
  }
  if (jsDoc) {
    replace(
      codes,
      /(?=export\sdefault)/,
      `${sfc.scriptSetup?.content.slice(jsDoc.pos, jsDoc.end)}
`
    );
  }
}
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  const filter = createFilter(options);
  return {
    name: "vue-macros-setup-jsdoc",
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
var setup_jsdoc_default = plugin;

export {
  setup_jsdoc_default
};
