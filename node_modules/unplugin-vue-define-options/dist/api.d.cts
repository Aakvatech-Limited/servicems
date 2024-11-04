export { t as transformDefineOptions } from './index.d-CEU5siLz.js';
import { Statement, CallExpression, ObjectExpression } from '@babel/types';
import '@vue-macros/common';

declare function filterMacro(stmts: Statement[]): CallExpression[];
declare function hasPropsOrEmits(node: ObjectExpression): boolean;

export { filterMacro, hasPropsOrEmits };
