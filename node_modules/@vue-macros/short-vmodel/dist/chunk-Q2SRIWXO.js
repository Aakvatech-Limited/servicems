// src/core/transformer.ts
import {
  createSimpleExpression,
  processExpression
} from "@vue/compiler-core";
function transformShortVmodel({
  prefix = "$"
} = {}) {
  return (node, context) => {
    if (node.type !== 1) return;
    if (prefix === "::") processDirective(node);
    else processAttribute(prefix, node, context);
  };
}
function processDirective(node) {
  for (const [i, prop] of node.props.entries()) {
    if (!(prop.type === 7 && prop.arg?.type === 4 && prop.arg.content.startsWith(":")))
      continue;
    prop.arg.loc.start.offset += 1;
    const argName = prop.arg.content.slice(1);
    node.props[i] = {
      ...prop,
      name: "model",
      arg: argName.length > 0 ? { ...prop.arg, content: prop.arg.content.slice(1) } : void 0
    };
  }
}
function processAttribute(prefix, node, context) {
  for (const [i, prop] of node.props.entries()) {
    if (!(prop.type === 6 && prop.name.startsWith(prefix) && prop.value))
      continue;
    const expLoc = prop.value.loc;
    {
      expLoc.start.offset++;
      expLoc.start.column++;
      expLoc.end.offset--;
      expLoc.end.column--;
      expLoc.source = expLoc.source.slice(1, -1);
    }
    const simpleExpression = createSimpleExpression(
      prop.value.content,
      false,
      expLoc,
      0
    );
    const exp = processExpression(simpleExpression, context);
    const argName = prop.name.slice(prefix.length);
    const arg = argName.length > 0 ? {
      type: 4,
      content: argName,
      constType: 3,
      isStatic: true,
      loc: {
        source: argName,
        start: {
          offset: prop.loc.start.offset + prefix.length,
          column: prop.loc.start.column,
          line: prop.loc.start.line
        },
        end: {
          offset: prop.loc.start.offset + prefix.length + argName.length,
          column: prop.loc.start.column,
          line: prop.loc.start.line
        }
      }
    } : void 0;
    node.props[i] = {
      type: 7,
      name: "model",
      arg,
      exp,
      modifiers: [],
      loc: prop.loc
    };
  }
}

export {
  transformShortVmodel,
  processDirective,
  processAttribute
};
