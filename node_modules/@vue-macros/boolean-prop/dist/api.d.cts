import { ConstantTypes, NodeTransform } from '@vue/compiler-core';

interface Options {
	/**
	* @default '!'
	*/
	negativePrefix?: string;
}
declare function transformBooleanProp({ negativePrefix, constType }?: Options & { constType?: ConstantTypes }): NodeTransform;

export { type Options, transformBooleanProp };
