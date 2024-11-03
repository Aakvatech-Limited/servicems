// src/core/transformer.ts
import {
  createSimpleExpression,
  processExpression
} from "@vue/compiler-core";
function transformShortBind(options = {}) {
  const version = options.version || 3.3;
  const reg = new RegExp(
    `^(::${version < 3.4 ? "?" : ""}|\\$|\\*)(?=[A-Z_])`,
    "i"
  );
  return (node, context) => {
    if (node.type !== 1) return;
    for (const prop of node.props) {
      if (reg.test(prop.loc.source) && (prop.type === 6 ? !prop.value : prop.type === 7 ? !prop.exp : false)) {
        const valueName = prop.loc.source.replace(reg, "").replaceAll(/-([A-Z])/gi, (_, name) => name.toUpperCase());
        if (prop.type === 6) {
          prop.value = {
            type: 2,
            content: valueName,
            loc: {
              start: { ...prop.loc.start },
              end: prop.loc.end,
              source: `"${valueName}"`
            }
          };
          prop.loc.start.offset = Number.POSITIVE_INFINITY;
        } else if (prop.type === 7) {
          const simpleExpression = createSimpleExpression(
            valueName,
            false,
            {
              start: {
                offset: prop.loc.start.offset + (prop.loc.source.startsWith("::") ? 2 : 1),
                column: prop.loc.start.column,
                line: prop.loc.start.line
              },
              end: {
                offset: prop.loc.end.offset,
                column: prop.loc.end.column,
                line: prop.loc.end.line
              },
              source: valueName
            },
            0
          );
          if (prop.arg?.type === 4)
            prop.arg.loc.start.offset = Number.POSITIVE_INFINITY;
          prop.exp = processExpression(simpleExpression, context);
        }
      }
    }
  };
}

export {
  transformShortBind
};
