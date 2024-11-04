import {
  addCode,
  getStart,
  getText,
  isJsxExpression
} from "./chunk-LMDKOHQF.mjs";

// src/jsx-directive.ts
import { createFilter } from "@vue-macros/common";

// src/jsx-directive/context.ts
import { replaceSourceRange } from "muggle-string";
function transformCtx(node, root, index, options) {
  const { ts, codes } = options;
  const openingElement = getOpeningElement(node, options);
  if (!openingElement) return "";
  if (!codes.toString().includes("function __VLS_getFunctionalComponentCtx")) {
    codes.push(`
function __VLS_getFunctionalComponentCtx<T, K, const S>(
  comp: T,
  compInstance: K,
  s: S,
): S extends keyof typeof __VLS_nativeElements
  ? { expose: (exposed: (typeof __VLS_nativeElements)[S]) => any }
  : '__ctx' extends keyof __VLS_PickNotAny<K, {}>
    ? K extends { __ctx?: infer Ctx }
      ? Ctx
      : never
    : T extends (props: infer P, ctx: infer Ctx) => any
      ? { props: P; slots: P['vSlots']; expose: P['vExpose'] } & Ctx
      : {};
`);
  }
  let props = "";
  let refValue;
  for (const prop of openingElement.attributes.properties) {
    if (!ts.isJsxAttribute(prop)) continue;
    let name = getText(prop.name, options);
    if (name === "ref" && prop.initializer && isJsxExpression(prop.initializer) && prop.initializer.expression) {
      refValue = getRefValue(prop.initializer.expression, options);
      continue;
    }
    if (name.startsWith("v-model")) {
      name = name.split("_")[0].split(":")[1] || "modelValue";
    } else if (name.startsWith("v-")) {
      continue;
    }
    const value = prop.initializer ? isJsxExpression(prop.initializer) && prop.initializer.expression ? getText(prop.initializer.expression, options) : getText(prop.initializer, options) : "true";
    props += `'${name}': ${value},`;
  }
  const ctxName = `__VLS_ctx_${refValue || index}`;
  const tagName = getTagName(node, { ...options, withTypes: true });
  const result = `
const ${ctxName} = __VLS_getFunctionalComponentCtx(${tagName}, __VLS_asFunctionalComponent(${tagName})({${props}}), '${tagName}');
`;
  if (root) {
    replaceSourceRange(
      codes,
      options.source,
      root.end - 1,
      root.end - 1,
      result
    );
  } else {
    addCode(codes, result);
  }
  return ctxName;
}
function getRefValue(expression, options) {
  const { ts } = options;
  if (ts.isIdentifier(expression)) {
    return getText(expression, options);
  } else if (ts.isFunctionLike(expression)) {
    let left;
    if (ts.isBinaryExpression(expression.body)) {
      left = expression.body.left;
    }
    ts.forEachChild(expression.body, (node) => {
      if (ts.isBinaryExpression(node)) {
        left = node.left;
      } else if (ts.isExpressionStatement(node) && ts.isBinaryExpression(node.expression)) {
        left = node.expression.left;
      }
    });
    return left && getText(
      ts.isPropertyAccessExpression(left) ? left.expression : left,
      options
    );
  } else if (ts.isCallExpression(expression) && expression.arguments[0] && ts.isIdentifier(expression.arguments[0])) {
    return getText(expression.arguments[0], options);
  }
}

