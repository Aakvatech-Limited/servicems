"use strict";Object.defineProperty(exports, "__esModule", {value: true}); function _optionalChain(ops) { let lastAccessLHS = undefined; let value = ops[0]; let i = 1; while (i < ops.length) { const op = ops[i]; const fn = ops[i + 1]; i += 2; if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) { return undefined; } if (op === 'access' || op === 'optionalAccess') { lastAccessLHS = value; value = fn(value); } else if (op === 'call' || op === 'optionalCall') { value = fn((...args) => value.call(lastAccessLHS, ...args)); lastAccessLHS = undefined; } } return value; }



var _chunkA7K2NBSOjs = require('./chunk-A7K2NBSO.js');

// src/export-expose.ts
var _common = require('@vue-macros/common');
var _languagecore = require('@vue/language-core');
var _mugglestring = require('muggle-string');
function transform(options) {
  const { codes, sfc, ts } = options;
  const exposed = /* @__PURE__ */ Object.create(null);
  for (const stmt of sfc.scriptSetup.ast.statements) {
    if (ts.isExportDeclaration(stmt) && stmt.exportClause) {
      const start = _chunkA7K2NBSOjs.getStart.call(void 0, stmt, options);
      const end = stmt.end;
      if (ts.isNamedExports(stmt.exportClause)) {
        const exportMap = /* @__PURE__ */ new Map();
        stmt.exportClause.elements.forEach((element) => {
          if (element.isTypeOnly) return;
          const name = element.name;
          const propertyName = element.propertyName || name;
          exportMap.set(
            [
              _chunkA7K2NBSOjs.getText.call(void 0, propertyName, options),
              "scriptSetup",
              _chunkA7K2NBSOjs.getStart.call(void 0, propertyName, options),
              _languagecore.allCodeFeatures
            ],
            [
              _chunkA7K2NBSOjs.getText.call(void 0, name, options),
              "scriptSetup",
              _chunkA7K2NBSOjs.getStart.call(void 0, name, options),
              _languagecore.allCodeFeatures
            ]
          );
          exposed[_chunkA7K2NBSOjs.getText.call(void 0, name, options)] = _chunkA7K2NBSOjs.getText.call(void 0, propertyName, options);
        });
        if (stmt.moduleSpecifier) {
          _mugglestring.replaceSourceRange.call(void 0, codes, "scriptSetup", start, start + 6, "import");
          _mugglestring.replaceSourceRange.call(void 0, 
            codes,
            "scriptSetup",
            end,
            end,
            `;[${Array.from(exportMap.values()).map(([name]) => name)}];`
          );
        } else {
          _mugglestring.replaceSourceRange.call(void 0, 
            codes,
            "scriptSetup",
            start,
            end,
            `;(({`,
            ...Array.from(exportMap.entries()).flatMap(
              ([name, value]) => name[0] === value[0] ? [value, ","] : [name, ":", value, ","]
            ),
            `})=>{${Array.from(exportMap.values()).map(([name]) => name)}`,
            `})({${Array.from(exportMap.keys()).map(([name]) => name)}})`
          );
        }
      } else if (ts.isNamespaceExport(stmt.exportClause)) {
        _mugglestring.replaceSourceRange.call(void 0, codes, "scriptSetup", start, start + 6, "import");
        _mugglestring.replaceSourceRange.call(void 0, 
          codes,
          "scriptSetup",
          end,
          end,
          `;[${_chunkA7K2NBSOjs.getText.call(void 0, stmt.exportClause.name, options)}];`
        );
      }
    } else if (ts.isVariableStatement(stmt) || ts.isFunctionDeclaration(stmt) || ts.isClassDeclaration(stmt)) {
      const exportModifier = _optionalChain([stmt, 'access', _ => _.modifiers, 'optionalAccess', _2 => _2.find, 'call', _3 => _3(
        (m) => m.kind === ts.SyntaxKind.ExportKeyword
      )]);
      if (!exportModifier) continue;
      const exposedValues = [];
      if (ts.isVariableStatement(stmt)) {
        for (const decl of stmt.declarationList.declarations) {
          if (!decl.name) continue;
          if (ts.isIdentifier(decl.name)) {
            const name = _chunkA7K2NBSOjs.getText.call(void 0, decl.name, options);
            exposed[name] = name;
          } else if (ts.isObjectBindingPattern(decl.name)) {
            decl.name.elements.forEach((element) => {
              if (!ts.isIdentifier(element.name)) return;
              exposedValues.push(_chunkA7K2NBSOjs.getText.call(void 0, element.name, options));
              exposed[_chunkA7K2NBSOjs.getText.call(void 0, element.name, options)] = element.propertyName && ts.isIdentifier(element.propertyName) ? _chunkA7K2NBSOjs.getText.call(void 0, element.propertyName, options) : _chunkA7K2NBSOjs.getText.call(void 0, element.name, options);
            });
          }
        }
      } else if (stmt.name && ts.isIdentifier(stmt.name)) {
        const name = _chunkA7K2NBSOjs.getText.call(void 0, stmt.name, options);
        exposed[name] = name;
      }
      _mugglestring.replaceSourceRange.call(void 0, 
        codes,
        "scriptSetup",
        _chunkA7K2NBSOjs.getStart.call(void 0, exportModifier, options),
        exportModifier.end,
        exposedValues.length > 0 ? `[${exposedValues}];` : ""
      );
    }
  }
  if (Object.keys(exposed).length === 0) return;
  const exposedStrings = Object.entries(exposed).flatMap(([key, value]) => [
    `${key}: `,
    value,
    ",\n"
  ]);
  if (_optionalChain([sfc, 'access', _4 => _4.scriptSetup, 'optionalAccess', _5 => _5.generic])) {
    _chunkA7K2NBSOjs.addCode.call(void 0, codes, `const __VLS_exportExposed = {
`, ...exposedStrings, `};
`);
    _mugglestring.replace.call(void 0, 
      codes,
      /(?<=expose\(exposed: import\(\S+\)\.ShallowUnwrapRef<)/,
      "typeof __VLS_exportExposed & "
    );
  } else {
    _mugglestring.replace.call(void 0, 
      codes,
      /(?<=export\sdefault \(await import\(\S+\)\)\.defineComponent\(\{[\s\S]*setup\(\) \{\nreturn \{\n)/,
      ...exposedStrings
    );
  }
}
var plugin = (ctx, options = {}) => {
  if (!options) return [];
  const filter = _common.createFilter.call(void 0, options);
  return {
    name: "vue-macros-export-expose",
    version: 2.1,
    resolveEmbeddedCode(fileName, sfc, embeddedFile) {
      if (!filter(fileName) || !_optionalChain([sfc, 'access', _6 => _6.scriptSetup, 'optionalAccess', _7 => _7.ast])) return;
      transform({
        codes: embeddedFile.content,
        sfc,
        ts: ctx.modules.typescript
      });
    }
  };
};
var export_expose_default = plugin;



exports.export_expose_default = export_expose_default;
