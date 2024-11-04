import { VueMacrosPlugin } from './common.js';
import 'typescript';
import '@vue-macros/config';
import '@vue-macros/common';
import '@vue/language-core';

declare const plugin: VueMacrosPlugin<"defineEmit">;

export { plugin as default };
