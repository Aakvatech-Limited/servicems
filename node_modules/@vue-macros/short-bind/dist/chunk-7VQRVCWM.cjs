"use strict";Object.defineProperty(exports, "__esModule", {value: true}); function _optionalChain(ops) { let lastAccessLHS = undefined; let value = ops[0]; let i = 1; while (i < ops.length) { const op = ops[i]; const fn = ops[i + 1]; i += 2; if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) { return undefined; } if (op === 'access' || op === 'optionalAccess') { lastAccessLHS = value; value = fn(value); } else if (op === 'call' || op === 'optionalCall') { value = fn((...args) => value.call(lastAccessLHS, ...args)); lastAccessLHS = undefined; } } return value; }// src/core/transformer.ts



var _compilercore = require('@vue/compiler-core');
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
          const simpleExpression = _compilercore.createSimpleExpression.call(void 0, 
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
          if (_optionalChain([prop, 'access', _2 => _2.arg, 'optionalAccess', _3 => _3.type]) === 4)
            prop.arg.loc.start.offset = Number.POSITIVE_INFINITY;
          prop.exp = _compilercore.processExpression.call(void 0, simpleExpression, context);
        }
      }
    }
  };
}



exports.transformShortBind = transformShortBind;