// src/jsx-directive/ref.ts
import { allCodeFeatures } from "@vue/language-core";
import { replaceSourceRange as replaceSourceRange2 } from "muggle-string";
function transformRef(nodes, ctxMap, options) {
  const { codes, source, ts } = options;
  for (const { node, attribute } of nodes) {
    if (attribute.initializer && isJsxExpression(attribute.initializer) && attribute.initializer.expression && (ts.isFunctionExpression(attribute.initializer.expression) || ts.isArrowFunction(attribute.initializer.expression))) {
      replaceSourceRange2(
        codes,
        source,
        getStart(attribute, options),
        attribute.end,
        "{...({ ",
        ["ref", source, getStart(attribute.name, options), allCodeFeatures],
        ": ",
        [
          getText(attribute.initializer.expression, options),
          source,
          getStart(attribute.initializer.expression, options),
          allCodeFeatures
        ],
        `} satisfies { ref: (e: Parameters<typeof ${ctxMap.get(node)}.expose>[0]) => any }) as {}}`
      );
    }
  }
}

// src/jsx-directive/v-bind.ts
import { replaceSourceRange as replaceSourceRange3 } from "muggle-string";
function transformVBind(nodes, options) {
  if (nodes.length === 0) return;
  const { codes, source } = options;
  for (const { attribute } of nodes) {
    const attributeName = getText(attribute.name, options);
    const start = getStart(attribute.name, options);
    const end = attribute.name.end;
    if (attributeName.includes("_")) {
      replaceSourceRange3(codes, source, start + attributeName.indexOf("_"), end);
    }
  }
}

// src/jsx-directive/v-for.ts
import { allCodeFeatures as allCodeFeatures2 } from "@vue/language-core";
import { replaceSourceRange as replaceSourceRange4 } from "muggle-string";
function resolveVFor(attribute, options) {
  const { ts, sfc, source } = options;
  const result = [];
  if (isJsxExpression(attribute.initializer) && attribute.initializer.expression && ts.isBinaryExpression(attribute.initializer.expression)) {
    let index;
    let objectIndex;
    let item = attribute.initializer.expression.left;
    const list = attribute.initializer.expression.right;
    if (ts.isParenthesizedExpression(item)) {
      if (ts.isBinaryExpression(item.expression)) {
        if (ts.isBinaryExpression(item.expression.left)) {
          index = item.expression.left.right;
          objectIndex = item.expression.right;
          item = item.expression.left.left;
        } else {
          index = item.expression.right;
          item = item.expression.left;
        }
      } else {
        item = item.expression;
      }
    }
    if (item && list) {
      result.push(
        "__VLS_getVForSourceType(",
        [
          sfc[source].content.slice(getStart(list, options), list.end),
          source,
          getStart(list, options),
          allCodeFeatures2
        ],
        ").map(([",
        [
          String(sfc[source]?.content.slice(getStart(item, options), item.end)),
          source,
          getStart(item, options),
          allCodeFeatures2
        ],
        ", ",
        index ? [
          String(
            sfc[source]?.content.slice(getStart(index, options), index.end)
          ),
          source,
          getStart(index, options),
          allCodeFeatures2
        ] : objectIndex ? "undefined" : "",
        ...objectIndex ? [
          ", ",
          [
            String(
              sfc[source]?.content.slice(
                getStart(objectIndex, options),
                objectIndex.end
              )
            ),
            source,
            getStart(objectIndex, options),
            allCodeFeatures2
          ]
        ] : "",
        "]) => "
      );
    }
  }
  return result;
}
function transformVFor(nodes, options) {
  const { codes, source } = options;
  nodes.forEach(({ attribute, node, parent }) => {
    const result = resolveVFor(attribute, options);
    if (parent) {
      result.unshift("{");
    }
    replaceSourceRange4(codes, source, node.pos, node.pos, ...result);
    replaceSourceRange4(
      codes,
      source,
      node.end - 1,
      node.end,
      `>)${parent ? "}" : ""}`
    );
    replaceSourceRange4(
      codes,
      source,
      getStart(attribute, options),
      attribute.end
    );
  });
}

