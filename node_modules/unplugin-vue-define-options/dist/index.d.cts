import { BaseOptions, MarkRequired } from '@vue-macros/common';
import { UnpluginInstance } from 'unplugin';
export { t as transform } from './index.d-CEU5siLz.js';

type Options = BaseOptions;
type OptionsResolved = MarkRequired<Options, "include" | "version">;
declare const plugin: UnpluginInstance<Options | undefined, false>;

export { type Options, type OptionsResolved, plugin as default };
