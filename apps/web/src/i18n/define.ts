import type { MessageKey } from './messages';

/**
 * `defineMessages` holds one feature's English strings: the source every other language is checked against.
 * `Translation<typeof feature>` is that feature's strings in another language: TypeScript rejects the file when
 * it misses a key the English one has, or has a key the English one does not. A language whose plurals have
 * more forms than English (`x.few`, `x.many`…) may add them.
 */
export function defineMessages<K extends string>(messages: Record<K, string>) {
  return messages;
}

type ExtraPluralForms = { [key: `${string}.${'zero' | 'two' | 'few' | 'many'}`]: string };

export type Translation<F extends Record<string, string>> = Record<keyof F, string> & Partial<ExtraPluralForms>;

/** A whole language (`locales/<language>/index.ts`): every English key, translated — TypeScript lists the missing. */
export function translation(messages: Record<MessageKey, string> & Partial<ExtraPluralForms>) {
  return messages as Record<string, string>;
}
