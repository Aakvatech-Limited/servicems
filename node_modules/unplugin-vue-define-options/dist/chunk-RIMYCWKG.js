// src/core/utils.ts
import { DEFINE_OPTIONS, isCallOf } from "@vue-macros/common";
function filterMacro(stmts) {
  return stmts.map((raw) => {
    let node = raw;
    if (raw.type === "ExpressionStatement") node = raw.expression;
    return isCallOf(node, DEFINE_OPTIONS) ? node : void 0;
  }).filter((node) => !!node);
}
function hasPropsOrEmits(node) {
  return node.properties.some(
    (prop) => (prop.type === "ObjectProperty" || prop.type === "ObjectMethod") && prop.key.type === "Identifier" && (prop.key.name === "props" || prop.key.name === "emits" || prop.key.name === "expose" || prop.key.name === "slots")
  );
}

// src/core/index.ts
import {
  addNormalScript,
  checkInvalidScopeReference,
  DEFINE_OPTIONS as DEFINE_OPTIONS2,
  generateTransform,
  importHelperFn,
  MagicStringAST,
  parseSFC
} from "@vue-macros/common";
import { walkAST } from "ast-walker-scope";
function transformDefineOptions(code, id) {
  if (!code.includes(DEFINE_OPTIONS2)) return;
  const sfc = parseSFC(code, id);
  if (!sfc.scriptSetup) return;
  const { scriptSetup, getSetupAst, getScriptAst } = sfc;
  const setupOffset = scriptSetup.loc.start.offset;
  const setupAst = getSetupAst();
  const nodes = filterMacro(setupAst.body);
  if (nodes.length === 0) {
    return;
  } else if (nodes.length > 1)
    throw new SyntaxError(`duplicate ${DEFINE_OPTIONS2}() call`);
  const scriptAst = getScriptAst();
  if (scriptAst) checkDefaultExport(scriptAst.body);
  const setupBindings = getRootScopeIds(setupAst);
  const s = new MagicStringAST(code);
  const [node] = nodes;
  const [arg] = node.arguments;
  if (arg) {
    const normalScript = addNormalScript(sfc, s);
    const scriptOffset = normalScript.start();
    s.appendLeft(
      scriptOffset,
      `
export default /*#__PURE__*/ ${importHelperFn(
        s,
        scriptOffset,
        "defineComponent"
      )}(`
    );
    if (arg.type === "ObjectExpression" && hasPropsOrEmits(arg))
      throw new SyntaxError(
        `${DEFINE_OPTIONS2}() please use defineProps, defineEmits, defineExpose, or defineSlots instead.`
      );
    checkInvalidScopeReference(arg, DEFINE_OPTIONS2, setupBindings);
    s.moveNode(arg, scriptOffset, { offset: setupOffset });
    s.remove(setupOffset + node.start, setupOffset + arg.start);
    s.remove(setupOffset + arg.end, setupOffset + node.end);
    s.appendRight(scriptOffset, ");");
    normalScript.end();
  } else {
    s.removeNode(node, { offset: setupOffset });
  }
  return generateTransform(s, id);
}
function checkDefaultExport(stmts) {
  const hasDefaultExport = stmts.some(
    (node) => node.type === "ExportDefaultDeclaration"
  );
  if (hasDefaultExport)
    throw new SyntaxError(
      `${DEFINE_OPTIONS2} cannot be used with default export within <script>.`
    );
}
function getRootScopeIds(program) {
  let ids = [];
  walkAST(program, {
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

export {
  filterMacro,
  hasPropsOrEmits,
  transformDefineOptions
};