// src/jsx-directive/v-if.ts
import { allCodeFeatures as allCodeFeatures3 } from "@vue/language-core";
import { replaceSourceRange as replaceSourceRange5 } from "muggle-string";
function transformVIf(nodes, options) {
  const { codes, ts, source } = options;
  nodes.forEach(({ node, attribute, parent }, index) => {
    if (!ts.isIdentifier(attribute.name)) return;
    if (["v-if", "v-else-if"].includes(getText(attribute.name, options)) && isJsxExpression(attribute.initializer) && attribute.initializer.expression) {
      const hasScope = parent && attribute.name.escapedText === "v-if";
      replaceSourceRange5(
        codes,
        source,
        node.pos,
        node.pos,
        `${hasScope ? "{" : " "}(`,
        [
          getText(attribute.initializer.expression, options),
          source,
          getStart(attribute.initializer.expression, options),
          allCodeFeatures3
        ],
        ") ? "
      );
      const nextAttribute = nodes[index + 1]?.attribute;
      const nextNodeHasElse = nextAttribute && ts.isIdentifier(nextAttribute.name) ? String(nextAttribute.name.escapedText).startsWith("v-else") : false;
      replaceSourceRange5(
        codes,
        source,
        node.end,
        node.end,
        nextNodeHasElse ? " : " : ` : null${parent ? "}" : ""}`
      );
    } else if (attribute.name.escapedText === "v-else") {
      replaceSourceRange5(codes, source, node.end, node.end, parent ? "}" : "");
    }
    replaceSourceRange5(
      codes,
      source,
      getStart(attribute, options),
      attribute.end
    );
  });
}

// src/jsx-directive/v-model.ts
import { allCodeFeatures as allCodeFeatures4 } from "@vue/language-core";
import { replaceSourceRange as replaceSourceRange6 } from "muggle-string";
function transformVModel(nodes, ctxMap, options) {
  const { codes, ts, source, sfc } = options;
  let firstNamespacedNode;
  const result = [];
  const emits = [];
  for (const { attribute: attribute2, node: node2 } of nodes) {
    const modelValue = ["input", "select", "textarea"].includes(
      getTagName(node2, options)
    ) ? "value" : "modelValue";
    const isArrayExpression = isJsxExpression(attribute2.initializer) && attribute2.initializer.expression && ts.isArrayLiteralExpression(attribute2.initializer.expression);
    const name = getText(attribute2.name, options);
    const start = getStart(attribute2.name, options);
    if (name.startsWith("v-model:") || isArrayExpression) {
      let isDynamic = false;
      const attributeName2 = name.slice(8).split(/\s/)[0].split("_")[0].replace(/^\$(.*)\$/, (_, $1) => {
        isDynamic = true;
        return $1;
      });
      firstNamespacedNode ??= {
        attribute: attribute2,
        attributeName: attributeName2,
        node: node2
      };
      if (firstNamespacedNode.attribute !== attribute2) {
        replaceSourceRange6(
          codes,
          source,
          getStart(attribute2, options),
          attribute2.end
        );
        result.push(",");
      }
      if (isArrayExpression) {
        const { elements } = attribute2.initializer.expression;
        if (elements[1] && !ts.isArrayLiteralExpression(elements[1])) {
          isDynamic = !ts.isStringLiteral(elements[1]);
          result.push(
            isDynamic ? "[`${" : "",
            [
              getText(elements[1], options),
              source,
              getStart(elements[1], options),
              allCodeFeatures4
            ],
            isDynamic ? "}`]" : ""
          );
        } else {
          result.push(modelValue);
        }
        if (elements[0])
          result.push(":", [
            getText(elements[0], options),
            source,
            getStart(elements[0], options),
            allCodeFeatures4
          ]);
      } else {
        result.push(
          isDynamic ? "[`${" : "",
          ...attributeName2.split("-").map((code, index, codes2) => [
            index ? code.at(0)?.toUpperCase() + code.slice(1) : code,
            source,
            start + (isDynamic ? 9 : 8) + (index && codes2[index - 1].length + 1),
            allCodeFeatures4
          ]),
          isDynamic ? "}`]" : ""
        );
        if (attribute2.initializer && isJsxExpression(attribute2.initializer) && attribute2.initializer.expression && attributeName2)
          result.push(":", [
            getText(attribute2.initializer.expression, options),
            source,
            getStart(attribute2.initializer.expression, options),
            allCodeFeatures4
          ]);
      }
      emits.push(`'onUpdate:${attributeName2}': () => {}, `);
    } else {
      replaceSourceRange6(
        codes,
        source,
        start,
        attribute2.name.end,
        `{...{'onUpdate:${modelValue}': () => {} }} `,
        modelValue.slice(0, 3),
        [modelValue.slice(3), source, start, allCodeFeatures4]
      );
    }
  }
  if (!firstNamespacedNode) return;
  const { attribute, attributeName, node } = firstNamespacedNode;
  getModelsType(codes);
  const end = attributeName ? attribute.end : getStart(attribute, options) + 8;
  replaceSourceRange6(
    codes,
    source,
    getStart(attribute, options),
    end,
    `{...{`,
    ...result,
    `} satisfies __VLS_GetModels<__VLS_NormalizeProps<typeof ${ctxMap.get(node)}.props>>}`,
    ` {...{`,
    ...emits,
    `}}`
  );
  replaceSourceRange6(
    codes,
    source,
    end,
    end + 1,
    sfc[source].content.slice(end, end + 1)
  );
}
function getModelsType(codes) {
  if (codes.toString().includes("type __VLS_GetModels")) return;
  codes.push(`
type __VLS_NormalizeProps<T> = T extends object
  ? {
      [K in keyof T as {} extends Record<K, 1>
        ? never
        : K extends keyof import('vue').VNodeProps | 'class' | 'style'
          ? never
          : K]: T[K]
    }
  : never;
type __VLS_CamelCase<S extends string> = S extends \`\${infer F}-\${infer RF}\${infer R}\`
  ? \`\${F}\${Uppercase<RF>}\${__VLS_CamelCase<R>}\`
  : S;
type __VLS_PropsToEmits<T> = T extends object
    ? {
        [K in keyof T as K extends \`onUpdate:\${infer R}\`
          ? R extends 'modelValue'
            ? never
            : __VLS_CamelCase<R>
          : never]: T[K]
      }
    : never
type __VLS_GetModels<P, E = __VLS_PropsToEmits<P>> = P extends object
  ? {
      [K in keyof P as K extends keyof E
        ? K
        : never]: K extends keyof P ? P[K] : never
    }
  : {};
`);
}

