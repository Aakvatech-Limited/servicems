import { NodeTransform } from '@vue/compiler-core';

interface Options {
	version?: number;
}
declare function transformShortBind(options?: Options): NodeTransform;

export { type Options, transformShortBind };
