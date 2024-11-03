import { NodeTransform, TransformContext, PlainElementNode, ComponentNode, SlotOutletNode, TemplateNode } from '@vue/compiler-core';

type Prefix = "::" | "$" | "*";
interface Options {
	/**
	* @default '$'
	*/
	prefix?: Prefix;
}
type NodeElement = PlainElementNode | ComponentNode | SlotOutletNode | TemplateNode;
declare function transformShortVmodel({ prefix }?: Options): NodeTransform;
declare function processDirective(node: NodeElement): void;
declare function processAttribute(prefix: string, node: NodeElement, context: TransformContext): void;

export { type Options, type Prefix, processAttribute, processDirective, transformShortVmodel };
