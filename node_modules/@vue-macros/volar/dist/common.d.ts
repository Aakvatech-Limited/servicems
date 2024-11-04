import * as typescript from 'typescript';
import { FeatureName, OptionsResolved } from '@vue-macros/config';
import { SFCScriptBlock } from '@vue-macros/common';
import { Code, VueLanguagePlugin, Sfc } from '@vue/language-core';

declare const REGEX_DEFINE_COMPONENT: RegExp;
declare function addProps(codes: Code[], decl: Code[], vueLibName: string): boolean | undefined;
declare function addEmits(codes: Code[], decl: Code[], vueLibName: string): boolean | undefined;
declare function addCode(codes: Code[], ...args: Code[]): void;
type VueMacrosPlugin<K extends FeatureName> = (ctx: PluginContext, options?: OptionsResolved[K]) => ReturnType<VueLanguagePlugin>;
type PluginContext = Parameters<VueLanguagePlugin>[0];
declare function getVolarOptions<K extends keyof OptionsResolved>(context: PluginContext, key: K): OptionsResolved[K];
declare function getImportNames(ts: typeof typescript, sfc: Sfc): string[];
interface VolarContext {
	sfc: Sfc;
	ts: typeof typescript;
	source?: "script" | "scriptSetup";
}
declare function getStart(node: typescript.Node, { ts, sfc, source }: VolarContext): number;
declare function getText(node: typescript.Node, context: VolarContext): string;
declare function isJsxExpression(node?: typescript.Node): node is typescript.JsxExpression;
declare function patchSFC(block: SFCScriptBlock | null, offset: number): void;

export { type PluginContext, REGEX_DEFINE_COMPONENT, type VolarContext, type VueMacrosPlugin, addCode, addEmits, addProps, getImportNames, getStart, getText, getVolarOptions, isJsxExpression, patchSFC };
