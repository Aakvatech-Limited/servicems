"use strict";Object.defineProperty(exports, "__esModule", {value: true}); function _optionalChain(ops) { let lastAccessLHS = undefined; let value = ops[0]; let i = 1; while (i < ops.length) { const op = ops[i]; const fn = ops[i + 1]; i += 2; if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) { return undefined; } if (op === 'access' || op === 'optionalAccess') { lastAccessLHS = value; value = fn(value); } else if (op === 'call' || op === 'optionalCall') { value = fn((...args) => value.call(lastAccessLHS, ...args)); lastAccessLHS = undefined; } } return value; }

var _chunkA7K2NBSOjs = require('./chunk-A7K2NBSO.js');

// src/define-generic.ts
var _common = require('@vue-macros/common');
var _mugglestring = require('muggle-string');
function getDefineGenerics(ts, sfc, codes) {
  const result = [];
  const sourceFile = sfc.scriptSetup.ast;
  ts.forEachChild(sourceFile, (node) => {
    if (ts.isTypeAliasDeclaration(node) && ts.isTypeReferenceNode(node.type) && ts.isIdentifier(node.type.typeName) && node.type.typeName.escapedText === "DefineGeneric") {
      if (!_optionalChain([node, 'access', _ => _.type, 'access', _2 => _2.typeArguments, 'optionalAccess', _3 => _3.length])) {
        _mugglestring.replaceSourceRange.call(void 0, 
          codes,
          "scriptSetup",
          node.name.pos,
          node.name.end,
          ` _${node.name.escapedText}`
        );
        _mugglestring.replaceSourceRange.call(void 0, 
          codes,
          "scriptSetup",
          node.type.end,
          node.type.end,
          `<${node.name.escapedText}>`
        );
      }
      const typeArgument = _optionalChain([node, 'access', _4 => _4.type, 'access', _5 => _5.typeArguments, 'optionalAccess', _6 => _6[0]]) ? ` extends ${_chunkA7K2NBSOjs.getText.call(void 0, node.type.typeArguments[0], { ts, sfc })}` : "";
      const defaultType = _optionalChain([node, 'access', _7 => _7.type, 'access', _8 => _8.typeArguments, 'optionalAccess', _9 => _9[1]]) ? ` = ${_chunkA7K2NBSOjs.getText.call(void 0, node.type.typeArguments[1], { ts, sfc })}` : "";
      result.push(`${node.name.escapedText}${typeArgument}${defaultType}`);
    }
  });
  return result;
}
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  const filter = _common.createFilter.call(void 0, options);
  return [
    {
      name: "vue-macros-define-generic-pre",
      version: 2.1,
      order: -1,
      resolveEmbeddedCode(fileName, sfc) {
        if (filter(fileName) && !_optionalChain([sfc, 'access', _10 => _10.scriptSetup, 'optionalAccess', _11 => _11.attrs, 'access', _12 => _12.generic]) && _optionalChain([sfc, 'access', _13 => _13.scriptSetup, 'optionalAccess', _14 => _14.content, 'access', _15 => _15.includes, 'call', _16 => _16("DefineGeneric")])) {
          sfc.scriptSetup.attrs.generic = "T";
        }
      }
    },
    {
      name: "vue-macros-define-generic",
      version: 2.1,
      resolveEmbeddedCode(fileName, sfc, embeddedFile) {
        if (!filter(fileName) || !_optionalChain([sfc, 'access', _17 => _17.scriptSetup, 'optionalAccess', _18 => _18.ast])) return;
        const defineGenerics = getDefineGenerics(
          ctx.modules.typescript,
          sfc,
          embeddedFile.content
        );
        if (!defineGenerics.length) return;
        _mugglestring.replace.call(void 0, 
          embeddedFile.content,
          /(?<=export\sdefault\s\(<).*(?=,>)/,
          defineGenerics.join(", ")
        );
      }
    }
  ];
};
var define_generic_default = plugin;



exports.define_generic_default = define_generic_default;
