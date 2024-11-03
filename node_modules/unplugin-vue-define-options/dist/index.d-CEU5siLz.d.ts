import { CodeTransform } from '@vue-macros/common';

declare function transformDefineOptions(code: string, id: string): CodeTransform | undefined;

export { transformDefineOptions as t };
