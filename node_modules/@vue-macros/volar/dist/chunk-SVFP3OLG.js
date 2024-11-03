"use strict";Object.defineProperty(exports, "__esModule", {value: true}); function _nullishCoalesce(lhs, rhsFn) { if (lhs != null) { return lhs; } else { return rhsFn(); } } function _optionalChain(ops) { let lastAccessLHS = undefined; let value = ops[0]; let i = 1; while (i < ops.length) { const op = ops[i]; const fn = ops[i + 1]; i += 2; if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) { return undefined; } if (op === 'access' || op === 'optionalAccess') { lastAccessLHS = value; value = fn(value); } else if (op === 'call' || op === 'optionalCall') { value = fn((...args) => value.call(lastAccessLHS, ...args)); lastAccessLHS = undefined; } } return value; }


var _chunkA7K2NBSOjs = require('./chunk-A7K2NBSO.js');

// src/define-prop.ts




var _common = require('@vue-macros/common');
function transformDefineProp({
  codes,
  defineProps,
  vueLibName,
  edition
}) {
  _chunkA7K2NBSOjs.addProps.call(void 0, 
    codes,
    defineProps.map((defineProp) => {
      let result = _nullishCoalesce(defineProp.name, () => ( "modelValue"));
      if (!defineProp.required) {
        result += "?";
      }
      result += ": ";
      let type = "any";
      if (defineProp.type) {
        type = defineProp.type;
      } else if (defineProp.defaultValue && defineProp.prop) {
        type = `NonNullable<typeof ${defineProp.prop}${defineProp.isReactivityTransform ? "" : `['value']`}>`;
      }
      result += type;
      return result;
    }),
    vueLibName
  );
  if (edition === "kevinEdition") {
    codes.push(`
declare function $defineProp<T>(
  name: string,
  options: 
    | ({ default: T } & __VLS_PropOptions<T>)
    | ({ required: true } & __VLS_PropOptions<T>)
): T;
declare function $defineProp<T>(
  name?: string,
  options?: __VLS_PropOptions<T>
): T | undefined;
`);
  } else if (edition === "johnsonEdition") {
    codes.push(`
type __VLS_Widen<T> = T extends number | string | boolean | symbol
  ? ReturnType<T['valueOf']>
  : T;
type __VLS_PropOptions<T> = Omit<
  Omit<
    Exclude<import('${vueLibName}').Prop<T>, import('${vueLibName}').PropType<T>>, 
    'default'
  >,
  'required'
>;
declare function $defineProp<T>(
  value: T | (() => T) | undefined,
  required: true,
  options?: __VLS_PropOptions<T>
): __VLS_Widen<T>;
declare function $defineProp<T>(
  value: T | (() => T),
  required?: boolean,
  options?: __VLS_PropOptions<T>
): __VLS_Widen<T>;
declare function $defineProp<T>(
  value?: T | (() => T),
  required?: boolean,
  options?: __VLS_PropOptions<T>
): | __VLS_Widen<T>
   | undefined;
`);
  }
}
function getDefineProp(ts, sfc, edition) {
  const defineProps = [];
  function visitNode(node, parent, isReactivityTransform = false) {
    if (ts.isCallExpression(node) && ts.isIdentifier(node.expression) && [_common.DEFINE_PROP, _common.DEFINE_PROP_DOLLAR].includes(node.expression.escapedText)) {
      if (edition === "kevinEdition") {
        const type = _optionalChain([node, 'access', _ => _.typeArguments, 'optionalAccess', _2 => _2.length]) ? _chunkA7K2NBSOjs.getText.call(void 0, node.typeArguments[0], { ts, sfc }) : void 0;
        const name = node.arguments[0] && ts.isStringLiteral(node.arguments[0]) ? node.arguments[0].text : ts.isVariableDeclaration(parent) && ts.isIdentifier(parent.name) ? parent.name.text : void 0;
        const prop = ts.isVariableDeclaration(parent) && ts.isIdentifier(parent.name) ? parent.name.text : void 0;
        const optionArg = node.arguments[0] && ts.isObjectLiteralExpression(node.arguments[0]) ? node.arguments[0] : node.arguments[1] && ts.isObjectLiteralExpression(node.arguments[1]) ? node.arguments[1] : void 0;
        let required = false;
        let defaultValue;
        if (optionArg) {
          for (const property of optionArg.properties) {
            if (ts.isPropertyAssignment(property) && ts.isIdentifier(property.name)) {
              if (property.name.text === "required" && property.initializer.kind === ts.SyntaxKind.TrueKeyword)
                required = true;
              if (ts.isIdentifier(property.name) && property.name.text === "default")
                defaultValue = _chunkA7K2NBSOjs.getText.call(void 0, property.initializer, { ts, sfc });
            }
          }
        }
        defineProps.push({
          name,
          prop,
          type,
          defaultValue,
          required,
          isReactivityTransform: isReactivityTransform || node.expression.escapedText === _common.DEFINE_PROP_DOLLAR
        });
      } else if (edition === "johnsonEdition" && ts.isVariableDeclaration(parent)) {
        const name = ts.isIdentifier(parent.name) ? parent.name.text : void 0;
        defineProps.push({
          name,
          prop: name,
          defaultValue: node.arguments.length > 0 ? _chunkA7K2NBSOjs.getText.call(void 0, node.arguments[0], { ts, sfc }) : void 0,
          type: _optionalChain([node, 'access', _3 => _3.typeArguments, 'optionalAccess', _4 => _4.length]) ? _chunkA7K2NBSOjs.getText.call(void 0, node.typeArguments[0], { ts, sfc }) : void 0,
          required: node.arguments.length >= 2 && node.arguments[1].kind === ts.SyntaxKind.TrueKeyword,
          isReactivityTransform: isReactivityTransform || node.expression.escapedText === _common.DEFINE_PROP_DOLLAR
        });
      }
    }
  }
  const ast = sfc.scriptSetup.ast;
  ts.forEachChild(ast, (node) => {
    if (ts.isExpressionStatement(node)) {
      visitNode(node.expression, ast);
    } else if (ts.isVariableStatement(node)) {
      ts.forEachChild(node.declarationList, (decl) => {
        if (!ts.isVariableDeclaration(decl) || !decl.initializer) return;
        if (ts.isCallExpression(decl.initializer) && ts.isIdentifier(decl.initializer.expression) && decl.initializer.expression.escapedText === "$" && decl.initializer.arguments.length > 0) {
          visitNode(decl.initializer.arguments[0], decl, true);
        } else {
          visitNode(decl.initializer, decl);
        }
      });
    }
  });
  return defineProps;
}
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  const filter = _common.createFilter.call(void 0, options);
  const {
    modules: { typescript: ts },
    vueCompilerOptions: { experimentalDefinePropProposal, lib }
  } = ctx;
  return {
    name: "vue-macros-define-prop",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName) || !["ts", "tsx"].includes(embeddedFile.lang) || !_optionalChain([sfc, 'access', _5 => _5.scriptSetup, 'optionalAccess', _6 => _6.ast]))
        return;
      const edition = options.edition || experimentalDefinePropProposal || "kevinEdition";
      const defineProps = getDefineProp(ts, sfc, edition);
      if (defineProps.length === 0) return;
      transformDefineProp({
        codes: embeddedFile.content,
        defineProps,
        vueLibName: lib,
        edition
      });
    }
  };
};
var define_prop_default = plugin;



exports.define_prop_default = define_prop_default;
