// src/core/transformer.ts
function transformBooleanProp({
  negativePrefix = "!",
  constType = 3
} = {}) {
  return (node) => {
    if (node.type !== 1) return;
    for (const [i, prop] of node.props.entries()) {
      if (prop.type !== 6 || prop.value !== void 0)
        continue;
      const isNegative = prop.name[0] === negativePrefix;
      const propName = isNegative ? prop.name.slice(1) : prop.name;
      const value = String(!isNegative);
      if (isNegative) prop.loc.start.offset++;
      node.props[i] = {
        type: 7,
        name: "bind",
        arg: {
          type: 4,
          constType: 3,
          content: propName,
          isStatic: true,
          loc: prop.loc
        },
        exp: {
          type: 4,
          constType,
          content: value,
          isStatic: false,
          loc: {
            start: {
              ...prop.loc.start,
              offset: prop.loc.start.offset + 1
            },
            end: prop.loc.end,
            source: value
          }
        },
        loc: prop.loc,
        modifiers: []
      };
    }
  };
}

export {
  transformBooleanProp
};