// src/jsx-directive/v-on.ts
import { allCodeFeatures as allCodeFeatures5 } from "@vue/language-core";
import { replaceSourceRange as replaceSourceRange7 } from "muggle-string";
function transformVOn(nodes, ctxMap, { codes, source }) {
  if (nodes.length === 0) return;
  for (const { node, attribute } of nodes) {
    replaceSourceRange7(
      codes,
      source,
      attribute.end - 1,
      attribute.end - 1,
      ` satisfies __VLS_NormalizeEmits<typeof ${ctxMap.get(node)}.emit>`
    );
  }
}
function transformVOnWithModifiers(nodes, options) {
  const { codes, source } = options;
  for (const { attribute } of nodes) {
    const attributeName = getText(attribute.name, options).split("_")[0];
    const start = getStart(attribute.name, options);
    const end = attribute.name.end;
    replaceSourceRange7(codes, source, start, end, "{...{", [
      attributeName,
      source,
      start,
      allCodeFeatures5
    ]);
    if (!attribute.initializer) {
      replaceSourceRange7(codes, source, end, end, ": () => {}}}");
    } else if (isJsxExpression(attribute.initializer) && attribute.initializer.expression) {
      replaceSourceRange7(
        codes,
        source,
        end,
        getStart(attribute.initializer.expression, options),
        ": "
      );
      replaceSourceRange7(codes, source, attribute.end, attribute.end, "}");
    }
  }
}

