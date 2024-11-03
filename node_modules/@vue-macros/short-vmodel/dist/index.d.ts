import { Options } from './api.js';
export { Prefix, processAttribute, processDirective, transformShortVmodel } from './api.js';
import { Plugin } from 'vite';
import '@vue/compiler-core';

declare function rollup(options?: Options): Plugin;
declare const plugin: {
	rollup: typeof rollup;
	rolldown: typeof rollup;
	vite: typeof rollup;
};

export { Options, plugin as default };
