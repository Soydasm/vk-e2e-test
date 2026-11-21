/**
 * The languages the app speaks: English (the strings in `messages/`) and one folder here per other language.
 * The provider, the language switcher, number and date formats and the API's Accept-Language all follow this
 * list; nothing else in the app names a language.
 *
 * Adding a language (Spanish, `es`): create `locales/es/` with
 *   - one file per file in `messages/`, the same name, its strings translated:
 *       import type home from '../../messages/home';
 *       import type { Translation } from '../../define';
 *       export default { 'home.title': 'Bienvenido', ... } satisfies Translation<typeof home>;
 *   - `index.ts` merging them, checked against every English key:
 *       import { translation } from '../../define';
 *       import common from './common'; import home from './home'; import uiKit from './uiKit';
 *       export default translation({ ...common, ...home, ...uiKit });
 * and register it below: `es: { name: 'Español', messages: es }`. `npx tsc --noEmit` lists every string the
 * new language still misses. Nothing else changes.
 */
import { english } from '../messages';

const REGISTRY = {
  en: { name: 'English', messages: english as Record<string, string> },
} satisfies Record<string, { name: string; messages: Record<string, string> }>;

export type Locale = keyof typeof REGISTRY;
export const LOCALES = Object.keys(REGISTRY) as Locale[];
/** Each language in its own words, for the language switcher. */
export const LOCALE_NAMES = Object.fromEntries(LOCALES.map((l) => [l, REGISTRY[l].name])) as Record<Locale, string>;
export const MESSAGES = Object.fromEntries(LOCALES.map((l) => [l, REGISTRY[l].messages])) as Record<Locale, Record<string, string>>;
