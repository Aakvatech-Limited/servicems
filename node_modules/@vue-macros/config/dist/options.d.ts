import { Options as Options$1 } from '@vue-macros/better-define';
import { Options as Options$2 } from '@vue-macros/boolean-prop';
import { Options as Options$3 } from '@vue-macros/chain-call';
import { BaseOptions, FilterOptions } from '@vue-macros/common';
import { Options as Options$4 } from '@vue-macros/define-emit';
import { Options as Options$5 } from '@vue-macros/define-models';
import { Options as Options$7 } from '@vue-macros/define-prop';
import { Options as Options$8 } from '@vue-macros/define-props';
import { Options as Options$9 } from '@vue-macros/define-props-refs';
import { Options as Options$a } from '@vue-macros/define-render';
import { Options as Options$b } from '@vue-macros/define-slots';
import { Options as Options$c } from '@vue-macros/define-stylex';
import { Options as Options$d } from '@vue-macros/export-expose';
import { Options as Options$e } from '@vue-macros/export-props';
import { Options as Options$f } from '@vue-macros/export-render';
import { Options as Options$g } from '@vue-macros/hoist-static';
import { Options as Options$h } from '@vue-macros/jsx-directive';
import { Options as Options$i } from '@vue-macros/named-template';
import { Options as Options$j } from '@vue-macros/reactivity-transform';
import { Options as Options$k } from '@vue-macros/script-lang';
import { Options as Options$l } from '@vue-macros/setup-block';
import { Options as Options$m } from '@vue-macros/setup-component';
import { Options as Options$n } from '@vue-macros/setup-sfc';
import { Options as Options$o } from '@vue-macros/short-bind';
import { Options as Options$p } from '@vue-macros/short-emits';
import { Options as Options$q } from '@vue-macros/short-vmodel';
import { Options as Options$6 } from 'unplugin-vue-define-options';

interface OptionsCommon extends Omit<BaseOptions, keyof FilterOptions> {
	root?: string;
	plugins?: {
		vue?: any;
		vueJsx?: any;
		vueRouter?: any;
	};
	/** @internal */
	nuxtContext?: { isClient?: boolean };
}
interface FeatureOptionsMap {
	/**
	* @see {@link https://vue-macros.dev/features/better-define.html}
	* @default true
	*/
	betterDefine: Options$1;
	/**
	* @see {@link https://vue-macros.dev/features/boolean-prop.html}
	* @default false
	*/
	booleanProp: Options$2;
	/**
	* @see {@link https://vue-macros.dev/macros/chain-call.html}
	* @default true
	*/
	chainCall: Options$3;
	/**
	* @see {@link https://vue-macros.dev/macros/define-emit.html}
	* @default true
	*/
	defineEmit: Options$4;
	/**
	* @see {@link https://vue-macros.dev/volar/define-generic.html}
	* @default true
	*/
	defineGeneric: FilterOptions;
	/**
	* @see {@link https://vue-macros.dev/macros/define-models.html}
	* @default true
	*/
	defineModels: Options$5;
	/**
	* @see {@link https://vue-macros.dev/macros/define-options.html}
	* @default vueVersion < 3.3
	*/
	defineOptions: Options$6;
	/**
	* @see {@link https://vue-macros.dev/macros/define-prop.html}
	* @default true
	*/
	defineProp: Options$7;
	/**
	* @see {@link https://vue-macros.dev/macros/define-props.html}
	* @default true
	*/
	defineProps: Options$8;
	/**
	* @see {@link https://vue-macros.dev/macros/define-props-refs.html}
	* @default true
	*/
	definePropsRefs: Options$9;
	/**
	* @see {@link https://vue-macros.dev/macros/define-render.html}
	* @default true
	*/
	defineRender: Options$a;
	/**
	* @see {@link https://vue-macros.dev/macros/define-slots.html}
	* @default vueVersion < 3.3
	*/
	defineSlots: Options$b;
	/**
	* @see {@link https://vue-macros.dev/macros/define-stylex.html}
	* @default false
	*/
	defineStyleX: Options$c;
	/**
	* @see {@link https://vue-macros.dev/features/export-expose.html}
	* @default false
	*/
	exportExpose: Options$d;
	/**
	* @see {@link https://vue-macros.dev/features/export-props.html}
	* @default false
	*/
	exportProps: Options$e;
	/**
	* @see {@link https://vue-macros.dev/features/export-render.html}
	* @default false
	*/
	exportRender: Options$f;
	/**
	* @see {@link https://vue-macros.dev/features/hoist-static.html}
	* @default true
	*/
	hoistStatic: Options$g;
	/**
	* @see {@link https://vue-macros.dev/features/jsx-directive.html}
	* @default true
	*/
	jsxDirective: Options$h;
	/**
	* @see {@link https://vue-macros.dev/features/jsx-ref.html}
	* @default false
	*/
	jsxRef: FilterOptions & { alias?: string[] };
	/**
	* @see {@link https://vue-macros.dev/features/named-template.html}
	* @default false
	* @deprecated Not actively maintained now. Try [createReusableTemplate](https://vueuse.org/core/createReusableTemplate/) instead.
	*/
	namedTemplate: Options$i;
	/**
	* @see {@link https://vue-macros.dev/features/reactivity-transform.html}
	* @default true
	*/
	reactivityTransform: Options$j;
	/**
	* @see {@link https://vue-macros.dev/features/script-lang.html}
	* @default false
	*/
	scriptLang: Options$k;
	/**
	* @see {@link https://vue-macros.dev/volar/script-sfc.html}
	* @default false
	*/
	scriptSFC: FilterOptions;
	/**
	* **experimental**: unpublished feature
	* @default false
	*/
	setupBlock: Options$l;
	/**
	* @see {@link https://vue-macros.dev/macros/setup-component.html}
	* @default true
	*/
	setupComponent: Options$m;
	/**
	* @see {@link https://vue-macros.dev/volar/setup-jsdoc.html}
	* @default true
	*/
	setupJsdoc: FilterOptions;
	/**
	* @see {@link https://vue-macros.dev/macros/setup-sfc.html}
	* @default false
	*/
	setupSFC: Options$n;
	/**
	* @see {@link https://vue-macros.dev/features/short-bind.html}
	* @default vueVersion < 3.4
	*/
	shortBind: Options$o;
	/**
	* @see {@link https://vue-macros.dev/macros/short-emits.html}
	* @default vueVersion < 3.3
	*/
	shortEmits: Options$p;
	/**
	* @see {@link https://vue-macros.dev/macros/short-vmodel.html}
	* @default true
	*/
	shortVmodel: Options$q;
}
type FeatureName = keyof FeatureOptionsMap;
type FeatureOptions = FeatureOptionsMap[FeatureName];
type OptionalSubOptions<T> = boolean | Omit<T, keyof OptionsCommon> | undefined;
type Options = OptionsCommon & { [K in keyof FeatureOptionsMap]? : OptionalSubOptions<FeatureOptionsMap[K]> };
type OptionsResolved = Required<OptionsCommon> & { [K in keyof FeatureOptionsMap] : false | FeatureOptionsMap[K] };
declare function resolveOptions(options?: Options, cwd?: string): OptionsResolved;

export { type FeatureName, type FeatureOptions, type FeatureOptionsMap, type Options, type OptionsCommon, type OptionsResolved, resolveOptions };