// src/jsx-directive/v-slot.ts
import { allCodeFeatures as allCodeFeatures6 } from "@vue/language-core";
import { replaceSourceRange as replaceSourceRange8 } from "muggle-string";
function transformVSlot(nodeMap, ctxMap, options) {
  if (nodeMap.size === 0) return;
  const { codes, ts, sfc, source } = options;
  nodeMap.forEach(({ attributeMap, vSlotAttribute }, node) => {
    const result = [" vSlots={{"];
    const attributes = Array.from(attributeMap);
    attributes.forEach(
      ([attribute, { children, vIfAttribute, vForAttribute }], index) => {
        if (!attribute) return;
        let vIfAttributeName;
        if (vIfAttribute && (vIfAttributeName = getText(vIfAttribute.name, options))) {
          if ("v-if" === vIfAttributeName) {
            result.push("...");
          }
          if (["v-if", "v-else-if"].includes(vIfAttributeName) && isJsxExpression(vIfAttribute.initializer) && vIfAttribute.initializer.expression) {
            result.push(
              "(",
              [
                getText(vIfAttribute.initializer.expression, options),
                source,
                getStart(vIfAttribute.initializer.expression, options),
                allCodeFeatures6
              ],
              ") ? {"
            );
          } else if ("v-else" === vIfAttributeName) {
            result.push("{");
          }
        }
        if (vForAttribute) {
          result.push("...", ...resolveVFor(vForAttribute, options), "({");
        }
        let isDynamic = false;
        let attributeName = getText(attribute.name, options).slice(6).split(/\s/)[0].replace(/\$(.*)\$/, (_, $1) => {
          isDynamic = true;
          return $1;
        });
        const isNamespace = attributeName.startsWith(":");
        attributeName = attributeName.slice(1);
        const wrapByQuotes = !attributeName || attributeName.includes("-");
        result.push(
          isNamespace ? [
            isDynamic ? `[${attributeName}]` : wrapByQuotes ? `'${attributeName}'` : attributeName,
            source,
            getStart(attribute.name, options) + (wrapByQuotes ? 6 : 7),
            allCodeFeatures6
          ] : "default",
          `: (`,
          (!isNamespace || attributeName) && isJsxExpression(attribute.initializer) && attribute.initializer.expression ? [
            getText(attribute.initializer.expression, options),
            source,
            getStart(attribute.initializer.expression, options),
            allCodeFeatures6
          ] : "",
          isDynamic ? ": any" : "",
          ") => <>",
          ...children.map((child) => {
            replaceSourceRange8(codes, source, child.pos, child.end);
            const isSlotTemplate = getTagName(child, options) === "template" && !vSlotAttribute;
            const node2 = isSlotTemplate && ts.isJsxElement(child) ? child.children : child;
            return isSlotTemplate && ts.isJsxSelfClosingElement(child) ? "" : [
              sfc[source].content.slice(node2.pos, node2.end),
              source,
              node2.pos,
              allCodeFeatures6
            ];
          }),
          "</>,"
        );
        if (vForAttribute) {
          result.push("})),");
        }
        if (vIfAttribute && vIfAttributeName) {
          if (["v-if", "v-else-if"].includes(vIfAttributeName)) {
            const nextIndex = index + (attributes[index + 1]?.[0] ? 1 : 2);
            const nextAttribute = attributes[nextIndex]?.[1].vIfAttribute;
            result.push(
              "}",
              nextAttribute && getText(nextAttribute.name, options).startsWith("v-else") ? " : " : " : null,"
            );
          } else if ("v-else" === vIfAttributeName) {
            result.push("},");
          }
        }
      }
    );
    const slotType = `} satisfies typeof ${ctxMap.get(node)}.slots}`;
    if (attributeMap.has(null)) {
      result.push("default: () => <>");
    } else {
      result.push(slotType);
    }
    if (vSlotAttribute) {
      replaceSourceRange8(
        codes,
        source,
        getStart(vSlotAttribute, options),
        vSlotAttribute.end,
        ...result
      );
      replaceSourceRange8(
        codes,
        source,
        vSlotAttribute.end,
        vSlotAttribute.end + 1,
        sfc[source].content.slice(vSlotAttribute.end, vSlotAttribute.end + 1)
      );
    } else if (ts.isJsxElement(node)) {
      replaceSourceRange8(
        codes,
        source,
        node.openingElement.end - 1,
        node.openingElement.end,
        ...result
      );
      replaceSourceRange8(
        codes,
        source,
        node.closingElement.pos,
        node.closingElement.pos,
        attributeMap.has(null) ? `</>${slotType}>` : ">"
      );
    }
  });
}
function transformVSlots(nodes, ctxMap, options) {
  const { codes, source } = options;
  for (const {
    node,
    attribute: { initializer }
  } of nodes) {
    if (initializer && isJsxExpression(initializer) && initializer.expression) {
      replaceSourceRange8(
        codes,
        source,
        initializer.expression.end,
        initializer.expression.end,
        ` satisfies typeof ${ctxMap.get(node)}.slots`
      );
    }
  }
}

