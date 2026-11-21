/**
 * Every feature's English strings, merged: the source language. A new feature adds its own file next to these
 * (`orders.ts` with `orders.*` keys) and one line to `features` — it never puts its strings into another
 * feature's file, so two tasks building at the same time do not edit the same lines. When the app speaks other
 * languages, the same feature also gets `locales/<language>/orders.ts` (see `locales/index.ts`).
 */
import common from './common';
import home from './home';
import uiKit from './uiKit';

const features = [
  common,
  home,
  uiKit,
] as const;

type KeysOf<F> = F extends Record<infer K, string> ? K : never;
export type MessageKey = KeysOf<(typeof features)[number]>;

export const english = Object.assign({}, ...features) as Record<MessageKey, string>;
