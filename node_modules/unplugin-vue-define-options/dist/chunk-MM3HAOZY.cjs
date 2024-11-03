"use strict";Object.defineProperty(exports, "__esModule", {value: true});// src/core/utils.ts
var _common = require('@vue-macros/common');
function filterMacro(stmts) {
  return stmts.map((raw) => {
    let node = raw;
    if (raw.type === "ExpressionStatement") node = raw.expression;
    return _common.isCallOf.call(void 0, node, _common.DEFINE_OPTIONS) ? node : void 0;
  }).filter((node) => !!node);
}
function hasPropsOrEmits(node) {
  return node.properties.some(
    (prop) => (prop.type === "ObjectProperty" || prop.type === "ObjectMethod") && prop.key.type === "Identifier" && (prop.key.name === "props" || prop.key.name === "emits" || prop.key.name === "expose" || prop.key.name === "slots")
  );
}

// src/core/index.ts









var _astwalkerscope = require('ast-walker-scope');
function transformDefineOptions(code, id) {
  if (!code.includes(_common.DEFINE_OPTIONS)) return;
  const sfc = _common.parseSFC.call(void 0, code, id);
  if (!sfc.scriptSetup) return;
  const { scriptSetup, getSetupAst, getScriptAst } = sfc;
  const setupOffset = scriptSetup.loc.start.offset;
  const setupAst = getSetupAst();
  const nodes = filterMacro(setupAst.body);
  if (nodes.length === 0) {
    return;
  } else if (nodes.length > 1)
    throw new SyntaxError(`duplicate ${_common.DEFINE_OPTIONS}() call`);
  const scriptAst = getScriptAst();
  if (scriptAst) checkDefaultExport(scriptAst.body);
  const setupBindings = getRootScopeIds(setupAst);
  const s = new (0, _common.MagicStringAST)(code);
  const [node] = nodes;
  const [arg] = node.arguments;
  if (arg) {
    const normalScript = _common.addNormalScript.call(void 0, sfc, s);
    const scriptOffset = normalScript.start();
    s.appendLeft(
      scriptOffset,
      `
export default /*#__PURE__*/ ${_common.importHelperFn.call(void 0, 
        s,
        scriptOffset,
        "defineComponent"
      )}(`
    );
    if (arg.type === "ObjectExpression" && hasPropsOrEmits(arg))
      throw new SyntaxError(
        `${_common.DEFINE_OPTIONS}() please use defineProps, defineEmits, defineExpose, or defineSlots instead.`
      );
    _common.checkInvalidScopeReference.call(void 0, arg, _common.DEFINE_OPTIONS, setupBindings);
    s.moveNode(arg, scriptOffset, { offset: setupOffset });
    s.remove(setupOffset + node.start, setupOffset + arg.start);
    s.remove(setupOffset + arg.end, setupOffset + node.end);
    s.appendRight(scriptOffset, ");");
    normalScript.end();
  } else {
    s.removeNode(node, { offset: setupOffset });
  }
  return _common.generateTransform.call(void 0, s, id);
}
function checkDefaultExport(stmts) {
  const hasDefaultExport = stmts.some(
    (node) => node.type === "ExportDefaultDeclaration"
  );
  if (hasDefaultExport)
    throw new SyntaxError(
      `${_common.DEFINE_OPTIONS} cannot be used with default export within <script>.`
    );
}
function getRootScopeIds(program) {
  let ids = [];
  _astwalkerscope.walkAST.call(void 0, program, {
    enter(node) {
      if (node.type === "BlockStatement") {
        this.skip();
      }
    },
    leave(node) {
      if (node.type !== "Program") return;
      ids = Object.keys(this.scope);
    }
  });
  return ids;
}





exports.filterMacro = filterMacro; exports.hasPropsOrEmits = hasPropsOrEmits; exports.transformDefineOptions = transformDefineOptions;