// src/jsx-directive/index.ts
function transformJsxDirective(options) {
  const { sfc, ts, source } = options;
  const vIfMap = /* @__PURE__ */ new Map();
  const vForNodes = [];
  const vSlotMap = /* @__PURE__ */ new Map();
  const vModelMap = /* @__PURE__ */ new Map();
  const vOnNodes = [];
  const vOnWithModifiers = [];
  const vBindNodes = [];
  const refNodes = [];
  const vSlots = [];
  const ctxNodeMap = /* @__PURE__ */ new Map();
  function walkJsxDirective(node, parent, parents = []) {
    const tagName = getTagName(node, options);
    const properties = getOpeningElement(node, options);
    let ctxNode;
    let vIfAttribute;
    let vForAttribute;
    let vSlotAttribute;
    for (const attribute of properties?.attributes.properties || []) {
      if (!ts.isJsxAttribute(attribute)) continue;
      const attributeName = getText(attribute.name, options);
      if (["v-if", "v-else-if", "v-else"].includes(attributeName)) {
        vIfAttribute = attribute;
      } else if (attributeName === "v-for") {
        vForAttribute = attribute;
      } else if (/^v-slot(?=:|$)/.test(attributeName)) {
        vSlotAttribute = attribute;
      } else if (/^v-model(?=[:_]|$)/.test(attributeName)) {
        vModelMap.has(node) || vModelMap.set(node, []);
        vModelMap.get(node).push({
          node,
          attribute
        });
        ctxNode = node;
      } else if (attributeName === "v-on") {
        vOnNodes.push({ node, attribute });
        ctxNode = node;
      } else if (/^on[A-Z]\S*_\S+/.test(attributeName)) {
        vOnWithModifiers.push({ node, attribute });
      } else if (/^(?!v-|on[A-Z])\S+_\S+/.test(attributeName)) {
        vBindNodes.push({ node, attribute });
      } else if (attributeName === "ref") {
        refNodes.push({ node, attribute });
        ctxNode = node;
      } else if (attributeName === "v-slots") {
        ctxNode = node;
        vSlots.push({ node, attribute });
      }
    }
    if (isJsxExpression(node) && node.expression && ts.isObjectLiteralExpression(node.expression) && parent && ts.isJsxElement(parent) && parent.children.filter(
      (child) => ts.isJsxText(child) ? getText(child, options).trim() : true
    ).length === 1) {
      ctxNode = node;
      vSlots.push({
        node: parent,
        attribute: {
          initializer: {
            kind: ts.SyntaxKind.JsxExpression,
            expression: node.expression
          }
        }
      });
    }
    if (!(vSlotAttribute && tagName === "template")) {
      if (vIfAttribute) {
        vIfMap.has(parent) || vIfMap.set(parent, []);
        vIfMap.get(parent).push({
          node,
          attribute: vIfAttribute,
          parent
        });
      }
      if (vForAttribute) {
        vForNodes.push({
          node,
          attribute: vForAttribute,
          parent: vIfAttribute ? void 0 : parent
        });
      }
    }
    if (vSlotAttribute) {
      const slotNode = tagName === "template" ? parent : node;
      if (!slotNode) return;
      ctxNode = slotNode;
      const attributeMap = vSlotMap.get(slotNode)?.attributeMap || vSlotMap.set(slotNode, {
        vSlotAttribute: tagName === "template" ? void 0 : vSlotAttribute,
        attributeMap: /* @__PURE__ */ new Map()
      }).get(slotNode).attributeMap;
      const children = attributeMap.get(vSlotAttribute)?.children || attributeMap.set(vSlotAttribute, {
        children: [],
        ...tagName === "template" ? {
          vIfAttribute,
          vForAttribute
        } : {}
      }).get(vSlotAttribute).children;
      if (slotNode === parent && ts.isJsxElement(parent)) {
        children.push(node);
        if (attributeMap.get(null)) return;
        for (const child of parent.children) {
          if (getTagName(child, options) === "template" || ts.isJsxText(child) && !getText(child, options).trim())
            continue;
          const defaultNodes = attributeMap.get(null)?.children || attributeMap.set(null, { children: [] }).get(null).children;
          defaultNodes.push(child);
        }
      } else if (ts.isJsxElement(node)) {
        children.push(...node.children);
      }
    }
    if (ctxNode) {
      ctxNodeMap.set(ctxNode, parents.find(ts.isBlock));
    }
    ts.forEachChild(node, (child) => {
      parents.unshift(node);
      walkJsxDirective(
        child,
        ts.isJsxElement(node) || ts.isJsxFragment(node) ? node : void 0,
        parents
      );
      parents.shift();
    });
  }
  ts.forEachChild(sfc[source].ast, walkJsxDirective);
  const ctxMap = new Map(
    Array.from(ctxNodeMap).map(([node, root], index) => [
      node,
      transformCtx(node, root, index, options)
    ])
  );
  transformVSlot(vSlotMap, ctxMap, options);
  transformVFor(vForNodes, options);
  vIfMap.forEach((nodes) => transformVIf(nodes, options));
  vModelMap.forEach((nodes) => transformVModel(nodes, ctxMap, options));
  transformVOn(vOnNodes, ctxMap, options);
  transformVOnWithModifiers(vOnWithModifiers, options);
  transformVBind(vBindNodes, options);
  transformRef(refNodes, ctxMap, options);
  transformVSlots(vSlots, ctxMap, options);
}
function getOpeningElement(node, options) {
  const { ts } = options;
  return ts.isJsxSelfClosingElement(node) ? node : ts.isJsxElement(node) ? node.openingElement : void 0;
}
function getTagName(node, options) {
  const openingElement = getOpeningElement(node, options);
  if (!openingElement) return "";
  let types = "";
  if (options.withTypes && openingElement.typeArguments?.length) {
    types = `<${openingElement.typeArguments.map((argument) => getText(argument, options)).join(", ")}>`;
  }
  return getText(openingElement.tagName, options) + types;
}

// src/jsx-directive.ts
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  const filter = createFilter(options);
  return {
    name: "vue-macros-jsx-directive",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName) || !["jsx", "tsx"].includes(embeddedFile.lang))
        return;
      for (const source of ["script", "scriptSetup"]) {
        if (!sfc[source]?.ast) continue;
        transformJsxDirective({
          codes: embeddedFile.content,
          sfc,
          ts: ctx.modules.typescript,
          source,
          vueVersion: ctx.vueCompilerOptions.target
        });
      }
    }
  };
};
var jsx_directive_default = plugin;

export {
  jsx_directive_default
};
