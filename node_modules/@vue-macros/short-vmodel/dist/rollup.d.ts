import plugin from './index.js';
import './api.js';
import '@vue/compiler-core';
import 'vite';

declare const _default: typeof plugin.rollup;

export { _default as default };
